from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Date,
    Double,
    UniqueConstraint,
)

meta = MetaData()


snapshots = Table(
    "snapshots",
    meta,
    Column("snapshot_id", Integer, primary_key=True),
    Column("customer_id", String(255)),
    Column("date", Date),
    Column("count", Integer),
    Column("errors", Integer),
    Column("avg_duration", Double),
    Column("median_duration", Double),
    Column("p99_duration", Double),
    UniqueConstraint("customer_id", "date", name="idx_daily_stats_customer_date"),
)
