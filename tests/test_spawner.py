import unittest
from types import SimpleNamespace
from unittest.mock import patch

import gradient_lab.spawner as spawner_module
from gradient_lab.spawner import (
    GradientSpawner,
    build_gradient_env,
    fetch_group_quota,
    fetch_user_group,
)


class FakeResult:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


class FakeRunner:
    def __init__(self, responses: list[FakeResult]) -> None:
        self.responses = responses
        self.calls: list[list[str]] = []

    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        if self.responses:
            return self.responses.pop(0)
        return FakeResult(returncode=1)


class SpawnerTests(unittest.TestCase):
    def test_fetch_user_group_reads_group_from_concave_payload(self) -> None:
        runner = FakeRunner([FakeResult(stdout='{"group":"gradient-developer"}')])

        self.assertEqual(fetch_user_group("alice", runner=runner), "gradient-developer")
        self.assertEqual(runner.calls[0], ["concave", "team", "status", "--user", "alice", "--json"])

    def test_fetch_group_quota_reads_quota_from_concave_payload(self) -> None:
        runner = FakeRunner([FakeResult(stdout='{"quota":{"cpu_cores":4,"memory_gb":16}}')])

        quota = fetch_group_quota("gradient-developer", runner=runner)

        self.assertEqual(quota, {"cpu_cores": 4, "memory_gb": 16})
        self.assertEqual(runner.calls[0], ["concave", "team", "status", "gradient-developer", "--json"])

    def test_build_gradient_env_adds_session_metadata(self) -> None:
        env = build_gradient_env(
            {"PATH": "/usr/bin"},
            group="gradient-developer",
            quota={"cpu_cores": 4, "memory_gb": 16},
        )

        self.assertEqual(env["GRADIENT_GROUP"], "gradient-developer")
        self.assertEqual(env["GRADIENT_CPU_LIMIT"], "4")
        self.assertEqual(env["GRADIENT_MEM_LIMIT"], "16")

    def test_spawner_user_env_merges_quota_metadata(self) -> None:
        runner = FakeRunner(
            [
                FakeResult(stdout='{"group":"gradient-developer"}'),
                FakeResult(stdout='{"quota":{"cpu_cores":2,"memory_gb":8}}'),
            ]
        )
        spawner = GradientSpawner(runner=runner)
        spawner.user = SimpleNamespace(name="alice")

        env = spawner.user_env({"PATH": "/usr/bin"})

        self.assertEqual(env["GRADIENT_GROUP"], "gradient-developer")
        self.assertEqual(env["GRADIENT_CPU_LIMIT"], "2")
        self.assertEqual(env["GRADIENT_MEM_LIMIT"], "8")

    def test_spawner_preexec_invokes_best_effort_systemd_scope(self) -> None:
        runner = FakeRunner([FakeResult(stdout='{"group":"gradient-developer"}')])
        spawner = GradientSpawner(runner=runner)
        spawner.user = SimpleNamespace(name="alice")

        executed = []

        def parent_preexec():
            executed.append("parent")

        with patch.object(spawner_module.LocalProcessSpawner, "make_preexec_fn", lambda self, name: parent_preexec):
            preexec = spawner.make_preexec_fn("alice")
            preexec()

        self.assertEqual(executed, ["parent"])
        self.assertEqual(
            runner.calls[-1],
            [
                "systemd-run",
                "--scope",
                "--slice",
                "gradient-gradient-developer.slice",
                "--uid",
                "alice",
                "--",
            ],
        )

    def test_spawner_user_env_ignores_malformed_payload(self) -> None:
        runner = FakeRunner([FakeResult(stdout="not-json")])
        spawner = GradientSpawner(runner=runner)
        spawner.user = SimpleNamespace(name="alice")

        env = spawner.user_env({"PATH": "/usr/bin"})

        self.assertEqual(env, {"PATH": "/usr/bin"})


if __name__ == "__main__":
    unittest.main()
