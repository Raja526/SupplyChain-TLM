import unittest
from pathlib import Path


class DeploymentTests(unittest.TestCase):
    def test_container_requires_authenticated_remote_service(self):
        dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
        self.assertIn("--allow-remote", dockerfile)
        self.assertIn("USER agent", dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)

    def test_dockerignore_excludes_weights_and_audit_data(self):
        ignored = Path(".dockerignore").read_text(encoding="utf-8")
        self.assertIn("*.safetensors", ignored)
        self.assertIn("audit", ignored)

    def test_compose_requires_service_token(self):
        compose = Path("compose.yaml").read_text(encoding="utf-8")
        self.assertIn("SUPPLYCHAIN_SERVICE_TOKEN", compose)
        self.assertIn("restart: unless-stopped", compose)


if __name__ == "__main__":
    unittest.main()
