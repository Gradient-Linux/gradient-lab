import os
import tempfile
import unittest
from unittest.mock import patch

from gradient_lab.config import (
    ALLOWED_GROUPS,
    ADMIN_GROUPS,
    API_PROXY_SERVICE,
    DEFAULT_URL,
    DB_URL,
    HUB_BIND_URL,
    HUB_IP,
    HUB_PORT,
    NOTEBOOK_DIR_TEMPLATE,
    SERVICE_DISPLAY_NAME,
    SERVICE_NAME,
    SERVER_EXTENSION_MODULE,
    SPAWNER_CLASS,
    apply_jupyterhub_config,
    build_jupyterhub_settings,
    notebook_dir_for,
)


class _ConfigLeaf:
    pass


class _FakeConfig:
    def __init__(self) -> None:
        self.Authenticator = _ConfigLeaf()
        self.JupyterHub = _ConfigLeaf()
        self.PAMAuthenticator = _ConfigLeaf()
        self.Spawner = _ConfigLeaf()
        self.ServerApp = _ConfigLeaf()


class ConfigTests(unittest.TestCase):
    def test_build_jupyterhub_settings_matches_thin_wrapper_boundary(self) -> None:
        settings = build_jupyterhub_settings()

        self.assertEqual(settings["authenticator_class"], "jupyterhub.auth.PAMAuthenticator")
        self.assertFalse(settings["allow_all"])
        self.assertTrue(settings["open_sessions"])
        self.assertEqual(settings["admin_groups"], set(ADMIN_GROUPS))
        self.assertEqual(settings["allowed_groups"], set(ALLOWED_GROUPS))
        self.assertEqual(settings["spawner_class"], SPAWNER_CLASS)
        self.assertEqual(settings["ip"], HUB_IP)
        self.assertEqual(settings["port"], HUB_PORT)
        self.assertEqual(settings["bind_url"], HUB_BIND_URL)
        self.assertEqual(settings["default_url"], DEFAULT_URL)
        self.assertEqual(settings["db_url"], DB_URL)
        self.assertEqual(settings["notebook_dir"], NOTEBOOK_DIR_TEMPLATE)
        self.assertEqual(settings["services"], [API_PROXY_SERVICE])
        self.assertEqual(settings["template_vars"]["gradient_lab_brand"], SERVICE_DISPLAY_NAME)
        self.assertEqual(settings["template_vars"]["gradient_lab_service_name"], SERVICE_NAME)
        self.assertEqual(settings["server_extensions"], {SERVER_EXTENSION_MODULE: True})

    def test_notebook_dir_for_uses_home_gradient_path(self) -> None:
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}, clear=False):
            expected = os.path.join(home, "gradient", "notebooks", "alice")

            self.assertEqual(notebook_dir_for("alice"), expected)

    def test_apply_jupyterhub_config_writes_expected_values(self) -> None:
        config = _FakeConfig()

        apply_jupyterhub_config(config)

        self.assertEqual(config.JupyterHub.authenticator_class, "jupyterhub.auth.PAMAuthenticator")
        self.assertFalse(config.Authenticator.allow_all)
        self.assertEqual(config.PAMAuthenticator.admin_groups, set(ADMIN_GROUPS))
        self.assertEqual(config.PAMAuthenticator.allowed_groups, set(ALLOWED_GROUPS))
        self.assertTrue(config.PAMAuthenticator.open_sessions)
        self.assertEqual(config.JupyterHub.spawner_class, SPAWNER_CLASS)
        self.assertEqual(config.JupyterHub.ip, HUB_IP)
        self.assertEqual(config.JupyterHub.port, HUB_PORT)
        self.assertEqual(config.JupyterHub.bind_url, HUB_BIND_URL)
        self.assertEqual(config.JupyterHub.default_url, DEFAULT_URL)
        self.assertFalse(config.JupyterHub.allow_named_servers)
        self.assertEqual(config.Spawner.notebook_dir, NOTEBOOK_DIR_TEMPLATE)
        self.assertEqual(config.Spawner.default_url, DEFAULT_URL)
        self.assertEqual(config.JupyterHub.db_url, DB_URL)
        self.assertEqual(config.JupyterHub.services, [API_PROXY_SERVICE])
        self.assertEqual(config.JupyterHub.template_vars["gradient_lab_brand"], SERVICE_DISPLAY_NAME)
        self.assertEqual(config.ServerApp.jpserver_extensions, {SERVER_EXTENSION_MODULE: True})


if __name__ == "__main__":
    unittest.main()
