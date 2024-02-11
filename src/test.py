from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "available"}


def test_create_short_url():
    response = client.post("/", json={"url": "https://www.example.com"})
    assert response.status_code == 201
    assert "short_id" in response.json()


def test_redirect_to_original():
    response = client.get("/1")
    assert response.status_code == 307


def test_delete_url():
    response = client.delete("/1")
    assert response.status_code == 200
    assert response.json() == {"detail": "URL deleted successfully."}


def test_get_url_usage():
    response = client.get("/1/status")
    assert response.status_code == 200
    assert "total" in response.json()
