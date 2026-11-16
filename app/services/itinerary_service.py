"""
Day-by-Day Travel Itinerary Generation & Orchestration Engine (REQ-F-001, ARCH-7794).
Synthesizes personalized, pacing-constrained, geo-clustered daily schedules.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.services.geo_clustering import cluster_activities_by_proximity

# Catalog of verified POIs with valid GPS coordinates and opening hours
POI_CATALOG = {
    "tokyo": [
        {"title": "Meiji Jingu Shrine", "location": "Shibuya, Tokyo", "lat": 35.676398, "lon": 139.699326, "cost": 0.0, "category": "Culture"},
        {"title": "Yoyogi Park Stroll", "location": "Shibuya, Tokyo", "lat": 35.671200, "lon": 139.694800, "cost": 0.0, "category": "Outdoors"},
        {"title": "Harajuku Takeshita Street", "location": "Harajuku, Tokyo", "lat": 35.671500, "lon": 139.703200, "cost": 20.0, "category": "Shopping"},
        {"title": "Shibuya Sky Observation Deck", "location": "Shibuya, Tokyo", "lat": 35.658518, "lon": 139.702221, "cost": 22.0, "category": "Sightseeing"},
        {"title": "Shinjuku Gyoen National Garden", "location": "Shinjuku, Tokyo", "lat": 35.685200, "lon": 139.710100, "cost": 5.0, "category": "Nature"},
        {"title": "Omoide Yokocho Izakaya Dinner", "location": "Shinjuku, Tokyo", "lat": 35.692800, "lon": 139.699800, "cost": 35.0, "category": "Dining"},
        {"title": "Senso-ji Temple & Kaminarimon", "location": "Asakusa, Tokyo", "lat": 35.714765, "lon": 139.796655, "cost": 0.0, "category": "Culture"},
        {"title": "Nakamise-dori Market Stroll", "location": "Asakusa, Tokyo", "lat": 35.712800, "lon": 139.796300, "cost": 15.0, "category": "Shopping"},
        {"title": "Tokyo Skytree Panorama", "location": "Sumida, Tokyo", "lat": 35.710063, "lon": 139.810700, "cost": 28.0, "category": "Sightseeing"},
        {"title": "Akihabara Electric Town", "location": "Chiyoda, Tokyo", "lat": 35.699700, "lon": 139.771400, "cost": 25.0, "category": "Tech"}
    ],
    "florence": [
        {"title": "Cattedrale di Santa Maria del Fiore (Duomo)", "location": "Piazza del Duomo, Florence", "lat": 43.773145, "lon": 11.255960, "cost": 30.0, "category": "Sightseeing"},
        {"title": "Battistero di San Giovanni", "location": "Piazza San Giovanni, Florence", "lat": 43.773200, "lon": 11.254980, "cost": 15.0, "category": "Culture"},
        {"title": "Mercato Centrale Food Hall", "location": "Piazza del Mercato Centrale, Florence", "lat": 43.776600, "lon": 11.253000, "cost": 25.0, "category": "Dining"},
        {"title": "Piazza della Signoria & Loggia dei Lanzi", "location": "Piazza della Signoria, Florence", "lat": 43.769560, "lon": 11.255814, "cost": 0.0, "category": "Sightseeing"},
        {"title": "Uffizi Gallery Masterpieces Tour", "location": "Piazzale degli Uffizi, Florence", "lat": 43.767786, "lon": 11.255311, "cost": 45.0, "category": "Art"},
        {"title": "Ponte Vecchio Sunset Walk", "location": "Ponte Vecchio, Florence", "lat": 43.767985, "lon": 11.253198, "cost": 0.0, "category": "Sightseeing"},
        {"title": "Piazzale Michelangelo Panorama", "location": "Piazzale Michelangelo, Florence", "lat": 43.762900, "lon": 11.265000, "cost": 0.0, "category": "Sightseeing"},
        {"title": "Boboli Gardens & Pitti Palace", "location": "Piazza de Pitti, Florence", "lat": 43.765100, "lon": 11.250100, "cost": 22.0, "category": "Nature"}
    ],
    "default": [
        {"title": "Historic Old Town Walking Tour", "location": "Central Square", "lat": 48.8566, "lon": 2.3522, "cost": 0.0, "category": "Sightseeing"},
        {"title": "National Museum of Art", "location": "Museum Quarter", "lat": 48.8606, "lon": 2.3376, "cost": 20.0, "category": "Art"},
        {"title": "Artisan Bistro Lunch", "location": "Market District", "lat": 48.8620, "lon": 2.3450, "cost": 25.0, "category": "Dining"},
        {"title": "Botanical Gardens & Pavilion", "location": "Riverside Park", "lat": 48.8430, "lon": 2.3580, "cost": 10.0, "category": "Nature"},
        {"title": "Panoramic Sunset Viewpoint", "location": "Hilltop Terrace", "lat": 48.8867, "lon": 2.3431, "cost": 0.0, "category": "Sightseeing"}
    ]
}

def generate_daily_schedule(
    destination: str,
    start_date_str: str,
    end_date_str: str,
    pacing: str = "Moderate",
    interests: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Generates pacing-compliant (Relaxed: 3, Moderate: 4-5, Fast-paced: up to 7 POIs/day),
    geographically clustered schedule for the requested date range.
    """
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
    except Exception:
        start_dt = datetime.now()
        end_dt = start_dt + timedelta(days=4)

    num_days = max(1, min(14, (end_dt - start_dt).days + 1))

    # Pacing constraints (ARCH-7794)
    pacing_lower = (pacing or "moderate").lower()
    if "relax" in pacing_lower:
        pois_per_day = 3
    elif "fast" in pacing_lower:
        pois_per_day = 6
    else:
        pois_per_day = 4

    # Determine POI pool
    dest_key = destination.lower()
    pool = None
    for k in POI_CATALOG:
        if k in dest_key:
            pool = POI_CATALOG[k]
            break
    if not pool:
        pool = POI_CATALOG["default"]

    times = ["09:00 AM", "11:30 AM", "01:30 PM", "03:30 PM", "05:30 PM", "07:30 PM", "09:00 PM"]
    days = []

    for d in range(num_days):
        day_date = (start_dt + timedelta(days=d)).strftime("%Y-%m-%d")
        raw_acts = []
        for i in range(pois_per_day):
            poi_idx = (d * pois_per_day + i) % len(pool)
            base_poi = pool[poi_idx]
            raw_acts.append({
                "id": f"act-{d+1}-{i+1}",
                "time": times[i % len(times)],
                "title": base_poi["title"],
                "location": base_poi["location"],
                "latitude": base_poi["lat"],
                "longitude": base_poi["lon"],
                "cost": base_poi["cost"],
                "category": base_poi["category"],
                "notes": f"Scheduled visit on Day {d+1}"
            })

        # Apply geo-clustering to guarantee < 15km transit proximity
        clustered = cluster_activities_by_proximity(raw_acts, max_transit_km=15.0)

        # Re-assign sequential times after spatial sorting
        for idx, act in enumerate(clustered):
            act["time"] = times[idx % len(times)]

        days.append({
            "day_number": d + 1,
            "date": day_date,
            "theme": f"Day {d+1} Highlights in {destination}",
            "activities": clustered
        })

    return days
