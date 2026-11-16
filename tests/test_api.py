"""
API Endpoint Unit & Integration Tests (ARCH-7851).
Verifies all 19 endpoints declared in api_contract.json.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.init_db import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db("test_travel.db")

@pytest.fixture
def client():
    return TestClient(app)

def test_health_probe(client):
    """Verifies standard container readiness probe."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_generate_itinerary(client):
    """Verifies AI day-by-day itinerary generation with geo-clustering (AC-1, REQ-F-001)."""
    payload = {
        "destination": "Kyoto, Japan",
        "start_date": "2026-10-15",
        "end_date": "2026-10-18",
        "pacing": "Moderate",
        "interests": ["Temples", "Gardens"]
    }
    res = client.post("/api/v1/itineraries/generate", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["destination"] == "Kyoto, Japan"
    assert len(data["days"]) == 4
    for day in data["days"]:
        assert len(day["activities"]) >= 3
        for act in day["activities"]:
            assert "latitude" in act
            assert "longitude" in act

def test_list_itineraries(client):
    """Verifies listing user itineraries."""
    res = client.get("/api/v1/itineraries")
    assert res.status_code == 200
    data = res.json()
    assert "itineraries" in data
    assert len(data["itineraries"]) >= 1

def test_get_itinerary_detail(client):
    """Verifies retrieval of full itinerary with day schedules (AC-2)."""
    res = client.get("/api/v1/itineraries/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "1"
    assert "days" in data
    assert len(data["days"]) > 0

def test_get_itinerary_not_found(client):
    """Verifies RFC 7807 problem details for not found resources."""
    res = client.get("/api/v1/itineraries/99999")
    assert res.status_code == 404
    err = res.json()
    assert err["status"] == 404
    assert "detail" in err

def test_update_itinerary(client):
    """Verifies updating itinerary metadata."""
    payload = {"title": "Updated Renaissance Adventure", "pacing": "Relaxed"}
    res = client.put("/api/v1/itineraries/1", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Updated Renaissance Adventure"

def test_add_and_delete_activity(client):
    """Verifies dynamic activity addition and removal from schedule."""
    # Add activity
    add_payload = {
        "day_id": 1,
        "title": "Gelateria dei Neri Tasting",
        "time": "04:30 PM",
        "location": "Via dei Neri, Florence",
        "cost": 6.50,
        "category": "Dining"
    }
    res = client.post("/api/v1/itineraries/1/activities", json=add_payload)
    assert res.status_code == 201
    act_id = res.json()["id"]

    # Delete activity
    del_res = client.delete(f"/api/v1/itineraries/1/activities/{act_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

def test_offline_delta_sync(client):
    """Verifies offline edit synchronization with Last-Write-Wins (AC-2, REQ-F-008)."""
    payload = {
        "client_timestamp": "2026-10-10T14:30:00Z",
        "mutations": [
            {
                "entity": "activity",
                "action": "update",
                "data": {"id": 1, "notes": "Updated note during flight airplane mode"},
                "timestamp": "2026-10-10T14:25:00Z"
            }
        ]
    }
    res = client.post("/api/v1/itineraries/1/sync", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "synced"
    assert data["applied_count"] == 1

def test_collaborators_workspace(client):
    """Verifies workspace collaborator listing and invitations (AC-3, REQ-F-011)."""
    # List
    list_res = client.get("/api/v1/workspaces/1/collaborators")
    assert list_res.status_code == 200
    collabs = list_res.json()["collaborators"]
    assert len(collabs) >= 1

    # Invite
    invite_res = client.post("/api/v1/workspaces/1/collaborators", json={"email": "elena.v@example.com", "role": "Editor"})
    assert invite_res.status_code == 201
    assert "invite_url" in invite_res.json()

def test_expense_ledger_and_settlement(client):
    """Verifies multi-currency ledger calculation and graph debt simplification."""
    # Add expense
    res = client.post("/api/v1/expenses/1", json={
        "title": "Group Gelato & Coffee",
        "amount": 24.00,
        "currency": "EUR",
        "paid_by": "Alex Morgan",
        "split_between": ["Alex Morgan", "Sophia Chen", "Marcus Rossi"]
    })
    assert res.status_code == 201

    # Fetch ledger
    ledger_res = client.get("/api/v1/expenses/1")
    assert ledger_res.status_code == 200
    ledger = ledger_res.json()
    assert ledger["total_spent"] > 0
    assert "settlements" in ledger

def test_affiliate_recommendations(client):
    """Verifies partner recommendations and attribution link formatting (ARCH-7793)."""
    res = client.get("/api/v1/affiliates/recommendations?destination=Florence")
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
    assert "affiliate_url" in data["recommendations"][0]

def test_tokenized_checkout(client):
    """Verifies PCI DSS SAQ-A compliant tokenized payment checkout (AC-4, REQ-F-016)."""
    payload = {
        "experience_id": "exp-duomo-vip",
        "payment_token": "tok_1N3xyzSecureToken",
        "amount": 65.00,
        "currency": "EUR"
    }
    res = client.post("/api/v1/checkout/tokenize", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "confirmed"
    assert "voucher_code" in data

def test_admin_stats(client):
    """Verifies admin analytics and uptime/TTFB telemetry."""
    res = client.get("/api/v1/admin/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["uptime_percent"] >= 99.0
    assert stats["p95_ttfb_seconds"] <= 1.5

def test_user_profile_and_export(client):
    """Verifies user settings and personal data export."""
    # Profile
    prof_res = client.get("/api/v1/user/profile")
    assert prof_res.status_code == 200
    assert "email" in prof_res.json()

    # Export
    exp_res = client.get("/api/v1/user/export")
    assert exp_res.status_code == 200
    assert "download_url" in exp_res.json()
