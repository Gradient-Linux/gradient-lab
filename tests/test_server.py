import unittest

from gradient_lab.permissions import visible_actions
from gradient_lab.server import build_status_payload


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self.body.encode("utf-8")


class ServerTests(unittest.TestCase):
    def test_visible_actions_hides_operator_only_actions_for_developers(self) -> None:
        actions = visible_actions("gradient-developer")
        labels = [action["label"] for action in actions]

        self.assertIn("Refresh status", labels)
        self.assertIn("Sync baseline", labels)
        self.assertNotIn("Reconcile cgroup quota", labels)
        self.assertNotIn("Provision user", labels)

    def test_build_status_payload_combines_quota_and_resolver_data(self) -> None:
        env = {
            "GRADIENT_GROUP": "gradient-developer",
            "GRADIENT_ROLE": "gradient-developer",
            "GRADIENT_CPU_LIMIT": "2",
            "GRADIENT_MEM_LIMIT": "8",
            "GRADIENT_QUOTA_GPU_COUNT": "1",
        }

        payload = build_status_payload(env, opener=lambda url, timeout=2.0: FakeResponse('{"available": true, "message": "ready"}'))

        self.assertEqual(payload["group"], "gradient-developer")
        self.assertEqual(payload["role"], "gradient-developer")
        self.assertEqual(payload["quota"]["cpu_cores"], 2)
        self.assertEqual(payload["quota"]["memory_gb"], 8)
        self.assertEqual(payload["quota"]["gpu_count"], 1)
        self.assertTrue(payload["resolver"]["available"])
        self.assertEqual(payload["resolver"]["message"], "ready")
        self.assertGreaterEqual(len(payload["actions"]), 2)


if __name__ == "__main__":
    unittest.main()
