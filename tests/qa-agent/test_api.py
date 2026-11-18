"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   api
Source:  test_strategy/plans/app__api.json
Generated: 2024-07-25T17:01:01.123456Z
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import datetime

# Import the FastAPI app instance
from app.main import app

@pytest.fixture
def client():
    """Provides a FastAPI TestClient for making requests to the app."""
    with TestClient(app) as c:
        yield c

def test_generate_new_itinerary_via_api(client: TestClient):
    """Generate a new itinerary via API.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    payload = {
        "destination": "Tokyo, Japan",
        "start_date": "2025-10-20",
        "end_date": "2025-10-25",
        "pacing": "Moderate",
        "interests": ["Culture", "Food"]
    }

    mock_schedule = [{
        "day_number": 1,
        "date": "2025-10-20",
        "theme": "Arrival and Shinjuku Exploration",
        "activities": []
    }]

    with patch("app.main.get_db_connection") as mock_get_db, \
         patch("app.main.generate_daily_schedule", return_value=mock_schedule) as mock_generate:
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 123 # Simulate new itinerary ID

        response = client.post("/api/v1/itineraries/generate", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["itinerary_id"] == "123"
    assert "Tokyo, Japan" in data["title"]
    assert isinstance(data["days"], list)
    assert len(data["days"]) > 0
    mock_generate.assert_called_once()

def test_fail_to_generate_itinerary_with_invalid_input(client: TestClient):
    """Fail to generate itinerary with invalid input.

    test_id: app__api__002_negative_bad_input
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    # The code specifically checks for an empty destination.
    payload = {
        "destination": "",
        "start_date": "2024-12-10",
        "end_date": "2024-12-05"
    }

    response = client.post("/api/v1/itineraries/generate", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert data["title"] == "Destination must not be empty"

def test_sync_an_itinerary_with_offline_changes(client: TestClient):
    """Sync an itinerary with offline changes.

    test_id: app__api__003
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    payload = {
        "client_timestamp": datetime.datetime.utcnow().isoformat(),
        "mutations": [
            {
                "entity": "activity",
                "action": "update",
                "data": {"id": 5, "notes": "Updated notes from offline."},
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        ]
    }

    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"id": 1} # Simulate itinerary exists

        response = client.post("/api/v1/itineraries/1/sync", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 1

def test_fail_to_sync_itinerary_for_a_non_existent_id(client: TestClient):
    """Fail to sync itinerary for a non-existent ID.

    test_id: app__api__004_negative_not_found
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    payload = {
        "client_timestamp": datetime.datetime.utcnow().isoformat(),
        "mutations": []
    }

    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None # Simulate itinerary does not exist

        response = client.post("/api/v1/itineraries/99999/sync", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert data["title"] == "Itinerary 99999 not found"

def test_invite_and_list_collaborators_in_a_workspace(client: TestClient):
    """Invite and list collaborators in a workspace.

    test_id: app__api__005
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    invite_payload = {"email": "new.collaborator@example.com", "role": "Viewer"}
    
    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 5 # New collaborator ID

        # Test inviting a collaborator
        response_post = client.post("/api/v1/workspaces/1/collaborators", json=invite_payload)
        assert response_post.status_code == 201
        post_data = response_post.json()
        assert post_data["id"] == "5"
        assert post_data["email"] == invite_payload["email"]

        # Mock the GET response
        mock_collaborators = [
            {"id": 1, "name": "Alex", "email": "alex@example.com", "role": "Owner", "status": "Active"},
            {"id": 5, "name": "New", "email": "new.collaborator@example.com", "role": "Viewer", "status": "Active"}
        ]
        mock_cursor.fetchall.return_value = mock_collaborators

        # Test listing collaborators
        response_get = client.get("/api/v1/workspaces/1/collaborators")
        assert response_get.status_code == 200
        get_data = response_get.json()
        assert len(get_data["collaborators"]) == 2
        assert any(c["email"] == invite_payload["email"] for c in get_data["collaborators"])

def test_successfully_checkout_for_an_experience(client: TestClient):
    """Successfully checkout for an experience.

    test_id: app__api__006
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    payload = {
        "experience_id": "exp-florence-tour",
        "payment_token": "tok_valid_visa_1234",
        "amount": 65.00,
        "currency": "EUR"
    }

    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 99 # New booking ID

        response = client.post("/api/v1/checkout/tokenize", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == "99"
    assert data["status"] == "confirmed"
    assert "VOUCH-" in data["voucher_code"]

def test_fail_checkout_when_payment_is_declined(client: TestClient):
    """Fail checkout when payment is declined.

    test_id: app__api__007_negative_payment_failed
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    # The code triggers a 402 if the token is too short.
    payload = {
        "experience_id": "exp-fail-case",
        "payment_token": "bad",
        "amount": 50.00,
        "currency": "USD"
    }

    response = client.post("/api/v1/checkout/tokenize", json=payload)

    assert response.status_code == 402
    data = response.json()
    assert "Payment token authorization failed" in data["title"]

def test_retrieve_a_specific_itinerary_by_id(client: TestClient):
    """Retrieve a specific itinerary by ID.

    test_id: app__api__008
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_itinerary_row = {
            "id": 1, "title": "Test Trip", "destination": "Testville",
            "start_date": "2024-01-01", "end_date": "2024-01-03",
            "pacing": "Moderate", "version": 1, "updated_at": "2024-01-01T10:00:00Z"
        }
        mock_days_rows = [
            {"id": 10, "day_number": 1, "date": "2024-01-01", "theme": "Day 1 Theme"}
        ]
        mock_activities_rows = [
            {"id": 100, "title": "Test Activity", "time": "10:00 AM", "location": "Test Location", "cost": 25.0, "category": "Testing", "notes": "A note."}
        ]

        mock_cursor.fetchone.return_value = mock_itinerary_row
        mock_cursor.fetchall.side_effect = [mock_days_rows, mock_activities_rows]

        response = client.get("/api/v1/itineraries/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["title"] == "Test Trip"
    assert len(data["days"]) == 1
    assert len(data["days"][0]["activities"]) == 1
    assert data["days"][0]["activities"][0]["title"] == "Test Activity"

def test_check_application_health(client: TestClient):
    """Check application health.

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
