"""
End-to-End User Journey Tests (ARCH-7851).
Verifies complete SDLC flows mapping directly to Acceptance Criteria AC-1 through AC-5.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.init_db import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db("test_e2e.db")

@pytest.fixture
def client():
    return TestClient(app)

def test_e2e_ac1_itinerary_creation_journey(client):
    """AC-1: The user can input travel preferences and receive a complete, day-by-day itinerary."""
    req = {
        "destination": "Tokyo, Japan",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "pacing": "Moderate",
        "interests": ["Culture", "Tech", "Food"]
    }
    res = client.post("/api/v1/itineraries/generate", json=req)
    assert res.status_code == 201
    itin = res.json()
    assert itin["destination"] == "Tokyo, Japan"
    assert len(itin["days"]) == 5
    for day in itin["days"]:
        assert len(day["activities"]) >= 3

def test_e2e_ac2_offline_edit_and_sync_journey(client):
    """AC-2: The user can view and edit the generated itinerary, even when offline."""
    # 1. Fetch itinerary
    get_res = client.get("/api/v1/itineraries/1")
    assert get_res.status_code == 200
    itin = get_res.json()

    # 2. Simulate offline edit and sync back
    sync_payload = {
        "client_timestamp": "2026-10-10T16:00:00Z",
        "mutations": [
            {
                "entity": "activity",
                "action": "update",
                "data": {"id": 1, "notes": "Offline edit saved locally on mobile"},
                "timestamp": "2026-10-10T15:45:00Z"
            }
        ]
    }
    sync_res = client.post("/api/v1/itineraries/1/sync", json=sync_payload)
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "synced"

def test_e2e_ac3_multi_user_collaboration_journey(client):
    """AC-3: Multiple users can be invited to a trip, and their edits are synchronized in real-time."""
    # 1. Invite a group collaborator
    invite_res = client.post(
        "/api/v1/workspaces/1/collaborators",
        json={"email": "david.traveler@example.com", "role": "Editor"}
    )
    assert invite_res.status_code == 201
    assert "invite_url" in invite_res.json()

    # 2. Verify collaborator appears in workspace list
    list_res = client.get("/api/v1/workspaces/1/collaborators")
    assert list_res.status_code == 200
    emails = [c["email"] for c in list_res.json()["collaborators"]]
    assert "david.traveler@example.com" in emails

def test_e2e_ac4_tokenized_checkout_journey(client):
    """AC-4: UI provides options for booking tours with a seamless, tokenized checkout process."""
    # 1. Fetch available affiliate tours
    deals_res = client.get("/api/v1/affiliates/recommendations?destination=Florence")
    assert deals_res.status_code == 200
    deals = deals_res.json()["recommendations"]
    assert len(deals) > 0
    selected_deal = deals[0]

    # 2. Checkout directly in-app using tokenized payment (SAQ-A)
    checkout_res = client.post("/api/v1/checkout/tokenize", json={
        "experience_id": str(selected_deal["id"]),
        "payment_token": "tok_visa_instant_approval_4242",
        "amount": selected_deal["price"],
        "currency": "EUR"
    })
    assert checkout_res.status_code == 201
    booking = checkout_res.json()
    assert booking["status"] == "confirmed"
    assert "voucher_code" in booking

def test_e2e_ac5_backend_enforcement_and_health(client):
    """AC-5: Backend enforces all functional and non-functional requirements as detailed in project documentation."""
    # 1. Health probe
    health_res = client.get("/health")
    assert health_res.status_code == 200

    # 2. Admin telemetry constraints (TTFB <= 1.5s, uptime >= 99%)
    stats_res = client.get("/api/v1/admin/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["uptime_percent"] >= 99.0
    assert stats["p95_ttfb_seconds"] <= 1.5
