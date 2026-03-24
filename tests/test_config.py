import unittest

from gradient_lab.config import (
    ALLOWED_GROUPS,
    ADMIN_GROUPS,
    API_PROXY_SERVICE,
    DB_URL,
    HUB_IP,
    HUB_PORT,
    NOTEBOOK_DIR_TEMPLATE,
    SPAWNER_CLASS,
    apply_jupyterhub_config,
    build_jupyterhub_settings,
    notebook_dir_for,
)


class _ConfigLeaf:
    pass


class _FakeConfig:
    def __init__(self) -> None:
        self.JupyterHub = _ConfigLeaf()
        self.PAMAuthenticator = _ConfigLeaf()
        self.Spawner = _ConfigLeaf()


class ConfigTests(unittest.TestCase):
    def test_build_jupyterhub_settings_matches_thin_wrapper_boundary(self) -> None:
        settings = build_jupyterhub_settings()

        self.assertEqual(settings["authenticator_class"], "jupyterhub.auth.PAMAuthenticator")
        self.assertEqual(settings["admin_groups"], set(ADMIN_GROUPS))
        self.assertEqual(settings["allowed_groups"], set(ALLOWED_GROUPS))
        self.assertEqual(settings["spawner_class"], SPAWNER_CLASS)
        self.assertEqual(settings["ip"], HUB_IP)
        self.assertEqual(settings["port"], HUB_PORT)
        self.assertEqual(settings["db_url"], DB_URL)
        self.assertEqual(settings["notebook_dir"], NOTEBOOK_DIR_TEMPLATE)
        self.assertEqual(settings["services"], [API_PROXY_SERVICE])

    def test_notebook_dir_for_uses_fixed_gradient_path(self) -> None:
        self.assertEqual(notebook_dir_for("alice"), "/gradient/notebooks/alice")

    def test_apply_jupyterhub_config_writes_expected_values(self) -> None:
        config = _FakeConfig()

        apply_jupyterhub_config(config)

        self.assertEqual(config.JupyterHub.authenticator_class, "jupyterhub.auth.PAMAuthenticator")
        self.assertEqual(config.PAMAuthenticator.admin_groups, set(ADMIN_GROUPS))
        self.assertEqual(config.PAMAuthenticator.allowed_groups, set(ALLOWED_GROUPS))
        self.assertEqual(config.JupyterHub.spawner_class, SPAWNER_CLASS)
        self.assertEqual(config.JupyterHub.ip, HUB_IP)
        self.assertEqual(config.JupyterHub.port, HUB_PORT)
        self.assertEqual(config.Spawner.notebook_dir, NOTEBOOK_DIR_TEMPLATE)
        self.assertEqual(config.JupyterHub.db_url, DB_URL)
        self.assertEqual(config.JupyterHub.services, [API_PROXY_SERVICE])


if __name__ == "__main__":
    unittest.main()

