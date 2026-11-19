"""
QA Persona v2 -- auto-generated tests
Service: app
Suite:   performance
Source:  test_strategy/plans/app__performance.json
Generated: 2024-07-12T13:41:20.900329Z
"""

import os
from locust import HttpUser, events, task, between

# Read configuration from environment variables
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
# P95 threshold from REQ-N-003: <= 30 seconds for total generation time
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "30000"))
# Error rate from REQ-N-002: < 1%
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class TargetUser(HttpUser):
    """
    User class that represents a user of the Travel Itinerary Generator Platform.
    This user will primarily generate itineraries and occasionally check the health endpoint.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    @task(3)
    def generate_itinerary(self):
        """Verify itinerary generation performance SLAs.

        test_id: app__performance__001
        target: POST /api/v1/itineraries/generate
        requirement_id: REQ-N-002, REQ-N-003
        ac_ids: REQ-N-002-AC-1, REQ-N-003-AC-1
        """
        payload = {
            "destination": "Tokyo",
            "start_date": "2025-01-01",
            "end_date": "2025-01-08",
            "pacing": "Moderate",
            "interests": ["Culture", "Tech", "Dining"]
        }
        self.client.post(
            "/api/v1/itineraries/generate",
            json=payload,
            name="/api/v1/itineraries/generate"
        )

    @task(1)
    def get_health(self):
        """Placeholder for System Availability Monitoring.

        test_id: app__performance__002
        target: GET /health
        requirement_id: REQ-N-001
        ac_ids: REQ-N-001-AC-1
        """
        self.client.get("/health", name="/health")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks if the performance thresholds were met during the test run.
    Fails the test run if P95 response time or failure ratio exceeds the defined limits.
    """
    if environment.stats.total.num_requests == 0:
        print("No requests were made. Skipping threshold checks.")
        return

    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds ---")
    print(f"Total Requests: {stats.num_requests}")
    print(f"P95 Response Time: {p95_ms:.2f} ms (Threshold: < {P95_MS_THRESHOLD} ms)")
    print(f"Failure Ratio: {fail_ratio:.4f} (Threshold: <= {FAIL_RATIO_THRESHOLD})")
    print(f"------------------------------\n")

    failed = False
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio {fail_ratio:.4f} exceeded threshold {FAIL_RATIO_THRESHOLD}")
        failed = True

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time {p95_ms:.2f} ms exceeded threshold {P95_MS_THRESHOLD} ms")
        failed = True

    if failed:
        environment.process_exit_code = 1
    else:
        print("PASS: All performance thresholds met.")
