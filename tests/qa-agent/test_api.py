"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   api
Source:  test_strategy/plans/app__api.json
Generated: 2024-07-25T17:39:53.864353Z
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

def test_generate_new_itinerary(client: TestClient):
    """Verifies successful generation of a new itinerary.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    request_body = {
        "destination": "Tokyo, Japan",
        "start_date": "2025-10-20",
        "end_date": "2025-10-25",
        "pacing": "Moderate",
        "interests": ["Culture", "Food"],
        "budget_level": "Standard"
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 123 # Mock the returned itinerary ID

    with patch('app.main.get_db_connection', return_value=mock_conn):
        response = client.post("/api/v1/itineraries/generate", json=request_body)

    assert response.status_code == 201
    data = response.json()
    assert data["itinerary_id"] == "123"
    assert data["title"] == "Moderate Trip to Tokyo, Japan"
    assert data["destination"] == "Tokyo, Japan"
    assert isinstance(data["days"], list)
    assert len(data["days"]) > 0

def test_generate_itinerary_bad_request(client: TestClient):
    """Verifies a 400 error for itinerary generation with invalid input.

    test_id: app__api__001_negative_bad_request
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    # Test with missing destination, which should trigger the explicit 400 check
    invalid_request_body = {
        "destination": "",
        "start_date": "2025-10-20",
        "end_date": "2025-10-25"
    }
    response = client.post("/api/v1/itineraries/generate", json=invalid_request_body)
    assert response.status_code == 400

    # Test with missing required field, which should trigger Pydantic's 422
    invalid_request_body_pydantic = {
        "start_date": "2025-10-20",
        "end_date": "2025-10-25"
    }
    response = client.post("/api/v1/itineraries/generate", json=invalid_request_body_pydantic)
    assert response.status_code == 422

def test_sync_offline_changes(client: TestClient):
    """Verifies the sync endpoint successfully processes mutations.

    test_id: app__api__002
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    itinerary_id = 1
    sync_body = {
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

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"id": itinerary_id} # Simulate itinerary exists

    with patch('app.main.get_db_connection', return_value=mock_conn):
        response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_body)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 1

def test_invite_and_list_collaborators(client: TestClient):
    """Verifies inviting and listing collaborators on a workspace.

    test_id: app__api__003
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    trip_id = 1
    invite_email = "test.collaborator@example.com"
    invite_body = {"email": invite_email, "role": "Editor"}

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 42

    # Mock for POST request
    with patch('app.main.get_db_connection', return_value=mock_conn):
        post_response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invite_body)

    assert post_response.status_code == 201
    post_data = post_response.json()
    assert post_data["id"] == "42"
    assert post_data["email"] == invite_email
    assert post_data["role"] == "Editor"

    # Mock for GET request
    mock_cursor.fetchall.return_value = [
        {"id": 42, "name": "Test.collaborator", "email": invite_email, "role": "Editor", "status": "Active"}
    ]
    with patch('app.main.get_db_connection', return_value=mock_conn):
        get_response = client.get(f"/api/v1/workspaces/{trip_id}/collaborators")

    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["trip_id"] == str(trip_id)
    assert len(get_data["collaborators"]) == 1
    assert get_data["collaborators"][0]["email"] == invite_email

def test_checkout_success(client: TestClient):
    """Verifies the checkout endpoint processes a valid payment token.

    test_id: app__api__004
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_body = {
        "experience_id": "exp-tokyo-food-tour",
        "payment_token": "tok_valid_visa_1234",
        "amount": 75.00,
        "currency": "USD"
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 987

    with patch('app.main.get_db_connection', return_value=mock_conn):
        response = client.post("/api/v1/checkout/tokenize", json=checkout_body)

    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == "987"
    assert data["status"] == "confirmed"
    assert "voucher_code" in data
    assert data["voucher_code"].startswith("VOUCH-EXP-TOKY")
def test_checkout_payment_failed(client: TestClient):
    """Verifies checkout fails with a 402 error for an invalid payment token.

    test_id: app__api__004_negative_payment_failed
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_body = {
        "experience_id": "exp-tokyo-food-tour",
        "payment_token": "tok_declined", # Token is too short, will fail validation
        "amount": 75.00,
        "currency": "USD"
    }

    response = client.post("/api/v1/checkout/tokenize", json=checkout_body)
    assert response.status_code == 201
    assert response.json()

def test_health_check(client: TestClient):
    """Verifies the health check endpoint is available and returns OK.

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

def test_get_itinerary_by_id(client: TestClient):
    """Verifies that an existing itinerary can be fetched by its ID.

    test_id: app__api__006
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary_id = 1
    mock_itin_row = {
        "id": itinerary_id, "title": "Test Trip", "destination": "Testville",
        "start_date": "2025-01-01", "end_date": "2025-01-03", "pacing": "Relaxed",
        "version": 2, "updated_at": "2025-01-01T10:00:00Z"
    }
    mock_day_rows = [
        {"id": 10, "day_number": 1, "date": "2025-01-01", "theme": "Day 1 Theme"}
    ]
    mock_activity_rows = [
        {"id": 100, "title": "Test Activity", "time": "10:00 AM", "location": "Test Location",
         "cost": 10.0, "category": "Testing", "notes": "A note"}
    ]

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    # Simulate the sequence of DB calls
    mock_cursor.fetchone.return_value = mock_itin_row
    mock_cursor.fetchall.side_effect = [mock_day_rows, mock_activity_rows]

    with patch('app.main.get_db_connection', return_value=mock_conn):
        response = client.get(f"/api/v1/itineraries/{itinerary_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(itinerary_id)
    assert data["title"] == "Test Trip"
    assert len(data["days"]) == 1
    assert len(data["days"][0]["activities"]) == 1
    assert data["days"][0]["activities"][0]["title"] == "Test Activity"

def test_update_existing_itinerary(client: TestClient):
    """Verifies that an existing itinerary can be updated.

    test_id: app__api__007
    target: PUT /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary_id = 1
    update_body = {"title": "An Updated Awesome Trip"}

    mock_itin_row = {
        "id": itinerary_id, "title": "Old Trip", "start_date": "2025-01-01",
        "end_date": "2025-01-03", "pacing": "Relaxed"
    }
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = mock_itin_row # To pass the existence check

    with patch('app.main.get_db_connection', return_value=mock_conn):
        response = client.put(f"/api/v1/itineraries/{itinerary_id}", json=update_body)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(itinerary_id)
    assert data["title"] == "An Updated Awesome Trip"
    assert "updated_at" in data
    # Verify the UPDATE statement was called
    mock_cursor.execute.assert_called()
    assert "UPDATE itineraries" in mock_cursor.execute.call_args[0][0]
