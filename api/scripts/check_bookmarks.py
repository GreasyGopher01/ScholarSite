from fastapi.testclient import TestClient
import sys
import os
# ensure `api` package dir is on sys.path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import main


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, length=None):
        return self._docs


class FakeBookmarksCollection:
    def __init__(self, docs):
        self._docs = docs

    def find(self, query):
        # return a FakeCursor synchronously (mirrors motor's cursor object)
        return FakeCursor(self._docs)


def fake_verify_token():
    # return a fake user dict with an _id field
    return {"_id": "fake_user_id", "email": "test@example.com", "name": "Tester"}


def main_check():
    # inject fake dependencies
    main.app.dependency_overrides[main.verify_token] = lambda: fake_verify_token()
    main.bookmarks_collection = FakeBookmarksCollection([{"opportunityId": 42}, {"opportunityId": 99}])

    client = TestClient(main.app)
    r = client.get("/api/bookmarks", headers={"Authorization": "Bearer fake-token"})
    print("Status:", r.status_code)
    print("Body:", r.json())


if __name__ == "__main__":
    main_check()
