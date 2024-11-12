from dataclasses import dataclass
from datetime import datetime


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


def acc_builder():
    return {
        "date": None,
        "customer_id": None,
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

    snapshot: Current accumulated statistics
    event: New event to incorporate into statistics

    Returns:
        dict: Updated statistics including:
            - count: Total number of events
            - avg_duration: Mean duration
            - median_duration: Median (p50) duration
            - p99_duration: 99th percentile duration
            - durations: Sorted list of all durations (for percentile calculations)
    """
    # Set the date and customer_id if this is the first event in the window
    if snapshot["date"] is None:
        snapshot["date"] = event.timestamp.date()
        snapshot["customer_id"] = event.customer_id

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
    """
    Collects output from each window into a list
    """
    if not snapshots:
        snapshots = []

    snapshots.append(new_snapshot)

    return snapshots


def window_to_db_row(item) -> dict:
    """
    Helper function that takes stream out from folded window snapshots
    and converts them into dicts that we can enter into db easily

    Arg: item is a tuple of (key, (window_id, snapshot))
    e.g. (cust_10, (21, {"customer_id": "cust_10"...}))
    """

    t, s = item[1]

    return {
        "customer_id": s["customer_id"],
        "date": s["date"],
        "count": s["count"],
        "errors": s["errors"],
        "avg_duration": s["avg_duration"],
        "median_duration": s["median_duration"],
        "p99_duration": s["p99_duration"],
    }
