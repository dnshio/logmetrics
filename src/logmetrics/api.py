import os
from datetime import date
from fastapi import FastAPI, Query
from logmetrics.snapshots import SnapshotStore


app = FastAPI()

snap_store = SnapshotStore(os.environ.get("DB_URL", ""))


@app.get("/_health")
async def health_check():
    return {"status": "OK"}


@app.get("/customers/{customer_id}/stats")
async def stats(customer_id: str, from_date: date | None = Query(None, alias="from")):
    return snap_store.find(customer_id=customer_id, from_date=from_date)
