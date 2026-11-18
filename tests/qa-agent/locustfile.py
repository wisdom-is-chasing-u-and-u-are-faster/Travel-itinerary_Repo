import os
from locust import HttpUser, task, between, events
import datetime

# QA Persona v2 -- auto-generated locustfile
# Service: app
# Suite:   performance
# Source:  test_strategy/plans/app__performance.json

# --- Environment-based Configuration ---
# The SERVICE_URL is provided by the test runner environment.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()

# Performance thresholds, configurable via environment variables.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "30000")) # Default from REQ-N-003
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01")) # 1% failure tolerance

class TargetUser(HttpUser):
    """Simulates a user generating travel itineraries."""
    host = SERVICE_URL
    wait_time = between(0.5, 2.5) # Wait 0.5-2.5s between tasks

    @task(3)
    def generate_7_day_itinerary(self):
        """Task for app__performance__002: Generate a 7-day itinerary."""
        start_date = datetime.date.today() + datetime.timedelta(days=30)
        end_date = start_date + datetime.timedelta(days=6) # 7 days total
        payload = {
            "destination": "Florence, Italy",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "pacing": "Moderate",
            "interests": ["Art", "Gastronomy"],
            "budget_level": "Standard"
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate [7-day]"
        )

    @task(1)
    def generate_short_itinerary(self):
        """Task for app__performance__001: Generate a short itinerary."""
        start_date = datetime.date.today() + datetime.timedelta(days=60)
        end_date = start_date + datetime.timedelta(days=2) # 3 days total
        payload = {
            "destination": "Tokyo, Japan",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "pacing": "Fast-paced",
            "interests": ["Culture", "Tech"],
            "budget_level": "Standard"
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate [short]"
        )

    @task(1)
    def get_health(self):
        """Task for app__performance__003: Monitor system availability via health endpoint."""
        self.client.get("/health", name="/health")

    @task(1)
    def get_homepage(self):
        """Simulates a user visiting the homepage."""
        self.client.get("/", name="/")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks if the run met the performance and availability thresholds.
    If not, sets the process exit code to 1, failing the CI/CD step.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds Check ---")
    print(f"P95 Response Time: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD:.2f}ms)")
    print(f"Failure Ratio: {fail_ratio:.4f} (Threshold: {FAIL_RATIO_THRESHOLD:.4f})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print("\n[FAILED] Failure ratio exceeded threshold.")
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        print("\n[FAILED] P95 response time exceeded threshold.")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("\n[PASSED] All performance thresholds met.")
