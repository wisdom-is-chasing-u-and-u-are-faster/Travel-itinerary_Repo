'''
QA Persona v2 -- auto-generated tests
Service: app
Suite:   api
Source:  test_strategy/plans/app__api.json
Generated: 2024-07-12T18:45:21.123456Z
'''
import os
import pytest
from fastapi.testclient import TestClient
import datetime

# Set a test database path before importing the app
# This ensures the app's lifespan manager uses a separate, clean database
DB_PATH = "./test_api_database.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_PATH"] = DB_PATH

from app.main import app

@pytest.fixture(scope="module")
def client():
    """
    A test client fixture that manages a test-specific database.
    The database is created and seeded once per module and cleaned up afterward.
    """
    # The TestClient context manager will trigger the app's lifespan events,
    # which includes initializing the database based on the DATABASE_PATH env var.
    with TestClient(app) as c:
        yield c
    
    # Teardown: clean up the test database file
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_generate_new_itinerary_successfully(client: TestClient):
    """Verifies that a POST request to /api/v1/itineraries/generate with valid data creates a new itinerary and returns a 201 status.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=5)
    payload = {
        "destination": "Florence, Italy",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "pacing": "Moderate",
        "interests": ["Art", "History"],
        "budget_level": "Standard"
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "itinerary_id" in data
    assert data["destination"] == "Florence, Italy"
    assert data["title"] == "Moderate Trip to Florence, Italy"
    assert "days" in data
    assert len(data["days"]) > 0

def test_fail_to_generate_itinerary_with_invalid_input(client: TestClient):
    """Verifies that a POST request to /api/v1/itineraries/generate with missing required fields returns a 422 status.

    test_id: app__api__001_negative_bad_request
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    response = client.post("/api/v1/itineraries/generate", json={})
    # FastAPI returns 422 for Pydantic validation errors
    assert response.status_code == 422

def test_sync_itinerary_with_valid_mutations(client: TestClient):
    """Verifies that POST /api/v1/itineraries/{id}/sync successfully applies changes and returns a 200 status.

    test_id: app__api__002
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    # First, create an itinerary to get a valid ID
    gen_payload = {
        "destination": "Sync Test City",
        "start_date": "2025-01-01",
        "end_date": "2025-01-02"
    }
    gen_response = client.post("/api/v1/itineraries/generate", json=gen_payload)
    assert gen_response.status_code == 201
    itinerary_id = gen_response.json()["itinerary_id"]

    sync_payload = {
        "client_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "mutations": [
            {
                "entity": "activity",
                "action": "create",
                "data": {"day_id": 1, "title": "New Synced Activity"},
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        ]
    }
    response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] > 0

def test_fail_to_sync_non_existent_itinerary(client: TestClient):
    """Verifies that POST /api/v1/itineraries/{id}/sync returns a 404 Not Found for an invalid itinerary ID.

    test_id: app__api__002_negative_not_found
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    sync_payload = {
        "client_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "mutations": []
    }
    response = client.post("/api/v1/itineraries/99999/sync", json=sync_payload)
    assert response.status_code == 404

def test_invite_a_collaborator_to_a_trip(client: TestClient):
    """Verifies that POST /api/v1/workspaces/{trip_id}/collaborators successfully invites a user and returns their details.

    test_id: app__api__003
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    # First, create an itinerary to get a valid trip_id
    gen_payload = {
        "destination": "Collaboration Trip",
        "start_date": "2025-02-01",
        "end_date": "2025-02-02"
    }
    gen_response = client.post("/api/v1/itineraries/generate", json=gen_payload)
    assert gen_response.status_code == 201
    trip_id = gen_response.json()["itinerary_id"]

    invite_payload = {"email": "new.collaborator@example.com", "role": "Viewer"}
    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invite_payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "new.collaborator@example.com"
    assert data["role"] == "Viewer"

def test_perform_a_successful_in_app_checkout(client: TestClient):
    """Verifies that POST /api/v1/checkout/tokenize processes a valid payment token and returns a booking confirmation.

    test_id: app__api__004
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    payload = {
        "experience_id": "exp-florence-tour-123",
        "payment_token": "tok_valid_visa_4242",
        "amount": 99.99,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "booking_id" in data
    assert data["status"] == "confirmed"
    assert "voucher_code" in data
    assert data["voucher_code"].startswith("VOUCH-EXP-FLOR")

def test_handle_a_failed_in_app_checkout(client: TestClient):
    """Verifies that POST /api/v1/checkout/tokenize returns a 402 Payment Required status when the payment provider rejects the transaction.

    test_id: app__api__004_negative_payment_failed
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    # The app logic raises 402 for short/invalid tokens
    payload = {
        "experience_id": "exp-failed-payment-456",
        "payment_token": "err",
        "amount": 150.00,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=payload)
    assert response.status_code == 402

def test_health_check_endpoint_is_available(client: TestClient):
    """Verifies that the GET /health endpoint is available and returns a 200 status with application health information.

    test_id: app__api__005
    target: GET /health
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime" in data

def test_retrieve_user_profile(client: TestClient):
    """Verifies that GET /api/v1/user/profile returns the current user's profile information.

    test_id: app__api__006
    target: GET /api/v1/user/profile
    requirement_id: no requirement
    ac_ids: none
    """
    # The endpoint is not authenticated and returns profile for user ID 1
    response = client.get("/api/v1/user/profile")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "email" in data
    # Based on seed data for user id=1
    assert data["email"] == "alex.morgan@example.com"
    assert "offline_caching_enabled" in data
