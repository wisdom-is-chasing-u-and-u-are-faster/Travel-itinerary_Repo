"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   api
Source:  test_strategy/plans/app__api.json
Generated: 2024-07-18T10:30:11.962383Z
"""

import pytest
from fastapi.testclient import TestClient
import datetime
import os
import uuid

# Ensure a unique, isolated database for each test run
os.environ["DATABASE_PATH"] = f"test_travel_platform_{uuid.uuid4().hex}.db"

from app.main import app

@pytest.fixture(scope="function")
def client():
    """Provides a new TestClient for each test function, ensuring isolation."""
    db_path = os.environ["DATABASE_PATH"]
    # The app's lifespan manager will call init_db, creating and seeding the DB.
    with TestClient(app) as c:
        yield c
    # Clean up the database file after the test function completes.
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def created_itinerary(client: TestClient) -> dict:
    """Fixture to create a new itinerary and return its details."""
    payload = {
        "destination": "Tokyo",
        "start_date": "2025-11-01",
        "end_date": "2025-11-06",
        "pacing": "Moderate",
        "interests": ["Culture", "Food"]
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    assert response.status_code == 201, f"Failed to create itinerary: {response.text}"
    itinerary = response.json()
    assert "itinerary_id" in itinerary
    return itinerary

def test_generate_a_new_personalized_itinerary(client: TestClient):
    """Generate a new personalized itinerary.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    payload = {
        "destination": "Florence",
        "start_date": "2026-10-10",
        "end_date": "2026-10-15",
        "pacing": "Relaxed",
        "interests": ["Art", "History", "Food"]
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "itinerary_id" in data
    assert data["destination"] == "Florence"
    assert len(data["days"]) > 0
    assert "activities" in data["days"][0]

def test_fail_to_generate_itinerary_with_invalid_input(client: TestClient):
    """Fail to generate itinerary with invalid input.

    test_id: app__api__002_negative_bad_request
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    # Test case with an empty destination string, which is handled by the endpoint's logic
    payload = {
        "destination": "",
        "start_date": "2026-10-10",
        "end_date": "2026-10-15"
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "Destination must not be empty" in data["detail"]

    # Test case with a missing required field, handled by Pydantic validation
    invalid_payload = {
        "start_date": "2026-10-10",
        "end_date": "2026-10-15"
    }
    response = client.post("/api/v1/itineraries/generate", json=invalid_payload)
    assert response.status_code == 422

def test_sync_offline_changes_to_an_itinerary(client: TestClient, created_itinerary: dict):
    """Sync offline changes to an itinerary.

    test_id: app__api__003
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    itinerary_id = created_itinerary["itinerary_id"]
    sync_payload = {
        "client_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "mutations": [
            {
                "entity": "activity",
                "action": "create",
                "data": {
                    "day_id": 1,
                    "title": "New Synced Activity",
                    "time": "08:00 AM",
                    "location": "Hotel Lobby"
                },
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        ]
    }
    response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 1

def test_fail_to_sync_changes_to_a_non_existent_itinerary(client: TestClient):
    """Fail to sync changes to a non-existent itinerary.

    test_id: app__api__004_negative_not_found
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    non_existent_id = 99999
    sync_payload = {
        "client_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "mutations": []
    }
    response = client.post(f"/api/v1/itineraries/{non_existent_id}/sync", json=sync_payload)
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == 404
    assert f"Itinerary {non_existent_id} not found" in data["detail"]

def test_invite_a_collaborator_to_a_trip_workspace(client: TestClient, created_itinerary: dict):
    """Invite a collaborator to a trip workspace.

    test_id: app__api__005
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    trip_id = created_itinerary["itinerary_id"]
    invite_payload = {
        "email": "new.collaborator@example.com",
        "role": "Editor"
    }
    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invite_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new.collaborator@example.com"
    assert "invite_url" in data
    assert data["invite_url"].startswith("https://travelgen.app/join/")

def test_perform_in_app_checkout_for_an_experience(client: TestClient):
    """Perform in-app checkout for an experience.

    test_id: app__api__006
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_payload = {
        "experience_id": "exp-tokyo-skytree-123",
        "payment_token": "tok_valid_payment_token_12345",
        "amount": 45.50,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=checkout_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"
    assert "booking_id" in data
    assert "voucher_code" in data
    assert data["voucher_code"].startswith("VOUCH-EXP-TOKY-")

def test_fail_checkout_when_payment_is_declined(client: TestClient):
    """Fail checkout when payment is declined.

    test_id: app__api__007_negative_payment_required
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    # The code simulates failure if token length is < 4
    checkout_payload = {
        "experience_id": "exp-tokyo-skytree-123",
        "payment_token": "bad",
        "amount": 45.50,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=checkout_payload)
    assert response.status_code == 402
    data = response.json()
    assert data["status"] == 402
    assert "Payment token authorization failed" in data["detail"]

def test_retrieve_a_specific_itinerary_by_id(client: TestClient, created_itinerary: dict):
    """Retrieve a specific itinerary by ID.

    test_id: app__api__008
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary_id = created_itinerary["itinerary_id"]
    response = client.get(f"/api/v1/itineraries/{itinerary_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == itinerary_id
    assert data["destination"] == created_itinerary["destination"]
    assert len(data["days"]) > 0

def test_health_check_endpoint_is_available(client: TestClient):
    """Verifies that the /health endpoint is active and returns a success status.

    test_id: app__api__009
    target: GET /health
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
