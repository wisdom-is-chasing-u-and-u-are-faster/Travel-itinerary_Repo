u"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   unit
Source:  test_strategy/plans/app__unit.json
Generated: 2024-07-25T18:35:41.928331Z
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.services.itinerary_service import generate_daily_schedule
from app.services.geo_clustering import cluster_activities_by_proximity, haversine_distance_km
from app.models.schemas import DeltaMutation, InviteCollaboratorRequest, CheckoutRequest


@pytest.fixture
def client():
    """Provides a FastAPI TestClient for endpoint testing."""
    with TestClient(app) as c:
        yield c


def test_generate_daily_schedule_logic():
    """Verifies generate_daily_schedule produces a structured schedule.

test_id: app__unit__001
target: app.services.itinerary_service.generate_daily_schedule
requirement_id: REQ-F-001
ac_ids: REQ-F-001-AC-1
    """
    start_date = "2024-08-01"
    end_date = "2024-08-03"
    destination = "Tokyo"
    pacing = "Moderate"
    interests = ["Culture", "Dining"]

    # Mock the clustering function to isolate the schedule generation logic
    with patch("app.services.itinerary_service.cluster_activities_by_proximity", side_effect=lambda x, **kwargs: x) as mock_cluster:
        schedule = generate_daily_schedule(
            destination=destination,
            start_date_str=start_date,
            end_date_str=end_date,
            pacing=pacing,
            interests=interests
        )

        assert isinstance(schedule, list)
        assert len(schedule) == 3  # 3 days from Aug 1 to Aug 3
        mock_cluster.assert_called()

        for day in schedule:
            assert isinstance(day, dict)
            assert "day_number" in day
            assert "date" in day
            assert "activities" in day
            assert isinstance(day["activities"], list)
            for activity in day["activities"]:
                assert "title" in activity
                assert "time" in activity


def test_cluster_activities_by_geographic_proximity():
    """Verifies activities are grouped correctly by geographic proximity.

test_id: app__unit__002
target: app.services.geo_clustering.cluster_activities_by_proximity
requirement_id: REQ-F-005
ac_ids: REQ-F-005-AC-1
    """
    # Note: The source for geo_clustering was not provided, so this test is based on the function's described behavior.
    # It assumes the function returns a single list of activities, sorted by proximity.
    activities = [
        {"title": "Eiffel Tower", "latitude": 48.8584, "longitude": 2.2945}, # Paris
        {"title": "Big Ben", "latitude": 51.5007, "longitude": -0.1246}, # London (far)
        {"title": "Louvre Museum", "latitude": 48.8606, "longitude": 2.3376} # Paris (close)
    ]

    # The function is expected to re-order activities to group those that are close together.
    # Here, Eiffel Tower and Louvre should be adjacent in the output.
    clustered_activities = cluster_activities_by_proximity(activities, max_transit_km=200.0)

    assert len(clustered_activities) == 3
    titles = [act['title'] for act in clustered_activities]
    
    # Check that the two Paris locations are grouped together
    louvre_pos = titles.index("Louvre Museum")
    eiffel_pos = titles.index("Eiffel Tower")

    assert abs(louvre_pos - eiffel_pos) == 1, "Paris activities should be adjacent after clustering"


def test_apply_sync_mutations_to_itinerary(client: TestClient):
    """Tests applying DeltaMutation objects to an itinerary state.

test_id: app__unit__003
target: app.main.sync_itinerary
requirement_id: REQ-F-008
ac_ids: REQ-F-008-AC-1
    """
    itinerary_id = 1
    mutations = [
        DeltaMutation(entity="activity", action="update", data={"id": 1, "title": "New Title"}, timestamp="2024-01-01T12:00:00Z"),
        DeltaMutation(entity="activity", action="create", data={"day_id": 1, "title": "New Activity"}, timestamp="2024-01-01T12:01:00Z")
    ]
    sync_payload = {"client_timestamp": "2024-01-01T12:02:00Z", "mutations": [m.dict() for m in mutations]}

    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (itinerary_id,)  # Simulate itinerary exists

        response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "synced"
        assert data["applied_count"] == 2
        assert mock_cursor.execute.call_count >= 4 # SELECT, UPDATE, INSERT, UPDATE version


def test_invite_collaborator_logic(client: TestClient):
    """Verifies the business logic for inviting a collaborator.

test_id: app__unit__004
target: app.main.invite_collaborator
requirement_id: REQ-F-011
ac_ids: REQ-F-011-AC-1
    """
    trip_id = 1
    invite_req = InviteCollaboratorRequest(email="new.collaborator@example.com", role="Viewer")

    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 50

        response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invite_req.dict())

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "50"
        assert data["email"] == invite_req.email
        assert data["role"] == invite_req.role
        assert "invite_url" in data
        mock_conn.commit.assert_called_once()

    # Test invalid email
    invalid_req = {"email": "invalid-email", "role": "Viewer"}
    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invalid_req)
    assert response.status_code == 400
    assert "Valid email address is required" in response.json()["detail"]


def test_tokenize_checkout_logic(client: TestClient):
    """Verifies the tokenize_checkout function logic with a mocked payment provider.

test_id: app__unit__005
target: app.main.tokenize_checkout
requirement_id: REQ-F-016
ac_ids: REQ-F-016-AC-1
    """
    checkout_req = CheckoutRequest(experience_id="exp-abc-123", payment_token="tok_valid_payment_token", amount=99.99, currency="USD")

    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 101

        response = client.post("/api/v1/checkout/tokenize", json=checkout_req.dict())

        assert response.status_code == 201
        data = response.json()
        assert data["booking_id"] == "101"
        assert data["status"] == "confirmed"
        assert "voucher_code" in data
        assert data["voucher_code"].startswith("VOUCH-EXP-ABC-")
        mock_conn.commit.assert_called_once()

    # Test invalid token
    invalid_req = checkout_req.dict()
    invalid_req["payment_token"] = "err"
    response = client.post("/api/v1/checkout/tokenize", json=invalid_req)
    assert response.status_code == 402
    assert "Payment token authorization failed" in response.json()["detail"]


def test_calculate_haversine_distance_between_two_points():
    """Verifies the haversine_distance_km utility calculates distance correctly.

test_id: app__unit__006
target: app.services.geo_clustering.haversine_distance_km
requirement_id: no requirement
ac_ids: none
    """
    # Coordinates for Paris, France and London, UK
    lat1, lon1 = 48.8566, 2.3522  # Paris
    lat2, lon2 = 51.5074, -0.1278 # London

    distance = haversine_distance_km(lat1, lon1, lat2, lon2)

    # The approximate distance is ~344 km.
    assert distance == pytest.approx(344, abs=5)
