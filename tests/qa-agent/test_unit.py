import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import math
from fastapi import HTTPException

from app.services.itinerary_service import generate_daily_schedule
from app.services.geo_clustering import cluster_activities_by_proximity, haversine_distance_km
from app.main import sync_itinerary, tokenize_checkout, invite_collaborator
from app.models.schemas import (
    SyncRequest, 
    DeltaMutation, 
    CheckoutRequest, 
    InviteCollaboratorRequest
)

"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   unit
Source:  test_strategy/plans/app__unit.json
Generated: 2024-07-26T17:39:03.355325
"""

def test_itinerary_generation_logic():
    """Verifies that the `generate_daily_schedule` function in `itinerary_service.py` produces a structured itinerary based on inputs, with external dependencies mocked.

    test_id: app__unit__001
    target: app.services.itinerary_service.generate_daily_schedule
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    with patch('app.services.itinerary_service.cluster_activities_by_proximity', side_effect=lambda x, **kwargs: x) as mock_cluster:
        destination = "Tokyo"
        start_date_str = "2024-01-01"
        end_date_str = "2024-01-03"
        pacing = "Moderate"
        interests = ["Culture", "Dining"]

        result = generate_daily_schedule(destination, start_date_str, end_date_str, pacing, interests)

        assert isinstance(result, list)
        assert len(result) == 3
        mock_cluster.assert_called()

        for day in result:
            assert "day_number" in day
            assert "date" in day
            assert "theme" in day
            assert "activities" in day
            assert isinstance(day['activities'], list)
            # Moderate pacing should result in 4 activities
            assert len(day['activities']) == 4

def test_geographic_clustering_of_activities():
    """Verifies that the `cluster_activities_by_proximity` function correctly groups activities based on their geographic coordinates and a maximum transit distance.

    test_id: app__unit__002
    target: app.services.geo_clustering.cluster_activities_by_proximity
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # Since source for geo_clustering is not provided, this test assumes the function
    # reorders a flat list to group nearby items, as suggested by its usage in itinerary_service.py
    activities = [
        {'id': 'C', 'latitude': 50.0, 'longitude': 50.0}, # Far away
        {'id': 'A', 'latitude': 10.0, 'longitude': 10.0}, # Close to B
        {'id': 'B', 'latitude': 10.1, 'longitude': 10.1}, # Close to A
    ]

    # Mock the distance function to control clustering behavior
    def mock_haversine(lat1, lon1, lat2, lon2):
        points = {(lat1, lon1), (lat2, lon2)}
        if (10.0, 10.0) in points and (10.1, 10.1) in points:
            return 5.0 # Close
        return 100.0 # Far

    with patch('app.services.geo_clustering.haversine_distance_km', side_effect=mock_haversine):
        clustered = cluster_activities_by_proximity(activities, max_transit_km=15.0)

        assert len(clustered) == 3
        clustered_ids = [act['id'] for act in clustered]
        
        # Check that A and B are adjacent in the list
        pos_A = clustered_ids.index('A')
        pos_B = clustered_ids.index('B')
        assert abs(pos_A - pos_B) == 1

def test_haversine_distance_calculation():
    """Verifies the `haversine_distance_km` utility function calculates the distance between two GPS coordinates correctly.

    test_id: app__unit__003
    target: app.services.geo_clustering.haversine_distance_km
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # Coordinates for Paris, France and London, UK
    paris_lat, paris_lon = 48.8566, 2.3522
    london_lat, london_lon = 51.5074, -0.1278
    expected_distance_km = 344

    distance = haversine_distance_km(paris_lat, paris_lon, london_lat, london_lon)

    assert distance == pytest.approx(expected_distance_km, abs=5)

def test_offline_sync_mutation_processing():
    """Verifies the `sync_itinerary` endpoint logic correctly processes a list of `DeltaMutation` objects, mocking database interactions.

    test_id: app__unit__004
    target: app.main.sync_itinerary
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    with patch('app.main.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,) # Simulate itinerary exists

        mutations = [
            DeltaMutation(entity="activity", action="create", data={"day_id": 1, "title": "New Activity"}, timestamp="2024-01-01T12:00:00Z"),
            DeltaMutation(entity="activity", action="update", data={"id": 42, "title": "Updated Title"}, timestamp="2024-01-01T12:01:00Z")
        ]
        sync_req = SyncRequest(client_timestamp="2024-01-01T12:02:00Z", mutations=mutations)

        response = sync_itinerary(id=1, req=sync_req)

        assert response["status"] == "synced"
        assert response["applied_count"] == 2
        assert mock_cursor.execute.call_count == 4 # SELECT, UPDATE, INSERT, UPDATE version
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

def test_checkout_tokenization_logic():
    """Verifies the `tokenize_checkout` endpoint logic handles a checkout request, mocking database and payment provider interactions.

    test_id: app__unit__005
    target: app.main.tokenize_checkout
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    with patch('app.main.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 101

        checkout_req = CheckoutRequest(experience_id="exp-abc-123", payment_token="tok_valid_token", amount=99.99, currency="USD")

        response = tokenize_checkout(req=checkout_req)

        assert response["booking_id"] == "101"
        assert response["status"] == "confirmed"
        assert "VOUCH-EXP-ABC--7851" in response["voucher_code"]
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    with pytest.raises(HTTPException) as exc_info:
        invalid_req = CheckoutRequest(experience_id="exp-abc-123", payment_token="bad", amount=99.99, currency="USD")
        tokenize_checkout(req=invalid_req)
    assert exc_info.value.status_code == 402

def test_collaborator_invitation_logic():
    """Verifies the `invite_collaborator` endpoint logic handles an invitation request, mocking database interactions.

    test_id: app__unit__006
    target: app.main.invite_collaborator
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    with patch('app.main.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 202

        invite_req = InviteCollaboratorRequest(email="test.user@example.com", role="Viewer")

        response = invite_collaborator(trip_id=1, req=invite_req)

        assert response["id"] == "202"
        assert response["email"] == "test.user@example.com"
        assert response["role"] == "Viewer"
        assert "/join/1?token=inv_202" in response["invite_url"]
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    with pytest.raises(HTTPException) as exc_info:
        invalid_req = InviteCollaboratorRequest(email="invalid-email", role="Editor")
        invite_collaborator(trip_id=1, req=invalid_req)
    assert exc_info.value.status_code == 400