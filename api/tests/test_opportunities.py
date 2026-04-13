from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_opportunities_list():
    r = client.get("/opportunities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert "id" in first and "title" in first and "deadline" in first
