from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_incidents():
    response = client.get("/incidents")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_incident():
    payload = {
        "service_name": "test-service",
        "title": "Test incident",
        "severity": "high"
    }

    response = client.post(
        "/incidents",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["service_name"] == "test-service"
    assert data["title"] == "Test incident"
    assert data["severity"] == "high"
    assert data["status"] == "open"


def test_invalid_incident():
    payload = {
        "service_name": "",
        "title": "",
        "severity": "high"
    }

    response = client.post(
        "/incidents",
        json=payload
    )

    assert response.status_code == 422


def test_incident_not_found():
    response = client.post(
        "/incidents/999999/investigate"
    )

    assert response.status_code == 404


def test_resolve_incident():
    payload = {
        "service_name": "resolve-test-service",
        "title": "Incident to resolve",
        "severity": "medium"
    }

    create_response = client.post(
        "/incidents",
        json=payload
    )

    assert create_response.status_code == 200

    incident_id = create_response.json()["id"]

    resolve_response = client.post(
        f"/incidents/{incident_id}/resolve"
    )

    assert resolve_response.status_code == 200

    data = resolve_response.json()

    assert data["status"] == "resolved"
    assert data["investigation_state"] == "resolved"
    assert data["resolved_at"] is not None