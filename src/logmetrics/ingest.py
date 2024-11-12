import os
from datetime import datetime, timedelta, timezone


import bytewax.operators as op
import bytewax.operators.windowing as win
from bytewax.operators.windowing import EventClock, TumblingWindower
from bytewax.connectors.files import FileSource
from bytewax.dataflow import Dataflow

from logmetrics.connectors import TableSink
from logmetrics.db import snapshots as snapshots_table
from logmetrics.dataflow_helpers import (
    event_from_raw,
    acc_builder,
    calculate_stats,
    window_merger,
    window_to_db_row,
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


align_to = datetime.now(timezone.utc).replace(
    hour=0, minute=0, second=0, microsecond=0
) - timedelta(days=60)

windower = TumblingWindower(align_to=align_to, length=timedelta(days=1))


daily_stats = win.fold_window(
    "daily_stats",
    partitioned,
    clock,
    windower,
    builder=acc_builder,
    folder=calculate_stats,
    merger=window_merger,
)

op.output(
    "db_out",
    daily_stats.down,
    TableSink(
        dsn=os.environ.get("DB_URL", ""),
        table=snapshots_table,
        value_generator=window_to_db_row,
        reset_table=True,
    ),
)


op.inspect("daily_stats_down", daily_stats.down)
