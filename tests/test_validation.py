"""
Domain Logic Validation Test Suite (ARCH-7851).
Verifies spatial geo-clustering bounds, FX decimal math, and debt simplification zero-sum balance.
"""

from app.services.geo_clustering import haversine_distance_km, cluster_activities_by_proximity, validate_geo_clustering
from app.services.expense_service import convert_to_base_usd, simplify_debts

def test_haversine_distance_calculation():
    """Verifies GPS distance calculation between known landmarks."""
    # Duomo to Uffizi Gallery in Florence (~600 meters / 0.6 km)
    duomo_lat, duomo_lon = 43.773145, 11.255960
    uffizi_lat, uffizi_lon = 43.767786, 11.255311
    dist = haversine_distance_km(duomo_lat, duomo_lon, uffizi_lat, uffizi_lon)
    assert 0.4 < dist < 0.8, f"Expected ~0.6 km, got {dist:.2f} km"

def test_geo_clustering_bound_enforcement():
    """Verifies spatial clustering satisfies REQ-F-005 (max 15 km per day)."""
    florence_activities = [
        {"id": "1", "title": "Duomo", "latitude": 43.773145, "longitude": 11.255960},
        {"id": "2", "title": "Piazzale Michelangelo", "latitude": 43.762900, "longitude": 11.265000},
        {"id": "3", "title": "Piazza della Signoria", "latitude": 43.769560, "longitude": 11.255814},
        {"id": "4", "title": "Uffizi Gallery", "latitude": 43.767786, "longitude": 11.255311}
    ]
    clustered = cluster_activities_by_proximity(florence_activities, max_transit_km=15.0)
    assert len(clustered) == 4
    is_valid, max_dist = validate_geo_clustering(clustered, max_km=15.0)
    assert is_valid is True
    assert max_dist < 5.0, f"Florence city center max transit distance should be under 5 km, got {max_dist}"

def test_debt_simplification_zero_sum_math():
    """Verifies group settlement graph simplification produces exact zero-sum balance (ARCH-7791)."""
    # Alice paid $90 ($30 each for Alice, Bob, Charlie).
    # Net: Alice: +$60, Bob: -$30, Charlie: -$30.
    balances = {
        "Alice": 60.00,
        "Bob": -30.00,
        "Charlie": -30.00
    }
    settlements = simplify_debts(balances)
    assert len(settlements) == 2

    total_transferred = sum(s["amount"] for s in settlements)
    assert round(total_transferred, 2) == 60.00
    for s in settlements:
        assert s["to_user"] == "Alice"
        assert s["amount"] == 30.00

def test_currency_conversion_precision():
    """Verifies arbitrary-precision decimal FX conversion."""
    converted = convert_to_base_usd(15000, "JPY")
    # 15,000 JPY at 150 JPY/USD = ~$100.00
    assert 99.0 <= float(converted) <= 101.0
