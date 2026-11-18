import os
import datetime
from locust import HttpUser, task, between, events

# --- Performance Thresholds ---
# These values can be overridden by environment variables.
# P95 response time threshold in milliseconds.
# The plan mentions 1.5s (1500ms) and 30s (30000ms) for different scenarios.
# We will use a general default that can be configured at runtime.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "1500"))
# Maximum acceptable failure ratio (e.g., 0.01 = 1% of requests may fail).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

# --- Locust User Class ---
class TargetUser(HttpUser):
    """
    Simulates a user generating travel itineraries.
    - Hits the health check endpoint occasionally.
    - Primarily focuses on the itinerary generation endpoint.
    """
    # The base URL for the service under test, read from environment.
    host = os.environ.get("SERVICE_URL", "").strip()

    # Time a user waits between executing tasks, in seconds.
    wait_time = between(0.5, 2.5)

    @task(1)
    def get_health(self):
        """
        Task to hit the health check endpoint.
        This is a lightweight check to ensure the service is responsive.
        test_id: app__performance__003 (related, for availability)
        ac_ids: REQ-N-001-AC-1
        """
        self.client.get("/health", name="/health")

    @task(4)
    def generate_7_day_itinerary(self):
        """
        Task to generate a 7-day itinerary.
        This covers the core functionality and performance requirements.
        test_id: app__performance__001, app__performance__002
        ac_ids: REQ-N-002-AC-1, REQ-N-003-AC-1
        """
        start_date = datetime.date(2025, 10, 1)
        end_date = start_date + datetime.timedelta(days=6)
        payload = {
            "destination": "Tokyo",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "pacing": "Moderate",
            "interests": ["Culture", "Tech", "Dining"],
            "budget_level": "Standard"
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate"
        )

# --- Locust Event Hooks for Threshold Enforcement ---
@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    This function is called when the Locust test run stops.
    It checks the aggregated statistics against the defined performance thresholds.
    If any threshold is breached, it sets a non-zero exit code, causing the
    CI/CD pipeline to fail.
    """
    stats = environment.stats.total

    # 1. Check Failure Ratio
    fail_ratio = stats.fail_ratio
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"Test failed: Failure ratio ({fail_ratio:.2%}) exceeded threshold ({FAIL_RATIO_THRESHOLD:.2%})")
        environment.process_exit_code = 1

    # 2. Check P95 Response Time
    p95_ms = stats.get_response_time_percentile(0.95)
    if p95_ms is not None and p95_ms > P95_MS_THRESHOLD:
        print(f"Test failed: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD:.2f} ms)")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("Performance thresholds met.")
