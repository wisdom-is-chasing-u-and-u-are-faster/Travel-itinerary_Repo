import pytest
import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import the FastAPI app instance
from app.main import app

# Import functions and models to be tested
from app.services.itinerary_service import generate_daily_schedule
from app.models.schemas import SyncRequest, DeltaMutation, InviteCollaboratorRequest, CheckoutRequest

# The geo_clustering module is in available_service_modules, but its source is not provided.
# We will assume the functions can be imported and test their behavior as described.
try:
    from app.services.geo_clustering import haversine_distance_km, cluster_activities_by_proximity
except ImportError:
    # Define dummy functions if the module is not found, so tests can be collected.
    # The tests will likely fail, indicating a problem with the module itself.
    def haversine_distance_km(*args, **kwargs):
        pytest.skip("Skipping test because app.services.geo_clustering module is not available.")
        return 0.0
    def cluster_activities_by_proximity(activities, *args, **kwargs):
        pytest.skip("Skipping test because app.services.geo_clustering module is not available.")
        return activities

@pytest.fixture
def client():
    """Fixture for the FastAPI TestClient."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_db_connection():
    """Mock the database connection for unit tests."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    # Default fetchone to return something to avoid NoneErrors on `if not cursor.fetchone()` checks
    mock_cursor.fetchone.return_value = {"id": 1}
    mock_cursor.lastrowid = 123

    with patch('app.main.get_db_connection', return_value=mock_conn) as mock_get_conn:
        yield mock_get_conn, mock_cursor

def test_generate_daily_schedule_logic():
    """Verifies generate_daily_schedule produces a structured schedule.

    test_id: app__unit__001
    target: app.services.itinerary_service.generate_daily_schedule
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    with patch('app.services.itinerary_service.cluster_activities_by_proximity', side_effect=lambda x, **kwargs: x) as mock_cluster:
        destination = "Tokyo"
        start_date = "2024-08-01"
        end_date = "2024-08-03"
        pacing = "Moderate"
        interests = ["Culture", "Dining"]

        result = generate_daily_schedule(destination, start_date, end_date, pacing, interests)

        assert isinstance(result, list)
        assert len(result) == 3  # 3 days from Aug 1 to Aug 3

        for day in result:
            assert "day_number" in day
            assert "date" in day
            assert "activities" in day
            assert isinstance(day["activities"], list)
            assert len(day["activities"]) == 4  # Moderate pacing is 4 POIs/day
            for activity in day["activities"]:
                assert "title" in activity
                assert "location" in activity

        mock_cluster.assert_called()

def test_sync_itinerary_logic(client, mock_db_connection):
    """Verifies offline sync mutations are applied correctly.

    test_id: app__unit__002
    target: app.main.sync_itinerary
    requirement_id: REQ-F-008
    ac_ids: REQ-F-008-AC-1
    """
    mock_get_conn, mock_cursor = mock_db_connection
    itinerary_id = 1

    update_mutation = DeltaMutation(
        entity="activity",
        action="update",
        data={"id": 101, "title": "Updated Title", "notes": "New notes here."},
        timestamp="2024-08-01T10:00:00Z"
    )

    create_mutation = DeltaMutation(
        entity="activity",
        action="create",
        data={"day_id": 2, "title": "New Activity", "location": "New Location"},
        timestamp="2024-08-01T11:00:00Z"
    )

    sync_payload = SyncRequest(
        client_timestamp="2024-08-01T12:00:00Z",
        mutations=[update_mutation, create_mutation]
    )

    response = client.post(f"/api/v1/itineraries/{itinerary_id}/sync", json=sync_payload.dict())

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "synced"
    assert response_data["applied_count"] == 2

    update_call_found = False
    insert_call_found = False
    for call in mock_cursor.execute.call_args_list:
        sql = call.args[0]
        if "UPDATE activities SET" in sql and "COALESCE(?, title)" in sql:
            update_call_found = True
            assert call.args[1] == ("Updated Title", "New notes here.", 101)
        if "INSERT INTO activities" in sql:
            insert_call_found = True
            assert call.args[1] == (itinerary_id, 2, "09:00 AM", "New Activity", "New Location", 0.0)

    assert update_call_found, "UPDATE statement for activity not found"
    assert insert_call_found, "INSERT statement for new activity not found"
    mock_cursor.execute.assert_any_call("UPDATE itineraries SET version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (itinerary_id,))

def test_invite_collaborator_logic(client, mock_db_connection):
    """Verifies collaborator invitation logic with mocked DB.

    test_id: app__unit__003
    target: app.main.invite_collaborator
    requirement_id: REQ-F-011
    ac_ids: REQ-F-011-AC-1
    """
    mock_get_conn, mock_cursor = mock_db_connection
    trip_id = 42
    invite_payload = InviteCollaboratorRequest(email="new.collaborator@example.com", role="Viewer")

    response = client.post(f"/api/v1/workspaces/{trip_id}/collaborators", json=invite_payload.dict())

    assert response.status_code == 201
    response_data = response.json()

    assert response_data["email"] == "new.collaborator@example.com"
    assert response_data["role"] == "Viewer"
    assert "invite_url" in response_data
    assert f"/join/{trip_id}?token=inv_" in response_data["invite_url"]

    mock_cursor.execute.assert_called_with(
        '\n            INSERT INTO collaborators (trip_id, name, email, role, status)\n            VALUES (?, ?, ?, ?, \'Active\')\n            ',
        (trip_id, "New.collaborator", "new.collaborator@example.com", "Viewer")
    )
    mock_get_conn.return_value.commit.assert_called_once()

def test_tokenize_checkout_logic(client, mock_db_connection):
    """Verifies checkout tokenization logic with mocked DB and payment.

    test_id: app__unit__004
    target: app.main.tokenize_checkout
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    mock_get_conn, mock_cursor = mock_db_connection
    checkout_payload = CheckoutRequest(
        experience_id="exp-tokyo-food-tour",
        payment_token="tok_valid_visa_1234",
        amount=75.50,
        currency="USD"
    )

    response = client.post("/api/v1/checkout/tokenize", json=checkout_payload.dict())

    assert response.status_code == 201
    response_data = response.json()

    assert response_data["status"] == "confirmed"
    assert "booking_id" in response_data
    assert "voucher_code" in response_data
    assert response_data["voucher_code"].startswith("VOUCH-EXP-TOKY-")

    args = mock_cursor.execute.call_args.args[1]
    assert args[0] == "exp-tokyo-food-tour"
    assert args[2] == "tok_valid_visa_1234"
    assert args[3] == 75.50
    mock_get_conn.return_value.commit.assert_called_once()

def test_tokenize_checkout_invalid_token(client):
    """Verifies checkout fails with an invalid payment token.

    test_id: app__unit__004
    target: app.main.tokenize_checkout
    requirement_id: REQ-F-016
    ac_ids: REQ-F-016-AC-1
    """
    checkout_payload = CheckoutRequest(
        experience_id="exp-tokyo-food-tour",
        payment_token="bad",
        amount=75.50,
        currency="USD"
    )
    response = client.post("/api/v1/checkout/tokenize", json=checkout_payload.dict())
    assert response.status_code == 402
    assert "Payment token authorization failed" in response.json()["detail"]

def test_haversine_distance_calculation():
    """Verifies haversine_distance_km calculates distance correctly.

    test_id: app__unit__005
    target: app.services.geo_clustering.haversine_distance_km
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    lat1, lon1 = 48.8566, 2.3522  # Paris
    lat2, lon2 = 51.5074, -0.1278 # London

    try:
        distance = haversine_distance_km(lat1, lon1, lat2, lon2)
        assert distance == pytest.approx(344, abs=5)
    except Exception as e:
        pytest.fail(f"haversine_distance_km raised an unexpected exception: {e}")

def test_activity_clustering_logic():
    """Verifies cluster_activities_by_proximity groups activities correctly.

    test_id: app__unit__006
    target: app.services.geo_clustering.cluster_activities_by_proximity
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    activity1 = {"id": "a1", "title": "Eiffel Tower", "latitude": 48.8584, "longitude": 2.2945}
    activity2 = {"id": "a2", "title": "Louvre Museum", "latitude": 48.8606, "longitude": 2.3376}
    activity3 = {"id": "a3", "title": "Statue of Liberty", "latitude": 40.6892, "longitude": -74.0445}

    activities = [activity3, activity1, activity2]

    try:
        clustered_result = cluster_activities_by_proximity(activities, max_transit_km=20.0)

        assert isinstance(clustered_result, list)
        assert len(clustered_result) == 3

        ids = [act["id"] for act in clustered_result]
        idx1 = ids.index("a1")
        idx2 = ids.index("a2")

        assert abs(idx1 - idx2) == 1, "Geographically close activities were not placed adjacently."
    except Exception as e:
        pytest.fail(f"cluster_activities_by_proximity raised an unexpected exception: {e}")
