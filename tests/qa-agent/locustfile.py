"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   performance
Source:  test_strategy/plans/app__performance.json
Generated: 2024-07-25T18:18:04.000000Z
"""

import os
from datetime import datetime, timedelta
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# These values can be overridden by environment variables.
# The test will fail if the P95 response time is greater than this value in milliseconds.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "1500"))
# The test will fail if the failure ratio is greater than this value.
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

# --- Locust User Class ---
class TargetUser(HttpUser):
    """Simulates a user interacting with the Travel Itinerary Generator Platform."""
    # The host to test against, read from environment variable.
    host = os.environ.get("SERVICE_URL", "").strip()
    # Time a user waits between executing tasks, in seconds.
    wait_time = between(0.5, 2.5)

    @task(1)
    def get_health(self):
        """Task to check the health endpoint.

        test_id: app__performance__001 (partially)
        target: GET /health
        requirement_id: no requirement
        ac_ids: none
        """
        self.client.get("/health", name="/health")

    @task(3)
    def generate_short_itinerary(self):
        """Task to generate a short (3-day) itinerary.

        test_id: app__performance__001
        target: POST /api/v1/itineraries/generate
        requirement_id: REQ-N-002
        ac_ids: REQ-N-002-AC-1
        """
        start_date = datetime.now() + timedelta(days=30)
        end_date = start_date + timedelta(days=2)
        payload = {
            "destination": "Tokyo",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "pacing": "Moderate",
            "interests": ["Culture", "Dining"]
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate [short]"
        )

    @task(2)
    def generate_long_itinerary(self):
        """Task to generate a long (7-day) itinerary.

        test_id: app__performance__002
        target: POST /api/v1/itineraries/generate
        requirement_id: REQ-N-003
        ac_ids: REQ-N-003-AC-1
        """
        start_date = datetime.now() + timedelta(days=90)
        end_date = start_date + timedelta(days=6)
        payload = {
            "destination": "Florence",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "pacing": "Relaxed",
            "interests": ["Art", "Gastronomy", "History"]
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate [long]"
        )

# --- Event Hook for Threshold Enforcement ---
@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    This function is executed when the test run stops. It checks the final
    statistics against the defined thresholds and sets the process exit code
    to 1 (failure) if any threshold is breached.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds ---")
    print(f"P95 Response Time: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD}ms)")
    print(f"Failure Ratio: {fail_ratio:.2%} (Threshold: {FAIL_RATIO_THRESHOLD:.2%})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print("\n*** Test failed: Failure ratio exceeded threshold. ***")
        environment.process_exit_code = 1

    if p95_ms is not None and p95_ms > P95_MS_THRESHOLD:
        print("\n*** Test failed: P95 response time exceeded threshold. ***")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("\n--- Test passed: All performance thresholds met. ---")
