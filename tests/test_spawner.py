import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gradient_lab.spawner as spawner_module
from gradient_lab.spawner import (
    GradientSpawner,
    build_gradient_env,
    fetch_group_quota,
    fetch_team_status,
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
    def test_fetch_team_status_reads_group_quota_and_role(self) -> None:
        runner = FakeRunner(
            [FakeResult(stdout='{"group":"gradient-developer","role":"gradient-developer","quota":{"cpu_cores":4,"memory_gb":16}}')]
        )

        status = fetch_team_status("alice", runner=runner)

        self.assertEqual(status["group"], "gradient-developer")
        self.assertEqual(status["role"], "gradient-developer")
        self.assertEqual(status["quota"], {"cpu_cores": 4, "memory_gb": 16})
        self.assertEqual(runner.calls[0], ["concave", "team", "status", "--user", "alice", "--json"])

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
            role="gradient-developer",
            notebook_dir="/tmp/gradient/notebooks/alice",
            quota={"cpu_cores": 4, "memory_gb": 16, "gpu_count": 1},
        )

        self.assertEqual(env["GRADIENT_GROUP"], "gradient-developer")
        self.assertEqual(env["GRADIENT_ROLE"], "gradient-developer")
        self.assertEqual(env["GRADIENT_NOTEBOOK_DIR"], "/tmp/gradient/notebooks/alice")
        self.assertEqual(env["GRADIENT_CGROUP_SLICE"], "gradient-gradient-developer.slice")
        self.assertEqual(env["GRADIENT_CPU_LIMIT"], "4")
        self.assertEqual(env["GRADIENT_MEM_LIMIT"], "16")
        self.assertEqual(env["GRADIENT_QUOTA_CPU_CORES"], "4")
        self.assertEqual(env["GRADIENT_QUOTA_MEMORY_GB"], "16")
        self.assertEqual(env["GRADIENT_QUOTA_GPU_COUNT"], "1")

    def test_spawner_user_env_merges_quota_metadata_and_creates_notebook_dir(self) -> None:
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}, clear=False):
            runner = FakeRunner(
                [
                    FakeResult(
                        stdout='{"group":"gradient-developer","role":"gradient-developer","quota":{"cpu_cores":2,"memory_gb":8,"gpu_count":1}}'
                    )
                ]
            )
            spawner = GradientSpawner(runner=runner)
            spawner.user = SimpleNamespace(name="alice")

            env = spawner.user_env({"PATH": "/usr/bin"})
            expected_notebook_dir = str(Path(home) / "gradient" / "notebooks" / "alice")

            self.assertEqual(env["GRADIENT_GROUP"], "gradient-developer")
            self.assertEqual(env["GRADIENT_ROLE"], "gradient-developer")
            self.assertEqual(env["GRADIENT_NOTEBOOK_DIR"], expected_notebook_dir)
            self.assertEqual(env["GRADIENT_CPU_LIMIT"], "2")
            self.assertEqual(env["GRADIENT_MEM_LIMIT"], "8")
            self.assertEqual(env["GRADIENT_QUOTA_GPU_COUNT"], "1")
            self.assertTrue(Path(expected_notebook_dir).exists())
            self.assertEqual(
                runner.calls[0],
                ["concave", "team", "status", "--user", "alice", "--json"],
            )

    def test_spawner_preexec_invokes_best_effort_systemd_scope(self) -> None:
        runner = FakeRunner([FakeResult(stdout='{"group":"gradient-developer","quota":{"cpu_cores":2}}')])
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
            runner.calls,
            [
                ["concave", "team", "status", "--user", "alice", "--json"],
                ["systemd-run", "--scope", "--quiet", "--slice", "gradient-gradient-developer.slice", "true"],
            ],
        )

    def test_spawner_user_env_ignores_malformed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}, clear=False):
            runner = FakeRunner([FakeResult(stdout="not-json")])
            spawner = GradientSpawner(runner=runner)
            spawner.user = SimpleNamespace(name="alice")

            env = spawner.user_env({"PATH": "/usr/bin"})
            expected_notebook_dir = str(Path(home) / "gradient" / "notebooks" / "alice")

            self.assertEqual(env["PATH"], "/usr/bin")
            self.assertEqual(env["GRADIENT_NOTEBOOK_DIR"], expected_notebook_dir)
            self.assertTrue(Path(expected_notebook_dir).exists())


if __name__ == "__main__":
    unittest.main()
