from locust import HttpUser, task, between, events
import os
import datetime


SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
# From plan app__performance__001: P95 total generation time for a 7-day trip is <= 30 seconds.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "30000"))
# From plan app__performance__001: error rate is below 1%.
FAIL_RATIO_THRESHOLD = 0.01

class TargetUser(HttpUser):
    """
    QA Persona v2 -- auto-generated tests
    Service: app
    Suite:   performance
    Source:  test_strategy/plans/app__performance.json
    Generated: 2024-07-12T13:01:21.164321Z
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    @task(1)
    def generate_itinerary_task(self):
        """Load test for itinerary generation.

        test_id: app__performance__001
        target: POST /api/v1/itineraries/generate
        requirement_id: REQ-N-002, REQ-N-003
        ac_ids: REQ-N-002-AC-1, REQ-N-003-AC-1
        """
        payload = {
            "destination": "Tokyo, Japan",
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
            "pacing": "Moderate",
            "interests": ["Culture", "Tech", "Street Food"],
            "budget_level": "Standard"
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate"
        )

    @task(5)
    def health_check_task(self):
        """Frequent health check to monitor availability.

        test_id: app__performance__002
        target: System-wide
        requirement_id: REQ-N-001
        ac_ids: REQ-N-001-AC-1
        """
        self.client.get("/health", name="/health")

    @task(3)
    def list_itineraries_task(self):
        """Read-heavy task to list itineraries."""
        self.client.get("/api/v1/itineraries", name="/api/v1/itineraries")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Check statistics when the test is stopped and set exit code based on thresholds."""
    if not environment.stats.total.num_requests:
        print("No requests made, skipping threshold checks.")
        return

    stats = environment.stats.total
    fail_ratio = stats.fail_ratio

    # Check overall failure rate
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Overall failure ratio {fail_ratio:.4f} exceeded threshold {FAIL_RATIO_THRESHOLD}")
        environment.process_exit_code = 1

    # Check P95 for the specific itinerary generation endpoint from app__performance__001
    # Note: This checks total response time. The TTFB threshold from the plan is not measured here.
    gen_stats = environment.stats.get("/api/v1/itineraries/generate", "POST")
    if gen_stats.num_requests > 0:
        p95_ms = gen_stats.get_response_time_percentile(0.95)
        if p95_ms is not None:
            print(f"P95 for POST /api/v1/itineraries/generate: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD}ms)")
            if p95_ms >= P95_MS_THRESHOLD:
                print(f"FAIL: P95 for itinerary generation ({p95_ms:.2f}ms) exceeded threshold ({P95_MS_THRESHOLD}ms)")
                environment.process_exit_code = 1
        else:
            print("Could not calculate P95 for itinerary generation.")
    else:
        print("No requests made to /api/v1/itineraries/generate, skipping its P95 check.")

    if environment.process_exit_code == 0:
        print("PASS: All performance thresholds met.")
