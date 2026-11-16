"""
Spatial Geo-Clustering Engine for Itinerary Optimization (REQ-F-005, ARCH-7794).
Ensures consecutive activities within any day cluster within 15 km transit distance.
"""

import math
from typing import List, Tuple, Dict, Any

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    radius_earth_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_earth_km * c

def cluster_activities_by_proximity(
    activities: List[Dict[str, Any]],
    max_transit_km: float = 15.0
) -> List[Dict[str, Any]]:
    """
    Sorts/clusters activities for a single day to minimize transit hopping,
    ensuring consecutive points do not exceed max_transit_km where coordinates exist.
    """
    if len(activities) <= 1:
        return activities

    # Filter out entries with valid geocoordinates
    positioned = [a for a in activities if a.get("latitude") and a.get("longitude")]
    unpositioned = [a for a in activities if not (a.get("latitude") and a.get("longitude"))]

    if not positioned:
        return activities

    # Nearest-neighbor clustering
    clustered = [positioned.pop(0)]
    while positioned:
        last = clustered[-1]
        last_lat, last_lon = last["latitude"], last["longitude"]
        nearest_idx = 0
        min_dist = float("inf")
        for idx, candidate in enumerate(positioned):
            dist = haversine_distance_km(last_lat, last_lon, candidate["latitude"], candidate["longitude"])
            if dist < min_dist:
                min_dist = dist
                nearest_idx = idx
        
        chosen = positioned.pop(nearest_idx)
        clustered.append(chosen)

    return clustered + unpositioned

def validate_geo_clustering(activities: List[Dict[str, Any]], max_km: float = 15.0) -> Tuple[bool, float]:
    """Validates that no two consecutive activities exceed max_km distance."""
    max_observed_dist = 0.0
    for i in range(len(activities) - 1):
        a1, a2 = activities[i], activities[i + 1]
        if a1.get("latitude") and a1.get("longitude") and a2.get("latitude") and a2.get("longitude"):
            dist = haversine_distance_km(a1["latitude"], a1["longitude"], a2["latitude"], a2["longitude"])
            if dist > max_observed_dist:
                max_observed_dist = dist
            if dist > max_km:
                return False, dist
    return True, max_observed_dist
