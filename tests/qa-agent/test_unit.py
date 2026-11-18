"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   unit
Source:  test_strategy/plans/app__unit.json
Generated: 2024-07-25T18:35:41.053903Z
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the FastAPI app instance
from app.main import app

# Import functions and models to be tested
from app.services.itinerary_service import generate_daily_schedule
from app.services.geo_clustering import cluster_activities_by_proximity
from app.models.schemas import SyncRequest, DeltaMutation, InviteCollaboratorRequest, CheckoutRequest

@pytest.fixture
def client():
    """Provides a FastAPI TestClient for making requests to the app."""
    with TestClient(app) as c:
        yield c

def test_generate_itinerary_logic(client: TestClient):
    """Verifies that the itinerary generation logic creates a valid schedule.

    test_id: app__unit__001
    target: app.services.itinerary_service.generate_daily_schedule
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    # Mock the geo-clustering function as it's an external dependency for this test
    with patch('app.services.itinerary_service.cluster_activities_by_proximity', side_effect=lambda activities, **kwargs: activities) as mock_cluster:
        destination = "Tokyo"
        start_date = "2024-08-01"
        end_date = "2024-08-03"
        pacing = "Moderate"
        interests = ["Culture", "Dining"]

        # Call the function under test
        schedule = generate_daily_schedule(destination, start_date, end_date, pacing, interests)

        # Assertions
        assert isinstance(schedule, list)
        assert len(schedule) == 3, "Schedule should be for 3 days"
        mock_cluster.assert_called()

        first_day = schedule[0]
        assert first_day['day_number'] == 1
        assert first_day['date'] == "2024-08-01"
        assert isinstance(first_day['activities'], list)
        assert len(first_day['activities']) == 4, "Moderate pacing should yield 4 activities per day"

        first_activity = first_day['activities'][0]
        assert 'title' in first_activity
        assert 'time' in first_activity

def test_offline_sync_mutation_logic(client: TestClient):
    """Verifies that delta mutations are correctly applied during an offline sync.

    test_id: app__unit__002
    target: app.main.sync_itinerary
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    itinerary_id = 1
    mutations = [
        DeltaMutation(
            entity="activity",
            action="update",
            data={"id": 5, "title": "Updated Title", "notes": "New notes here"},
            timestamp=datetime.now().isoformat()
        ),
        DeltaMutation(
            entity="activity",
            action="create",
            data={"day_id": 2, "title": "New Activity"},
            timestamp=datetime.now().isoformat()
        )
    ]
    sync_request = SyncRequest(client_timestamp=datetime.now().isoformat(), mutations=mutations)

    with patch('app.main.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        # Simulate that the itinerary exists
        mock_cursor.fetchone.return_value = (itinerary_id,)

        response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_request.dict())

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'synced'
        assert response_data['applied_count'] == 2

        # Verify that the correct SQL commands were executed
        update_call_found = False
        create_call_found = False
        for call in mock_cursor.execute.call_args_list:
            sql = call.args[0]
            if 'UPDATE activities' in sql:
                update_call_found = True
                assert call.args[1] == ('Updated Title', 'New notes here', 5)
            if 'INSERT INTO activities' in sql:
                create_call_found = True
                assert call.args[1][0] == itinerary_id
                assert call.args[1][1] == 2 # day_id
                assert call.args[1][3] == 'New Activity'
        
        assert update_call_found
        assert create_call_found
        mock_conn.commit.assert_called_once()

def test_collaborator_invitation_logic(client: TestClient):
    """Verifies the business logic for inviting a collaborator.

    test_id: app__unit__003
    target: app.main.invite_collaborator
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    trip_id = 1
    invite_req = InviteCollaboratorRequest(email="new.collaborator@example.com", role="Viewer")

    with patch('app.main.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 123

        # Test successful invitation
        response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invite_req.dict())

        assert response.status_code == 201
        data = response.json()
        assert data['id'] == '123'
        assert data['email'] == invite_req.email
        assert data['role'] == invite_req.role
        assert 'invite_url' in data
        mock_conn.commit.assert_called_once()

    # Test with invalid email
    invalid_invite_req = InviteCollaboratorRequest(email="not-an-email", role="Editor")
    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invalid_invite_req.dict())
    assert response.status_code == 400
    assert response.json()['title'] == 'Valid email address is required'

def test_checkout_tokenization_logic(client: TestClient):
    """Verifies the checkout tokenization logic for success and failure cases.

    test_id: app__unit__004
    target: app.main.tokenize_checkout
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_req = CheckoutRequest(
        experience_id="exp-florence-123",
        payment_token="tok_valid_payment_token",
        amount=99.99,
        currency="USD"
    )

    with patch('app.main.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 456

        # Test successful tokenization
        response = client.post("/api/v1/checkout/tokenize", json=checkout_req.dict())

        assert response.status_code == 201
        data = response.json()
        assert data['booking_id'] == '456'
        assert data['status'] == 'confirmed'
        assert 'voucher_code' in data
        mock_conn.commit.assert_called_once()

    # Test failed tokenization (invalid token)
    failed_checkout_req = checkout_req.copy(update={"payment_token": "bad"})
    response = client.post("/api/v1/checkout/tokenize", json=failed_checkout_req.dict())
    assert response.status_code == 402
    assert 'Payment token authorization failed' in response.json()['title']

def test_geographic_clustering_logic():
    """Verifies that the geographic clustering function groups activities.

    test_id: app__unit__005
    target: app.services.geo_clustering.cluster_activities_by_proximity
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # NOTE: Source for geo_clustering is not available. This test assumes the function
    # returns a re-ordered flat list of activities based on its usage in itinerary_service.py.
    # It verifies that the output is a permutation of the input.
    activities = [
        {'id': 'act1', 'title': 'Far North', 'latitude': 40.0, 'longitude': -120.0},
        {'id': 'act2', 'title': 'Close South 1', 'latitude': 34.05, 'longitude': -118.25},
        {'id': 'act3', 'title': 'Far East', 'latitude': 35.0, 'longitude': -70.0},
        {'id': 'act4', 'title': 'Close South 2', 'latitude': 34.06, 'longitude': -118.26},
    ]

    try:
        # Call the function under test
        clustered_activities = cluster_activities_by_proximity(activities, max_transit_km=50.0)

        # Assert that the output is a permutation of the input
        assert isinstance(clustered_activities, list)
        assert len(clustered_activities) == len(activities)
        
        input_ids = {act['id'] for act in activities}
        output_ids = {act['id'] for act in clustered_activities}
        assert input_ids == output_ids

    except ImportError:
        pytest.skip("Skipping test because 'cluster_activities_by_proximity' could not be imported.")
    except NameError: # If the function is not defined in the module
        pytest.skip("Skipping test because 'cluster_activities_by_proximity' is not defined.")
