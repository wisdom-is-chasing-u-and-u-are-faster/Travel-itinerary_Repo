"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   performance
Source:  test_strategy/plans/app__performance.json
Generated: 2024-07-31T15:01:21.992683
"""

import os
from locust import HttpUser, events, task, between

# SERVICE_URL is the full base URL of the target service (e.g., http://localhost:8000)
SERVICE_URL = os.environ.get("SERVICE_URL", "http://localhost:8000").strip() or "http://localhost:8000"

# Performance thresholds from plan or environment variables
# Plan expects P95 total response time <= 30s (30000ms) for this specific generation task.
# Baseline error threshold is 5%, so fail ratio is 0.05.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "30000"))
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.05"))

class TargetUser(HttpUser):
    """Simulates a user generating travel itineraries."""
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    @task
    def generate_itinerary_task(self):
        """Task to generate a 7-day itinerary.

        test_id: app__performance__001
        target: POST /api/v1/itineraries/generate
        requirement_id: REQ-N-002, REQ-N-003
        ac_ids: REQ-N-002-AC-1, REQ-N-003-AC-1
        """
        payload = {
            "destination": "Tokyo",
            "start_date": "2025-07-01",
            "end_date": "2025-07-08", # 7-day trip
            "pacing": "Moderate",
            "interests": ["Culture", "Tech", "Dining"]
        }
        with self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="POST /api/v1/itineraries/generate",
            catch_response=True
        ) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if resp.status_code >= 400:
                resp.failure(f"HTTP {resp.status_code}")
            elif "text/html" in ctype:
                resp.failure("Unexpected Content-Type: text/html (SPA fallback instead of JSON API)")
            elif "application/json" not in ctype:
                resp.failure(f"Unexpected Content-Type: {ctype}")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Checks if performance thresholds were met and sets exit code on failure."""
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio {fail_ratio:.2%} exceeded threshold {FAIL_RATIO_THRESHOLD:.2%}")
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time {p95_ms:.0f}ms exceeded threshold {P95_MS_THRESHOLD:.0f}ms")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("PASS: All performance thresholds met.")
