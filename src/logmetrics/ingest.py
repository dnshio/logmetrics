import os
from datetime import datetime, timedelta, timezone, tzinfo
from dataclasses import dataclass

import bytewax.operators as op
import bytewax.operators.windowing as win
from bytewax.operators.windowing import EventClock, TumblingWindower
from bytewax.connectors.stdio import StdOutSink
from bytewax.connectors.files import FileSource
from bytewax.dataflow import Dataflow


# slots are enabled by default on Python 3.10+
# but we are being explicit here for good measure
@dataclass(slots=True)
class LogEvent:
    customer_id: str
    resource: str
    status_code: int
    # TODO: consider using Decimal
    duration: float
    timestamp: datetime


def event_from_raw(log_line: str) -> LogEvent:
    """
    Returns LogEvent object for a given log_line string input.

    Example log line:
        2024-10-10 12:50:18 cust_14 /api/v1/resource3 401 0.847

    Notes on parsing:
    We are going to just split the logline by whitespace and
    treat each token as an attribute for this exercise.
    Except for timestamp, which is parsed by reading the first
    19 chars of the log line rather than re-joining split tokens.

    This approach doesn't work if the attributes could contain spaces.
    "I'll fix it next sprint xD"

    TODO:
        Decide if we should raise a ParseError or return None.
        Depends on how we filter erroreous events from the stream
    """

    # The first 19 chars of the logline is a isoformatted timestamp.
    # I'm adding Z to force UTC. Hopefully working with dates would
    # become easier by Python 3.28
    dt = datetime.fromisoformat(f"{log_line[0:19]}Z")

    tokens = log_line.split(" ")

    # TODO: add _plenty_ of error handling here.
    # e.g. IndexError and ValueError
    return LogEvent(
        customer_id=tokens[2],
        resource=tokens[3],
        status_code=int(tokens[4]),
        duration=float(tokens[5]),
        timestamp=dt,
    )


flow = Dataflow("api_requests")

raw = op.input(
    "input", flow, FileSource(path=os.environ.get("INPUT_FILE_PATH"))
)

parsed = op.map("deserialise", raw, event_from_raw)


partitioned = op.key_on(
    "partitioned_input", parsed, lambda event: event.customer_id
)

# Configure the `fold_window` operator to use the event time.
clock = EventClock(
    lambda event: event.timestamp,
    wait_for_system_duration=timedelta(seconds=10),
)


align_to = datetime.now(timezone.utc) - timedelta(days=60)

windower = TumblingWindower(align_to=align_to, length=timedelta(days=1))


def acc_builder():
    return {
        "count": 0,
        "errors": 0,
        "avg_duration": 0,
        "median_duration": 0,
        "p99_duration": 0,
        "durations": [],
    }


def calculate_stats(snapshot: dict, event: LogEvent):
    """
    Maintains running statistics for event durations in a streaming context.

    Args:
        snapshot (dict): Current accumulated statistics
        event (LogEvent): New event to incorporate into statistics

    Returns:
        dict: Updated statistics including:
            - count: Total number of events
            - avg_duration: Mean duration
            - median_duration: Median (p50) duration
            - p99_duration: 99th percentile duration
            - durations: Sorted list of all durations (for percentile calculations)
    """

    print("\n\n => Snapshot: ", snapshot)

    # Update count
    snapshot["count"] += 1

    # Update the error count
    if event.status_code >= 400:
        snapshot["errors"] += 1

    # Insert new duration while maintaining sorted order
    durations = snapshot["durations"]
    insert_idx = 0
    for i, d in enumerate(durations):
        if event.duration <= d:
            insert_idx = i
            break
        if i == len(durations) - 1:
            insert_idx = len(durations)
    durations.insert(insert_idx, event.duration)

    # Update average
    snapshot["avg_duration"] = (
        snapshot["avg_duration"] * (snapshot["count"] - 1) + event.duration
    ) / snapshot["count"]

    # Update median (p50)
    median_idx = (snapshot["count"] - 1) // 2
    if snapshot["count"] % 2 == 0:
        snapshot["median_duration"] = (
            durations[median_idx] + durations[median_idx + 1]
        ) / 2
    else:
        snapshot["median_duration"] = durations[median_idx]

    # Update p99
    p99_idx = min(int(snapshot["count"] * 0.99), snapshot["count"] - 1)
    snapshot["p99_duration"] = durations[p99_idx]

    return snapshot


def window_merger(snapshots, new_snapshot):
    if not snapshots:
        snapshots = []

    snapshots.append(new_snapshot)

    return snapshots


daily_stats = win.fold_window(
    "daily_stats",
    partitioned,
    clock,
    windower,
    builder=acc_builder,
    folder=calculate_stats,
    merger=window_merger,
)


op.inspect("daily_stats_down", daily_stats.down)
