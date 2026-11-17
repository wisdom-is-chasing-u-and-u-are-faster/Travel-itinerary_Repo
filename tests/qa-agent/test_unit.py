"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   unit
Source:  test_strategy/plans/app__unit.json
Generated: 2024-07-12T13:45:00Z
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.main import app
from app.services.itinerary_service import generate_daily_schedule
from app.services.geo_clustering import cluster_activities_by_proximity
from app.models.schemas import SyncRequest, DeltaMutation, InviteCollaboratorRequest, CheckoutRequest

@pytest.fixture
def client():
    """Provides a FastAPI TestClient for making requests to the app."""
    with TestClient(app) as c:
        yield c

def test_generate_daily_schedule_logic(
    
):
    """Verifies generate_daily_schedule correctly structures output with mocked dependencies.

    test_id: app__unit__001
    target: app.services.itinerary_service.generate_daily_schedule
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    start_date = datetime.now()
    end_date = start_date + timedelta(days=2) # 3-day trip
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Mock the clustering function to isolate the schedule generation logic
    with patch("app.services.itinerary_service.cluster_activities_by_proximity", side_effect=lambda acts, **kwargs: acts) as mock_cluster:
        schedule = generate_daily_schedule(
            destination="Paris",
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            pacing="Moderate",
            interests=["Culture", "Dining"]
        )

        assert isinstance(schedule, list)
        assert len(schedule) == 3, "Schedule should be for 3 days"
        assert mock_cluster.call_count == 3, "Clustering should be called once per day"

        first_day = schedule[0]
        assert "day_number" in first_day
        assert "date" in first_day
        assert "activities" in first_day
        assert first_day["day_number"] == 1
        assert len(first_day["activities"]) == 4, "Moderate pacing should yield 4 activities per day"

def test_geographic_clustering_of_activities(
    
):
    """Ensures cluster_activities_by_proximity groups activities based on geographic coordinates.

    test_id: app__unit__002
    target: app.services.geo_clustering.cluster_activities_by_proximity
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # NOTE: The source for `cluster_activities_by_proximity` is not provided.
    # This test assumes a simple spatial sort where closer items are adjacent.
    activity_a = {"title": "Eiffel Tower", "latitude": 48.8584, "longitude": 2.2945}
    activity_b = {"title": "Louvre Museum", "latitude": 48.8606, "longitude": 2.3376}
    activity_c = {"title": "Disneyland Paris", "latitude": 48.8722, "longitude": 2.7758} # Far away

    activities = [activity_c, activity_a, activity_b] # Start with close items separated

    # The function is expected to reorder the list to group A and B together.
    clustered_activities = cluster_activities_by_proximity(activities, max_transit_km=20.0)

    assert len(clustered_activities) == 3
    assert set(act['title'] for act in clustered_activities) == {"Eiffel Tower", "Louvre Museum", "Disneyland Paris"}

    # Find indices of the close activities
    indices = {act['title']: i for i, act in enumerate(clustered_activities)}
    
    # Assert that the two close activities are adjacent in the sorted list
    assert abs(indices["Eiffel Tower"] - indices["Louvre Museum"]) == 1

def test_offline_sync_delta_mutation_parsing(
    client: TestClient
):
    from unittest.mock import patch, MagicMock
    from fastapi.testclient import TestClient
    from app.main import app, SyncRequest, DeltaMutation
    """Verifies sync_itinerary correctly parses mutations and calls the data layer.

    test_id: app__unit__003
    target: app.main.sync_itinerary
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,) # Simulate itinerary exists

    sync_req = SyncRequest(
        client_timestamp="2024-01-01T10:00:00Z",
        mutations=[
            DeltaMutation(entity="activity", action="update", data={"id": 101, "notes": "New notes"}, timestamp="2024-01-01T09:00:00Z"),
            DeltaMutation(entity="activity", action="create", data={"day_id": 2, "title": "New Activity"}, timestamp="2024-01-01T09:05:00Z"),
        ]
    )

    with patch("app.main.get_db_connection", return_value=mock_conn):
        response = client.post("/api/v1/itineraries/1/sync", json=sync_req.dict())

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 2

    assert mock_cursor.execute.call_count >= 3 # fetch, update, insert, update itinerary
    update_call = mock_cursor.execute.call_args_list[1]
    assert "UPDATE activities" in update_call.args[0]
    # The parameters tuple is the second argument to execute. The `title` is missing from the mutation, so it's None.
    assert update_call.args[1] == (None, "New notes", 101)

    insert_call = mock_cursor.execute.call_args_list[2]
    assert "INSERT INTO activities" in insert_call.args[0]
    # The parameters tuple is the second argument to execute.
    assert insert_call.args[1] == (1, 2, "09:00 AM", "New Activity", "", 0.0)

    assert mock_conn.commit.called

def test_collaborator_invitation_logic(
    client: TestClient
):
    """Verifies invite_collaborator attempts to create a collaborator record.

    test_id: app__unit__004
    target: app.main.invite_collaborator
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 123

    invite_req = InviteCollaboratorRequest(email="test.user@example.com", role="Viewer")

    with patch("app.main.get_db_connection", return_value=mock_conn):
        response = client.post("/api/v1/workspaces/1/collaborators", json=invite_req.dict())

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "123"
    assert data["email"] == "test.user@example.com"
    assert data["role"] == "Viewer"

    mock_cursor.execute.assert_called_once_with(
        '\n            INSERT INTO collaborators (trip_id, name, email, role, status)\n            VALUES (?, ?, ?, ?, \'Active\')\n            ',
        (1, 'Test.user', 'test.user@example.com', 'Viewer')
    )
    assert mock_conn.commit.called

def test_checkout_tokenization_logic(
    client: TestClient
):
    from unittest.mock import patch, MagicMock
    from fastapi.testclient import TestClient
    from app.main import app, CheckoutRequest
    """Verifies tokenize_checkout processes a request and interacts with the database.

    test_id: app__unit__005
    target: app.main.tokenize_checkout
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 456

    checkout_req = CheckoutRequest(
        experience_id="exp-tokyo-robot",
        payment_token="tok_valid_token_12345",
        amount=75.00,
        currency="USD"
    )

    with patch("app.main.get_db_connection", return_value=mock_conn):
        response = client.post("/api/v1/checkout/tokenize", json=checkout_req.dict())

    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == "456"
    assert data["status"] == "confirmed"
    assert data["voucher_code"] == "VOUCH-EXP-TOKY-7851"

    mock_cursor.execute.assert_called_once()
    # The positional arguments to execute() are (sql_query, params_tuple)
    sql_query, params = mock_cursor.execute.call_args.args
    assert "INSERT INTO bookings" in sql_query

    # Check the parameters tuple passed to the query
    # params[0] is experience_id, params[2] is payment_token
    assert params[0] == "exp-tokyo-robot"
    assert params[2] == "tok_valid_token_12345"
    assert mock_conn.commit.called

def test_checkout_tokenization_fails_on_bad_token(
    client: TestClient
):
    """Verifies tokenize_checkout returns 402 for an invalid payment token.

    test_id: app__unit__005
    target: app.main.tokenize_checkout
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_req = CheckoutRequest(
        experience_id="exp-tokyo-robot",
        payment_token="bad", # Token is too short
        amount=75.00,
        currency="USD"
    )

    response = client.post("/api/v1/checkout/tokenize", json=checkout_req.dict())

    assert response.status_code == 402
    data = response.json()
    assert data["title"] == "Payment token authorization failed. Please check payment provider credentials."
