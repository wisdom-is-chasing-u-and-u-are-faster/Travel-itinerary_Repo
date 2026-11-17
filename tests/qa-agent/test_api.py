"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   api
Source:  test_strategy/plans/app__api.json
Generated: 2024-07-12T12:04:31.944351Z
"""
import os
import pytest
from fastapi.testclient import TestClient

# Use a dedicated test database file to avoid interfering with a potential dev database.
# This file will be created in the current working directory and removed after the test session.
TEST_DB_PATH = "./test_api_database.db"
os.environ["DATABASE_PATH"] = TEST_DB_PATH

# Import the app *after* setting the environment variable.
from app.main import app

@pytest.fixture(scope="session", autouse=True)
def manage_test_db():
    """Ensure the test database is created and seeded for the session, and cleaned up afterwards."""
    # The TestClient's context manager will trigger the app's lifespan events,
    # which includes initializing the database via init_db().
    # We just need to ensure the file is removed after the test session.
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.fixture(scope="module")
def client():
    """A module-scoped test client for the FastAPI application."""
    with TestClient(app) as c:
        yield c

def test_generate_new_itinerary(client):
    """Successfully generate a new itinerary.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    payload = {
        "destination": "Tokyo",
        "start_date": "2026-11-01",
        "end_date": "2026-11-03",
        "pacing": "Moderate",
        "interests": ["Culture", "Tech"]
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "itinerary_id" in data
    assert data["title"] == "Moderate Trip to Tokyo"
    assert data["destination"] == "Tokyo"
    assert "days" in data
    assert isinstance(data["days"], list)
    assert len(data["days"]) == 3

def test_generate_itinerary_invalid_input(client):
    """Fail to generate itinerary with invalid input.

    test_id: app__api__001_negative_bad_request
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    payload = {
        "start_date": "2026-11-01",
        "end_date": "2026-11-03",
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    assert response.status_code == 422

def test_retrieve_specific_itinerary(client):
    """Retrieve a specific itinerary by ID.

    test_id: app__api__002
    target: GET /api/v1/itineraries/{id}
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    response = client.get("/api/v1/itineraries/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["title"] == "Classic Italian Renaissance - Florence & Tuscany"
    assert "days" in data
    assert len(data["days"]) > 0

def test_retrieve_non_existent_itinerary(client):
    """Fail to retrieve a non-existent itinerary.

    test_id: app__api__002_negative_not_found
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/itineraries/99999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Itinerary 99999 not found"

def test_sync_itinerary_changes(client):
    """Synchronize client-side changes with the server.

    test_id: app__api__003
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    payload = {
        "client_timestamp": "2026-11-16T11:00:00Z",
        "mutations": [
            {
                "entity": "activity",
                "action": "update",
                "data": {
                    "id": 1,
                    "title": "Updated via Sync"
                },
                "timestamp": "2026-11-16T10:59:00Z"
            }
        ]
    }
    response = client.post("/api/v1/itineraries/1/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 1

def test_invite_collaborator(client):
    """Invite a collaborator to a trip.

    test_id: app__api__004
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    payload = {
        "email": "new.collaborator@example.com",
        "role": "Viewer"
    }
    response = client.post("/api/v1/workspaces/1/collaborators", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new.collaborator@example.com"
    assert data["role"] == "Viewer"
    assert "invite_url" in data

def test_perform_tokenized_checkout(client):
    """Perform a tokenized checkout for an activity.

    test_id: app__api__005
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    payload = {
        "experience_id": "exp-tokyo-skytree",
        "payment_token": "tok_valid_mastercard",
        "amount": 28.00,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "booking_id" in data
    assert data["status"] == "confirmed"
    assert "voucher_code" in data

def test_checkout_invalid_token(client):
    """Fail checkout with an invalid payment token.

    test_id: app__api__005_negative_payment_required
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    payload = {
        "experience_id": "exp-tokyo-skytree",
        "payment_token": "bad",
        "amount": 28.00,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=payload)
    assert response.status_code == 402
    data = response.json()
    assert "Payment token authorization failed" in data["detail"]

def test_check_health(client):
    """Check application health.

    test_id: app__api__006
    target: GET /health
    requirement_id: REQ-N-001
    ac_ids: REQ-N-001-AC-1
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_update_user_profile(client):
    """Update user profile.

    test_id: app__api__007
    target: PUT /api/v1/user/profile
    requirement_id: no requirement
    ac_ids: none
    """
    payload = {
        "name": "Alex Morgan (Updated)",
        "email": "alex.morgan@example.com",
        "preferred_currency": "EUR",
        "offline_caching_enabled": False,
        "notifications_enabled": False
    }
    response = client.put("/api/v1/user/profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"

def test_add_activity_to_itinerary(client):
    """Verify REQ-F-008-AC-1 via POST /api/v1/itineraries/{id}/activities.

    test_id: app__api__011
    target: POST /api/v1/itineraries/{id}/activities
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    payload = {
        "day_id": 1,
        "title": "New Test Activity",
        "location": "Test Location",
        "time": "08:00 PM"
    }
    response = client.post("/api/v1/itineraries/1/activities", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "New Test Activity"

def test_update_activity_in_itinerary(client):
    """Verify REQ-F-008-AC-1 via PUT /api/v1/itineraries/{id}/activities/{activity_id}.

    test_id: app__api__012
    target: PUT /api/v1/itineraries/{id}/activities/{activity_id}
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    payload = {
        "title": "Updated Duomo Visit",
        "notes": "Reservation confirmed."
    }
    response = client.put("/api/v1/itineraries/1/activities/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["title"] == "Updated Duomo Visit"

def test_list_itineraries_contract(client):
    """Verify API contract for GET /api/v1/itineraries.

    test_id: app__api__013
    target: GET /api/v1/itineraries
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/itineraries")
    assert response.status_code == 200
    data = response.json()
    assert "itineraries" in data
    assert isinstance(data["itineraries"], list)
    if data["itineraries"]:
        item = data["itineraries"][0]
        assert "id" in item
        assert "title" in item
        assert "destination" in item

def test_update_itinerary_contract(client):
    """Verify API contract for PUT /api/v1/itineraries/{id}.

    test_id: app__api__014
    target: PUT /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    payload = {
        "title": "My Awesome Florence Trip"
    }
    response = client.put("/api/v1/itineraries/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["title"] == "My Awesome Florence Trip"
    assert "updated_at" in data

def test_delete_activity_contract(client):
    """Verify API contract for DELETE /api/v1/itineraries/{id}/activities/{activity_id}.

    test_id: app__api__015
    target: DELETE /api/v1/itineraries/{id}/activities/{activity_id}
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.delete("/api/v1/itineraries/1/activities/2")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"
    assert data["id"] == "2"

def test_get_collaborators_contract(client):
    """Verify API contract for GET /api/v1/workspaces/{trip_id}/collaborators.

    test_id: app__api__016
    target: GET /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/workspaces/1/collaborators")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == "1"
    assert "collaborators" in data
    assert isinstance(data["collaborators"], list)

def test_get_expenses_contract(client):
    """Verify API contract for GET /api/v1/expenses/{trip_id}.

    test_id: app__api__017
    target: GET /api/v1/expenses/{trip_id}
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/expenses/1")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == "1"
    assert "total_spent" in data
    assert "expenses" in data
    assert "settlements" in data

def test_create_expense_contract(client):
    """Verify API contract for POST /api/v1/expenses/{trip_id}.

    test_id: app__api__018
    target: POST /api/v1/expenses/{trip_id}
    requirement_id: no requirement
    ac_ids: none
    """
    payload = {
        "title": "Gelato",
        "amount": 10.0,
        "currency": "EUR",
        "paid_by": "Alex Morgan",
        "split_between": ["Alex Morgan", "Sophia Chen"]
    }
    response = client.post("/api/v1/expenses/1", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "amount_base" in data

def test_get_affiliate_recommendations_contract(client):
    """Verify API contract for GET /api/v1/affiliates/recommendations.

    test_id: app__api__019
    target: GET /api/v1/affiliates/recommendations
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/affiliates/recommendations?destination=Florence")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)

def test_get_admin_stats_contract(client):
    """Verify API contract for GET /api/v1/admin/stats.

    test_id: app__api__020
    target: GET /api/v1/admin/stats
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_itineraries" in data
    assert "uptime_percent" in data

def test_get_user_profile_contract(client):
    """Verify API contract for GET /api/v1/user/profile.

    test_id: app__api__021
    target: GET /api/v1/user/profile
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/user/profile")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "email" in data
    assert data["email"] == "alex.morgan@example.com"

def test_get_user_export_contract(client):
    """Verify API contract for GET /api/v1/user/export.

    test_id: app__api__022
    target: GET /api/v1/user/export
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/user/export")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "download_url" in data

def test_get_root_contract(client):
    """Verify API contract for GET /.

    test_id: app__api__023
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_get_tokens_css_contract(client):
    """Verify API contract for GET /tokens.css.

    test_id: app__api__024
    target: GET /tokens.css
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/tokens.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
