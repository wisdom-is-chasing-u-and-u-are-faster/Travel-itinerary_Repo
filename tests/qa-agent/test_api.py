import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import datetime
import time

from app.main import app


@pytest.fixture
def client():
    """A test client for the app."""
    # The app's lifespan manager handles DB initialization.
    # TestClient will call the lifespan events.
    with TestClient(app) as c:
        yield c


def test_generate_new_itinerary(client: TestClient):
    """Generate a new itinerary via API.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    mock_schedule = [
        {
            "day_number": 1,
            "date": "2025-07-01",
            "theme": "Exploring the Mock City",
            "activities": [
                {
                    "time": "10:00 AM",
                    "title": "Visit the Mock Museum",
                    "location": "Central Mockville",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "cost": 20.0,
                    "category": "Culture",
                    "notes": "A mock activity"
                }
            ]
        }
    ]
    payload = {
        "destination": "Mockville",
        "start_date": "2025-07-01",
        "end_date": "2025-07-01",
        "pacing": "Moderate",
        "interests": ["Culture", "History"],
        "budget_level": "Standard"
    }

    with patch("app.main.generate_daily_schedule", return_value=mock_schedule) as mock_gen_schedule:
        response = client.post("/api/v1/itineraries/generate", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "itinerary_id" in data
    assert data["title"] == "Moderate Trip to Mockville"
    assert data["destination"] == "Mockville"
    assert "days" in data
    assert len(data["days"]) == 1
    assert data["days"][0]["activities"][0]["title"] == "Visit the Mock Museum"
    mock_gen_schedule.assert_called_once_with(
        destination="Mockville",
        start_date_str="2025-07-01",
        end_date_str="2025-07-01",
        pacing="Moderate",
        interests=["Culture", "History"]
    )


def test_fail_to_generate_itinerary_with_invalid_input(client: TestClient):
    """Fail to generate itinerary with invalid input.

    test_id: app__api__001_negative_bad_request
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    payload = {
        "start_date": "2025-07-01",
        "end_date": "2025-07-01"
    }
    response = client.post("/api/v1/itineraries/generate", json=payload)
    assert response.status_code == 422


def test_perform_a_tokenized_checkout_for_an_experience(client: TestClient):
    """Perform a tokenized checkout for an experience.

    test_id: app__api__002
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    payload = {
        "experience_id": "exp-test-1234",
        "payment_token": "tok_valid_charge",
        "amount": 99.99,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "booking_id" in data
    assert data["status"] == "confirmed"
    assert "voucher_code" in data
    assert "qr_code_url" in data


def test_fail_checkout_when_payment_is_declined(client: TestClient):
    """Fail checkout when payment is declined.

    test_id: app__api__002_negative_payment_failed
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    payload = {
        "experience_id": "exp-test-1234",
        "payment_token": "bad",
        "amount": 99.99,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=payload)
    assert response.status_code == 402
    data = response.json()
    assert data["title"] == "Payment token authorization failed. Please check payment provider credentials."


def test_synchronize_offline_changes_to_an_itinerary(client: TestClient):
    """Synchronize offline changes to an itinerary.

    test_id: app__api__003
    target: POST /api/v1/itineraries/{id}/sync
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    itinerary_id = 1
    payload = {
        "client_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "mutations": [
            {
                "entity": "activity",
                "action": "update",
                "data": {"id": 1, "title": "Updated Duomo Visit"},
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            },
            {
                "entity": "activity",
                "action": "create",
                "data": {"day_id": 1, "title": "New Gelato Stop"},
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        ]
    }
    response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 2


def test_invite_a_collaborator_to_a_trip(client: TestClient):
    """Invite a collaborator to a trip.

    test_id: app__api__004
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    trip_id = 1
    payload = {
        "email": f"new.collaborator.{int(time.time())}@example.com",
        "role": "Viewer"
    }
    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == payload["email"]
    assert data["role"] == "Viewer"
    assert "invite_url" in data


def test_list_itineraries(client: TestClient):
    """List itineraries.

    test_id: app__api__005
    target: GET /api/v1/itineraries
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/itineraries")
    assert response.status_code == 200
    data = response.json()
    assert "itineraries" in data
    assert isinstance(data["itineraries"], list)
    assert len(data["itineraries"]) > 0


def test_get_a_specific_itinerary_by_id(client: TestClient):
    """Get a specific itinerary by ID.

    test_id: app__api__006
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary_id = 1
    response = client.get(f"/api/v1/itineraries/{itinerary_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(itinerary_id)
    assert data["destination"] == "Florence, Italy"
    assert "days" in data


def test_update_an_existing_itinerary(client: TestClient):
    """Update an existing itinerary.

    test_id: app__api__007
    target: PUT /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary_id = 1
    payload = {
        "title": "An Updated Florence Adventure"
    }
    response = client.put(f"/api/v1/itineraries/{itinerary_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(itinerary_id)
    assert data["title"] == "An Updated Florence Adventure"
    assert "updated_at" in data


def test_delete_an_activity_from_an_itinerary(client: TestClient):
    """Delete an activity from an itinerary.

    test_id: app__api__008
    target: DELETE /api/v1/itineraries/{id}/activities/{activity_id}
    requirement_id: no requirement
    ac_ids: none
    """
    itinerary_id = 1
    day_id = 1
    add_payload = {
        "day_id": day_id,
        "title": "Temporary Activity to Delete",
        "location": "Someplace",
        "time": "08:00 AM"
    }
    add_response = client.post(f"/api/v1/itineraries/{itinerary_id}/activities", json=add_payload)
    assert add_response.status_code == 201
    activity_to_delete = add_response.json()
    activity_id = int(activity_to_delete["id"])

    response = client.delete(f"/api/v1/itineraries/{itinerary_id}/activities/{activity_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"
    assert data["id"] == str(activity_id)

    get_response = client.get(f"/api/v1/itineraries/{itinerary_id}")
    get_data = get_response.json()
    activity_ids = [act['id'] for day in get_data['days'] for act in day['activities']]
    assert str(activity_id) not in activity_ids
