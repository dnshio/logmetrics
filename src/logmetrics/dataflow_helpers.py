from dataclasses import dataclass, asdict
from datetime import datetime, date


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


@dataclass
class Accumulator:
    date: date | None
    customer_id: str | None
    count: int
    errors: int
    avg_duration: float
    median_duration: float
    p99_duration: float
    durations: list


def acc_builder():
    return Accumulator(
        date=None,
        customer_id=None,
        count=0,
        errors=0,
        avg_duration=0,
        median_duration=0,
        p99_duration=0,
        durations=[],
    )


def calculate_stats(snapshot: Accumulator, event: LogEvent) -> Accumulator:
    """
    Maintains running statistics for event durations in a streaming context.

    snapshot: Current accumulated statistics
    event: New event to incorporate into statistics

    Returns:
        Accumulator: Updated snapshot:
    """
    count = snapshot.count + 1
    errors = snapshot.errors

    if event.status_code >= 400:
        errors += 1

    # Insert new duration while maintaining sorted order

    durations = [d for d in snapshot.durations]
    durations.append(event.duration)
    durations.sort()

    # Calculate running avg
    avg = (snapshot.avg_duration * (count - 1) + event.duration) / count

    # Calculate running median (p50)
    idx = (count - 1) // 2
    if count % 2 == 0:
        median = (durations[idx] + durations[idx + 1]) / 2
    else:
        median = durations[idx]

    # Calculate p99
    p99_idx = min(int(count * 0.99), count - 1)
    p99 = durations[p99_idx]

    return Accumulator(
        date=event.timestamp.date(),
        customer_id=event.customer_id,
        count=count,
        errors=errors,
        avg_duration=avg,
        median_duration=median,
        p99_duration=p99,
        durations=durations,
    )


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

    vals = asdict(s)

    return {k: v for k, v in asdict(s).items() if k != "durations"}
