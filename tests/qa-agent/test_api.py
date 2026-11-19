"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   api
Source:  test_strategy/plans/app__api.json
Generated: 2024-07-12T11:45:16.123456Z
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import datetime

# Import the FastAPI app instance
from app.main import app

@pytest.fixture
def client():
    """Provides a FastAPI TestClient for making requests to the app."""
    with TestClient(app) as c:
        yield c


def test_app_api_001(client: TestClient):
    """Successfully generate a new itinerary.

    test_id: app__api__001
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    mock_schedule = [
        {
            "day_number": 1,
            "date": "2024-07-12",
            "theme": "Exploring the City",
            "activities": [
                {
                    "time": "10:00 AM",
                    "title": "Visit Central Park",
                    "location": "New York, NY",
                    "latitude": 40.785091, 
                    "longitude": -73.968285,
                    "cost": 0.0,
                    "category": "Outdoors",
                    "notes": "A lovely walk."
                }
            ]
        }
    ]

    with patch("app.main.generate_daily_schedule", return_value=mock_schedule):
        request_body = {
            "destination": "New York",
            "start_date": "2024-07-12",
            "end_date": "2024-07-12",
            "pacing": "Moderate",
            "interests": ["Sightseeing"],
            "budget_level": "Standard"
        }
        response = client.post("/api/v1/itineraries/generate", json=request_body)

    assert response.status_code == 201
    data = response.json()
    assert "itinerary_id" in data
    assert data["destination"] == "New York"
    assert "days" in data
    assert isinstance(data["days"], list)

def test_app_api_001_negative_bad_request(client: TestClient):
    """Fail to generate itinerary with invalid input.

    test_id: app__api__001_negative_bad_request
    target: POST /api/v1/itineraries/generate
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    request_body = {
        "destination": "",  # Invalid empty destination
        "start_date": "2024-07-12",
        "end_date": "2024-07-13"
    }
    response = client.post("/api/v1/itineraries/generate", json=request_body)
    assert response.status_code == 400

def test_app_api_002(client: TestClient):
    """Successfully retrieve an existing itinerary.

    test_id: app__api__002
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    # Assumes itinerary with ID 1 exists from seed data
    response = client.get("/api/v1/itineraries/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["destination"] == "Florence, Italy"
    assert "days" in data

def test_app_api_002_negative_not_found(client: TestClient):
    """Fail to retrieve a non-existent itinerary.

    test_id: app__api__002_negative_not_found
    target: GET /api/v1/itineraries/{id}
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get("/api/v1/itineraries/99999")
    assert response.status_code == 404

def test_app_api_003(client: TestClient):
    """Successfully process a checkout request.

    test_id: app__api__003
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    request_body = {
        "experience_id": "exp-test-1234",
        "payment_token": "tok_valid_visa",
        "amount": 99.99,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=request_body)
    assert response.status_code == 201
    data = response.json()
    assert "booking_id" in data
    assert data["status"] == "confirmed"

def test_app_api_003_negative_payment_failed(client: TestClient):
    """Handle a failed checkout request.

    test_id: app__api__003_negative_payment_failed
    target: POST /api/v1/checkout/tokenize
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    request_body = {
        "experience_id": "exp-fail-5678",
        "payment_token": "",  # Invalid token
        "amount": 49.99,
        "currency": "USD"
    }
    response = client.post("/api/v1/checkout/tokenize", json=request_body)
    assert response.status_code == 402

def test_app_api_004(client: TestClient):
    """Successfully invite a collaborator.

    test_id: app__api__004
    target: POST /api/v1/workspaces/{trip_id}/collaborators
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    # Assumes trip_id=1 exists from seed data
    trip_id = 1
    request_body = {
        "email": "new.collaborator@example.com",
        "role": "Viewer"
    }
    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=request_body)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "new.collaborator@example.com"
    assert data["role"] == "Viewer"

def test_app_api_005(client: TestClient):
    """Health check endpoint is available.

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
