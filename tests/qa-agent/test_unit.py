import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import datetime

from app.main import app
from app.services.itinerary_service import generate_daily_schedule
from app.services.geo_clustering import cluster_activities_by_proximity
from app.models.schemas import SyncRequest, DeltaMutation

"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   unit
Source:  test_strategy/plans/app__unit.json
Generated: 2024-07-25T13:08:41.053579Z
"""

@pytest.fixture
def client():
    """Provides a FastAPI TestClient for making requests to the application."""
    return TestClient(app)

def test_generate_daily_schedule_structure():
    """Verify itinerary service generates daily schedules with correct structure.

    test_id: app__unit__001
    target: app.services.itinerary_service.generate_daily_schedule
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    # Patch the clustering function to isolate the schedule generation logic
    with patch('app.services.itinerary_service.cluster_activities_by_proximity', side_effect=lambda activities, **kwargs: activities) as mock_cluster:
        destination = "Tokyo"
        start_date = "2024-10-01"
        end_date = "2024-10-03"
        pacing = "Moderate"
        interests = ["Culture", "Food"]

        schedule = generate_daily_schedule(
            destination=destination,
            start_date_str=start_date,
            end_date_str=end_date,
            pacing=pacing,
            interests=interests
        )

        # The date range is 3 days inclusive
        assert isinstance(schedule, list)
        assert len(schedule) == 3

        # Check the structure of the first day
        day1 = schedule[0]
        assert isinstance(day1, dict)
        assert day1['day_number'] == 1
        assert day1['date'] == "2024-10-01"
        assert 'theme' in day1
        assert isinstance(day1['activities'], list)

        # Moderate pacing should result in 4 activities per day based on source
        assert len(day1['activities']) == 4
        mock_cluster.assert_called()

def test_geographic_clustering_of_activities():
    """Verify geographic clustering of activities groups them by proximity.

    test_id: app__unit__002
    target: app.services.geo_clustering.cluster_activities_by_proximity
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # Note: Source for cluster_activities_by_proximity not provided.
    # This test assumes the function reorders the list to group close activities together.
    mock_activities = [
        {'id': 'nyc_1', 'title': 'Statue of Liberty', 'latitude': 40.6892, 'longitude': -74.0445},
        {'id': 'la_1', 'title': 'Hollywood Sign', 'latitude': 34.1341, 'longitude': -118.3215},
        {'id': 'nyc_2', 'title': 'Empire State Building', 'latitude': 40.7484, 'longitude': -73.9857},
        {'id': 'la_2', 'title': 'Santa Monica Pier', 'latitude': 34.0195, 'longitude': -118.4912}
    ]

    clustered_result = cluster_activities_by_proximity(mock_activities, max_transit_km=20.0)

    assert isinstance(clustered_result, list)
    assert len(clustered_result) == len(mock_activities)

    # Check that all original activities are present
    original_ids = {act['id'] for act in mock_activities}
    result_ids = {act['id'] for act in clustered_result}
    assert original_ids == result_ids

    # Check if items from the same city are adjacent in the sorted list
    result_ids_list = [act['id'] for act in clustered_result]
    nyc_indices = sorted([result_ids_list.index('nyc_1'), result_ids_list.index('nyc_2')])
    la_indices = sorted([result_ids_list.index('la_1'), result_ids_list.index('la_2')])

    # A simple proxy for clustering is that items from the same group are next to each other.
    assert nyc_indices[1] - nyc_indices[0] == 1
    assert la_indices[1] - la_indices[0] == 1

@patch("app.main.get_db_connection")
def test_sync_itinerary_applies_mutations(mock_get_db, client: TestClient):
    """Verify sync logic applies mutations correctly via the endpoint.

    test_id: app__unit__003
    target: app.main.sync_itinerary
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    # Setup mock database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    # Simulate that the itinerary exists
    mock_cursor.fetchone.return_value = (1,)

    # Prepare a sync request payload
    update_mutation = DeltaMutation(
        entity="activity",
        action="update",
        data={"id": 101, "title": "Updated Activity Title"},
        timestamp=datetime.datetime.now().isoformat()
    )
    create_mutation = DeltaMutation(
        entity="activity",
        action="create",
        data={"day_id": 2, "title": "New Activity"},
        timestamp=datetime.datetime.now().isoformat()
    )
    sync_payload = {
        "client_timestamp": datetime.datetime.now().isoformat(),
        "mutations": [update_mutation.dict(), create_mutation.dict()]
    }

    itinerary_id = 1
    response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "synced"
    assert response_data["applied_count"] == 2

    # Verify database interactions
    mock_get_db.assert_called_once()
    mock_conn.cursor.assert_called_once()
    mock_cursor.fetchone.assert_called_once_with()
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()

    # Check that the correct SQL statements were executed
    execute_calls = mock_cursor.execute.call_args_list
    
    # Check for itinerary existence check
    assert any(call.args[0] == "SELECT id FROM itineraries WHERE id = ?" and call.args[1] == (itinerary_id,) for call in execute_calls)

    # Check for update mutation SQL
    update_sql = "UPDATE activities SET title = COALESCE(?, title), notes = COALESCE(?, notes) WHERE id = ?"
    update_params = ('Updated Activity Title', None, 101)
    assert any(call.args[0].strip() == update_sql and call.args[1] == update_params for call in execute_calls)

    # Check for create mutation SQL
    create_sql = "INSERT INTO activities (itinerary_id, day_id, time, title, location, cost) VALUES (?, ?, ?, ?, ?, ?)"
    create_params = (itinerary_id, 2, '09:00 AM', 'New Activity', '', 0.0)
    assert any(call.args[0].strip() == create_sql and call.args[1] == create_params for call in execute_calls)

    # Check for version bump
    version_sql = "UPDATE itineraries SET version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    assert any(call.args[0].strip() == version_sql and call.args[1] == (itinerary_id,) for call in execute_calls)
