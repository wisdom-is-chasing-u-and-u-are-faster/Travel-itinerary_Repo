import pytest
from fastapi.testclient import TestClient
import os
from datetime import datetime, timezone

# Set a consistent database path for the test session
TEST_DB = "./test_travel_platform.db"
os.environ["DATABASE_PATH"] = TEST_DB

# Ensure the app is imported after the environment variable is set
from app.main import app

@pytest.fixture(scope="module")
def client():
    # Clean up the test database before and after the test module runs
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    with TestClient(app) as c:
        yield c
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def create_test_itinerary(client: TestClient):
    """Helper function to create a new itinerary for tests that need one."""
    payload = {
        "destination": "Florence",
        "start_date": "2025-05-10",
        "end_date": "2025-05-12",
        "pacing": "Moderate",
        "interests": ["Art", "History"]
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    assert response.status_code == 201, f"Failed to create itinerary: {response.text}"
    return response.json()

def test_generate_new_itinerary_with_valid_preferences(client: TestClient):
    """Verifies that a user can generate a complete, day-by-day itinerary by providing valid travel preferences.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    payload = {
        "destination": "Tokyo",
        "start_date": "2025-11-01",
        "end_date": "2025-11-05",
        "pacing": "Fast-paced",
        "interests": ["Culture", "Tech", "Dining"]
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "itinerary_id" in data
    assert isinstance(int(data["itinerary_id"]), int)
    assert data["title"] == "Fast-paced Trip to Tokyo"
    assert "days" in data
    assert isinstance(data["days"], list)
    assert len(data["days"]) == 5

def test_fail_to_generate_itinerary_with_invalid_input(client: TestClient):
    """Verifies that the itinerary generation endpoint returns a 400 Bad Request error when provided with invalid data, such as a missing destination.

    test_id: app__api__001_negative_bad_input
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    payload = {
        "destination": "",  # Invalid empty destination
        "start_date": "2025-11-01",
        "end_date": "2025-11-05"
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert data["title"] == "Destination must not be empty"

def test_synchronize_client_side_mutations(client: TestClient):
    """Verifies the offline sync endpoint can accept and process a list of mutations from a client.

    test_id: app__api__002
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    itinerary = create_test_itinerary(client)
    itinerary_id = itinerary["itinerary_id"]
    activity_id_to_update = itinerary["days"][0]["activities"][0]["id"]

    sync_payload = {
        "client_timestamp": datetime.now(timezone.utc).isoformat(),
        "mutations": [
            {
                "entity": "activity",
                "action": "update",
                "data": {
                    "id": activity_id_to_update,
                    "title": "Updated Activity Title via Sync"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    }
    
    response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 1

def test_invite_collaborator_to_trip_workspace(client: TestClient):
    """Verifies that a user can be invited to a trip workspace via email.

    test_id: app__api__003
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    itinerary = create_test_itinerary(client)
    trip_id = itinerary["itinerary_id"]
    
    invite_payload = {
        "email": "new.collaborator@example.com",
        "role": "Viewer"
    }
    
    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invite_payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "new.collaborator@example.com"
    assert data["role"] == "Viewer"
    assert "invite_url" in data

def test_perform_tokenized_checkout_for_experience(client: TestClient):
    """Verifies the in-app checkout process by submitting a mock payment token.

    test_id: app__api__004
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_payload = {
        "experience_id": "exp-tokyo-food-tour-123",
        "payment_token": "tok_valid_visa_4242",
        "amount": 75.50,
        "currency": "USD"
    }
    
    response = client.post("/api/v1/checkout/tokenize", json=checkout_payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "booking_id" in data
    assert data["status"] == "confirmed"
    assert "voucher_code" in data
    assert data["voucher_code"].startswith("VOUCH-EXP-TOKY")

def test_fail_checkout_when_payment_is_declined(client: TestClient):
    """Verifies the checkout endpoint returns a 402 Payment Required status when the payment token is declined.

    test_id: app__api__004_negative_payment_failed
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_payload = {
        "experience_id": "exp-paris-museum-456",
        "payment_token": "tok",  # Invalid token length triggers failure
        "amount": 50.00,
        "currency": "EUR"
    }
    
    response = client.post("/api/v1/checkout/tokenize", json=checkout_payload)
    
    assert response.status_code == 402
    data = response.json()
    assert "Payment token authorization failed" in data["title"]

def test_health_check_endpoint(client: TestClient):
    """Verifies the health check endpoint is available and returns success.

    test_id: app__api__005
    target: GET /health
    requirement_id: REQ-N-001
    ac_ids: REQ-N-001-AC-1
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime" in data

def test_retrieve_specific_itinerary_by_id(client: TestClient):
    """Ensures the GET /api/v1/itineraries/{id} endpoint can fetch a created itinerary.

    test_id: app__api__006
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary = create_test_itinerary(client)
    itinerary_id = itinerary["itinerary_id"]
    
    response = client.get(f"/api/v1/itineraries/{itinerary_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == itinerary_id
    assert data["destination"] == "Florence"
    assert len(data["days"]) == 3

def test_update_existing_itinerary(client: TestClient):
    """Ensures the PUT /api/v1/itineraries/{id} endpoint can update an itinerary's properties.

    test_id: app__api__007
    target: PUT /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary = create_test_itinerary(client)
    itinerary_id = itinerary["itinerary_id"]
    
    update_payload = {
        "title": "Updated Florence Adventure"
    }
    
    response = client.put(f"/api/v1/itineraries/{itinerary_id}", json=update_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == itinerary_id
    assert data["title"] == "Updated Florence Adventure"
    assert "updated_at" in data

def test_delete_activity_from_itinerary(client: TestClient):
    """Smoke test for the DELETE /api/v1/itineraries/{id}/activities/{activity_id} endpoint.

    test_id: app__api__008
    target: DELETE /api/v1/itineraries/{id}/activities/{activity_id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary = create_test_itinerary(client)
    itinerary_id = itinerary["itinerary_id"]
    activity_id = itinerary["days"][0]["activities"][0]["id"]
    
    response = client.delete(f"/api/v1/itineraries/{itinerary_id}/activities/{activity_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"
    assert data["id"] == str(activity_id)

def test_retrieve_user_profile(client: TestClient):
    """Smoke test for the GET /api/v1/user/profile endpoint.

    test_id: app__api__009
    target: GET /api/v1/user/profile
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/user/profile")
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "email" in data
    assert "preferred_currency" in data
    assert "offline_caching_enabled" in data
