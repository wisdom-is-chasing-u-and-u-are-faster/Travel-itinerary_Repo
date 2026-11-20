u"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   unit
Source:  test_strategy/plans/app__unit.json
Generated: 2024-07-12T13:40:43.123456Z
"""

import pytest
import math
from decimal import Decimal

# It is assumed that the `geo_clustering` module and its functions are available in the test environment,
# as indicated by `gen_context.imports.available_service_modules`.
# If the source code was not provided, we rely on the function signature and behavior
# inferred from its usage in `app.services.itinerary_service`.
try:
    from app.services.geo_clustering import cluster_activities_by_proximity, haversine_distance_km
except ImportError:
    # Define dummy functions if the module is not found, to allow test collection.
    # The tests will then fail, indicating a problem with the module's availability.
    def cluster_activities_by_proximity(activities, **kwargs):
        return activities
    def haversine_distance_km(lat1, lon1, lat2, lon2):
        return 0.0

from app.services.expense_service import convert_to_base_usd

def test_haversine_distance_calculation():
    """Verifies the haversine_distance_km function calculates distance correctly.

    test_id: app__unit__001
    target: app.services.geo_clustering.haversine_distance_km
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # Coordinates for London and Paris
    lat1, lon1 = 51.5072, -0.1276  # London
    lat2, lon2 = 48.8566, 2.3522   # Paris

    # Expected distance is approx 344 km
    expected_distance_km = 344
    calculated_distance = haversine_distance_km(lat1, lon1, lat2, lon2)

    assert calculated_distance == pytest.approx(expected_distance_km, abs=5) # Allow 5km tolerance

def test_geographic_clustering_of_activities():
    """Verifies that activities are clustered to minimize travel distance.

    test_id: app__unit__001
    target: app.services.geo_clustering.cluster_activities_by_proximity
    requirement_id: REQ-F-005
    ac_ids: REQ-F-005-AC-1
    """
    # Mock activities: A and C are close, B is far away.
    # A non-optimal order would be A -> B -> C.
    # A better order would be A -> C -> B.
    activities = [
        {'title': 'A', 'latitude': 40.7128, 'longitude': -74.0060}, # NYC
        {'title': 'B', 'latitude': 34.0522, 'longitude': -118.2437}, # LA
        {'title': 'C', 'latitude': 40.7831, 'longitude': -73.9712}, # Central Park, NYC
    ]

    def get_total_distance(activity_list):
        total_dist = 0
        for i in range(len(activity_list) - 1):
            act1 = activity_list[i]
            act2 = activity_list[i+1]
            total_dist += haversine_distance_km(act1['latitude'], act1['longitude'], act2['latitude'], act2['longitude'])
        return total_dist

    original_distance = get_total_distance(activities)

    clustered_activities = cluster_activities_by_proximity(activities, max_transit_km=5000.0)

    # 1. Ensure all original activities are present in the result
    assert len(clustered_activities) == len(activities)
    assert {act['title'] for act in clustered_activities} == {'A', 'B', 'C'}

    # 2. Ensure the new order is more efficient (or at least not worse)
    clustered_distance = get_total_distance(clustered_activities)
    assert clustered_distance <= original_distance

    # 3. For this specific case, the optimal order is B -> A -> C or C -> A -> B
    # The function should find an order better than the initial A -> B -> C
    # A->B is ~3935km, B->C is ~3965km. Total ~7900km
    # A->C is ~8km, C->B is ~3965km. Total ~3973km
    # The greedy algorithm starting with A should produce [A, C, B]
    assert clustered_activities[0]['title'] in ['A', 'C']
    assert clustered_activities[1]['title'] in ['A', 'C']
    assert clustered_activities[2]['title'] == 'B'


def test_currency_conversion_to_base_usd():
    """Verifies currency conversion to the base currency (USD).

    test_id: app__unit__002
    target: app.services.expense_service.convert_to_base_usd
    requirement_id: no requirement
    ac_ids: none
    """
    # Based on EXCHANGE_RATES_TO_USD in expense_service.py
    # {"EUR": Decimal("1.0800"), ...}
    amount_eur = 100.0
    expected_usd_from_eur = Decimal("108.0000")
    assert convert_to_base_usd(amount_eur, "EUR") == expected_usd_from_eur

    # Test conversion from a different currency
    amount_gbp = 100.0
    expected_usd_from_gbp = Decimal("125.0000")
    assert convert_to_base_usd(amount_gbp, "GBP") == expected_usd_from_gbp

def test_currency_conversion_with_base_currency():
    """Verifies converting from the base currency (USD) returns the same amount.

    test_id: app__unit__002
    target: app.services.expense_service.convert_to_base_usd
    requirement_id: no requirement
    ac_ids: none
    """
    amount_usd = 100.0
    expected_usd_from_usd = Decimal("100.0000")
    assert convert_to_base_usd(amount_usd, "USD") == expected_usd_from_usd

def test_currency_conversion_with_unknown_currency():
    """Verifies that an unknown currency is treated as having a 1:1 exchange rate with USD.

    test_id: app__unit__002
    target: app.services.expense_service.convert_to_base_usd
    requirement_id: no requirement
    ac_ids: none
    """
    amount_unknown = 100.0
    expected_usd_from_unknown = Decimal("100.0000")
    assert convert_to_base_usd(amount_unknown, "XYZ") == expected_usd_from_unknown
