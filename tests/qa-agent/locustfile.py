import os
import datetime
from locust import HttpUser, task, between, events

# --- Performance Thresholds ---
# These values are configurable via environment variables.
# P95 response time threshold in milliseconds.
# The test will fail if the 95th percentile response time exceeds this value.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "30000"))

# Failure ratio threshold.
# The test will fail if the percentage of failed requests exceeds this ratio (e.g., 0.01 = 1%).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

# --- Test Configuration ---
# The base URL for the service under test. This is set by the test runner.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()

class ItineraryUser(HttpUser):
    """
    Simulates a user generating travel itineraries.
    - Hits the health check endpoint.
    - Generates short (3-day) and long (7-day) itineraries.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 2.5) # Wait between 0.5 and 2.5 seconds between tasks

    @task(1)
    def get_health(self):
        """
        Task to check the health of the service.
        test_id: app__performance__003
        """
        self.client.get("/health", name="/health")

    @task(3)
    def generate_short_itinerary(self):
        """
        Task to generate a standard 3-day itinerary.
        This covers the general TTFB measurement.
        test_id: app__performance__001
        ac_ids: REQ-N-002-AC-1
        """
        start_date = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.date.today() + datetime.timedelta(days=33)).strftime("%Y-%m-%d")
        payload = {
            "destination": "Tokyo, Japan",
            "start_date": start_date,
            "end_date": end_date,
            "pacing": "Moderate",
            "interests": ["Culture", "Dining"],
            "budget_level": "Standard"
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate [short]"
        )

    @task(2)
    def generate_long_itinerary(self):
        """
        Task to generate a longer 7-day itinerary.
        This specifically targets the 30s P95 requirement for complex generations.
        test_id: app__performance__002
        ac_ids: REQ-N-003-AC-1
        """
        start_date = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = (datetime.date.today() + datetime.timedelta(days=97)).strftime("%Y-%m-%d")
        payload = {
            "destination": "Florence, Italy",
            "start_date": start_date,
            "end_date": end_date,
            "pacing": "Fast-paced",
            "interests": ["Art", "Architecture", "Gastronomy", "History"],
            "budget_level": "Luxury"
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate [long]"
        )

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Event handler to check performance statistics against defined thresholds when the test run stops.
    If any threshold is breached, it sets the process exit code to 1, causing the run to fail.
    """
    print("--- Performance Threshold Check ---")
    stats = environment.stats.total
    
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    did_fail = False

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio ({fail_ratio:.2%}) exceeded threshold ({FAIL_RATIO_THRESHOLD:.2%})")
        did_fail = True
    else:
        print(f"PASS: Failure ratio ({fail_ratio:.2%}) is within threshold ({FAIL_RATIO_THRESHOLD:.2%})")

    if p95_ms is not None and p95_ms > P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD:.2f} ms)")
        did_fail = True
    elif p95_ms is not None:
        print(f"PASS: P95 response time ({p95_ms:.2f} ms) is within threshold ({P95_MS_THRESHOLD:.2f} ms)")
    else:
        print("INFO: P95 response time could not be calculated (no requests made?).")

    if did_fail:
        environment.process_exit_code = 1
        print("--- Result: Performance thresholds FAILED ---")
    else:
        environment.process_exit_code = 0
        print("--- Result: Performance thresholds PASSED ---")
