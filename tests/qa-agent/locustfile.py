import os
import time
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# These values can be overridden by environment variables
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "30000")) # Default to 30s from REQ-N-003
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01")) # Default to 1% failure rate

class TargetUser(HttpUser):
    """
    Simulates a user generating travel itineraries.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5) # Wait 0.5-1.5s between tasks

    @task(3)
    def generate_7_day_itinerary(self):
        """
        Simulates generating a 7-day itinerary, the primary workload.
        This task corresponds to test_ids: app__performance__001, app__performance__002
        """
        payload = {
            "destination": "Tokyo",
            "start_date": "2025-10-10",
            "end_date": "2025-10-17", # 7-day trip
            "pacing": "Moderate",
            "interests": ["Culture", "Dining", "Tech"],
            "budget_level": "Standard"
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate"
        )

    @task(1)
    def get_health(self):
        """
        Checks the basic health of the service.
        This task corresponds to test_id: app__performance__003 (availability monitoring)
        """
        self.client.get("/health", name="/health")

    @task(1)
    def get_homepage(self):
        """
        Simulates a user visiting the homepage.
        """
        self.client.get("/", name="/")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks if the performance test run met the defined SLOs/thresholds.
    If not, it sets a non-zero exit code, causing the CI/CD pipeline to fail.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Summary ---")
    print(f"P95 Response Time: {p95_ms:.2f} ms")
    print(f"Failure Ratio: {fail_ratio*100:.2f}%")
    print(f"-------------------------")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio ({fail_ratio*100:.2f}%) exceeded threshold ({FAIL_RATIO_THRESHOLD*100:.2f}%)")
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD:.2f} ms)")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("PASS: All performance thresholds met.")
