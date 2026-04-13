from fastapi.testclient import TestClient
from bson import ObjectId
import main


def fake_verify_token():
    # return a fake user dict — no DB access required
    return {
        "_id": ObjectId(),
        "email": "test@example.com",
        "name": "Tester",
        "picture": None,
    }


def test_auth_me_override():
    main.app.dependency_overrides[main.verify_token] = lambda: fake_verify_token()
    client = TestClient(main.app)
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "test@example.com"
    assert body["name"] == "Tester"
    # cleanup override
    main.app.dependency_overrides.pop(main.verify_token, None)
