from typing import Sequence
from datetime import date
from pydantic import BaseModel

from sqlalchemy import create_engine, select

from logmetrics.db import snapshots


class Snapshot(BaseModel):
    customer_id: str
    date: date
    count: int
    errors: int
    avg_duration: float
    median_duration: float
    p99_duration: float


class SnapshotStore:

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url)

    def find(self, customer_id: str, from_date: date | None) -> Sequence[Snapshot]:
        stmt = select(snapshots).where(snapshots.c.customer_id == customer_id)

        if from_date is not None:
            stmt = stmt.where(snapshots.c.date >= from_date)

        results = []
        with self.engine.connect() as conn:
            for row in conn.execute(stmt):
                results.append(Snapshot(**row._asdict()))

        return results
