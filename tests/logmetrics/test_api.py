from datetime import date
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from logmetrics.api import app
from logmetrics.snapshots import Snapshot


client = TestClient(app)


def test_health_check():
    response = client.get("/_health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


# def test_request_parsing(snap_store):
#     test_snapshot = dict(
#         customer_id="cust_123",
#         date=date(2024, 11, 10),
#         count=10,
#         errors=1,
#         avg_duration=0.3,
#         median_duration=0.31,
#         p99_duration=0.991,
#     )
#     snap_store.find.return_value = [Snapshot(**test_snapshot)]

#     resp = client.get("/customers/cust_123/stats?from=2024-11-12")
#     assert resp.status_code == 200
#     assert resp.json() == [test_snapshot]
