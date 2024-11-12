from fastapi.testclient import TestClient
from logmetrics.api import app


client = TestClient(app)


def test_health_check():
    response = client.get("/_health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_request_parsing():
    resp = client.get("/customers/cust_200/stats?from=2024-11-12")
    assert resp.status_code == 200
    assert resp.json() == {"customer_id": "cust_200", "from": "2024-11-12"}
