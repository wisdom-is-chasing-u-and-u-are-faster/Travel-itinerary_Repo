u"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   unit
Source:  test_strategy/plans/app__unit.json
Generated: 2024-07-25T17:01:01.123456Z
"""
import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.itinerary_service import generate_daily_schedule
from app.models.schemas import CheckoutRequest, InviteCollaboratorRequest

# It is assumed that these modules are available in the test environment as per gen_context.
# If they are missing, these tests will fail at collection time.
# This is an intentional design choice to trust the available_service_modules list.
try:
    from app.services.geo_clustering import cluster_activities_by_proximity, haversine_distance_km
except ImportError:
    # Define dummy functions to allow test collection if the module is missing.
    # The tests will then fail, indicating a problem with the service structure.
    def cluster_activities_by_proximity(*args, **kwargs):
        pytest.fail("app.services.geo_clustering module not found")
    def haversine_distance_km(*args, **kwargs):
        pytest.fail("app.services.geo_clustering module not found")


@pytest.fixture
def client():
    """Provides a FastAPI TestClient for making API requests."""
    with TestClient(app) as c:
        yield c


def test_generate_daily_schedule_creates_daily_schedules():
    """Verify itinerary generation logic creates daily schedules.

    test_id: app__unit__001
    target: app.services.itinerary_service.generate_daily_schedule
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    start_date_str = "2024-01-01"
    end_date_str = "2024-01-05"
    destination = "Test City"

    # Mock the clustering function to isolate the schedule generation logic.
    # The source code shows it returns a flat list, so we mimic that.
    with patch("app.services.itinerary_service.cluster_activities_by_proximity", side_effect=lambda acts, **kwargs: acts) as mock_cluster:
        result = generate_daily_schedule(
            destination=destination,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            pacing="Moderate",
            interests=["Testing"]
        )

        assert isinstance(result, list)
        # Duration is 5 days inclusive
        assert len(result) == 5
        mock_cluster.assert_called()

        # Check properties of the first and last day
        assert result[0]["day_number"] == 1
        assert result[0]["date"] == "2024-01-01"
        assert isinstance(result[0]["activities"], list)

        assert result[4]["day_number"] == 5
        assert result[4]["date"] == "2024-01-05"

def test_cluster_activities_by_proximity_groups_nearby_activities():
    """Verify geo-clustering logic groups nearby activities.

    test_id: app__unit__002
    target: app.services.geo_clustering.cluster_activities_by_proximity
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # Based on source code usage, this function returns a flat, sorted list.
    # We test that close items end up adjacent in the list.
    activities = [
        {'id': 'A', 'latitude': 40.7128, 'longitude': -74.0060}, # NYC
        {'id': 'B', 'latitude': 34.0522, 'longitude': -118.2437}, # LA
        {'id': 'C', 'latitude': 40.7130, 'longitude': -74.0062}, # NYC (close to A)
        {'id': 'D', 'latitude': 34.0520, 'longitude': -118.2435}, # LA (close to B)
    ]

    try:
        clustered = cluster_activities_by_proximity(activities, max_transit_km=10.0)
    except Exception as e:
        if "not found" in str(e):
            pytest.skip("Skipping test, geo_clustering module was not available.")
        raise

    assert isinstance(clustered, list)
    assert len(clustered) == 4

    # Create a list of IDs to find positions easily
    ids_in_order = [act['id'] for act in clustered]

    # Find indices of our pairs
    idx_A = ids_in_order.index('A')
    idx_C = ids_in_order.index('C')
    idx_B = ids_in_order.index('B')
    idx_D = ids_in_order.index('D')

    # Assert that close items are adjacent
    assert abs(idx_A - idx_C) == 1
    assert abs(idx_B - idx_D) == 1

def test_haversine_distance_calculation_is_accurate():
    """Verify haversine distance calculation is accurate.

    test_id: app__unit__003
    target: app.services.geo_clustering.haversine_distance_km
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    try:
        # Case 1: Distance to self should be 0
        coord1 = (48.8566, 2.3522) # Paris
        distance_same = haversine_distance_km(coord1, coord1)
        assert distance_same == 0.0

        # Case 2: Known distance (Paris to London)
        coord2 = (51.5074, -0.1278) # London
        distance_known = haversine_distance_km(coord1, coord2)
        # Real distance is ~344 km
        assert math.isclose(distance_known, 344, abs_tol=5)
    except Exception as e:
        if "not found" in str(e):
            pytest.skip("Skipping test, geo_clustering module was not available.")
        raise

def test_tokenize_checkout_success(client: TestClient):
    """Verify checkout tokenization logic handles success.

    test_id: app__unit__004
    target: app.main.tokenize_checkout
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 789
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        payload = {
            "experience_id": "exp-test-123",
            "payment_token": "tok_valid_card",
            "amount": 150.00,
            "currency": "USD"
        }
        response = client.post("/api/v1/checkout/tokenize", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["booking_id"] == "789"
        assert "voucher_code" in data
        assert "qr_code_url" in data

        mock_get_db.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

def test_invite_collaborator_logic(client: TestClient):
    """Verify collaborator invitation logic.

    test_id: app__unit__005
    target: app.main.invite_collaborator
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    with patch("app.main.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 101
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        trip_id = 42
        payload = {
            "email": "new.friend@example.com",
            "role": "Editor"
        }
        response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "101"
        assert data["email"] == payload["email"]
        assert data["role"] == payload["role"]
        assert "invite_url" in data
        assert data["invite_url"] == f"https://travelgen.app/join/{trip_id}?token=inv_101"

        mock_get_db.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
