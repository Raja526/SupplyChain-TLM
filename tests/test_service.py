import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

from src.supplychain_tlm.service import AgentRequestHandler, answer_payload, handle_json, release_payload, serve


class ServiceTests(unittest.TestCase):
    bundle = "examples/shipment_bundle.json"

    def test_answer_payload_is_tool_free(self):
        payload = answer_payload(self.bundle, "Can this shipment be released?")
        self.assertEqual(payload["mode"], "deterministic")
        self.assertEqual(payload["suggested_action"], "request_approval")

    def test_release_requires_approval(self):
        with TemporaryDirectory() as directory:
            result = release_payload(self.bundle, audit_path=str(Path(directory) / "audit.jsonl"))
            self.assertEqual(result["mode"], "review_only")

    def test_json_dispatch(self):
        payload = handle_json(json.dumps({"operation": "answer", "bundle": self.bundle, "request": "status"}))
        self.assertEqual(json.loads(payload)["mode"], "deterministic")

    def test_unknown_operation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "operation must be answer or release"):
            handle_json(json.dumps({"operation": "execute"}))

    def test_http_endpoint_dispatches_json(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), AgentRequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = json.dumps({"operation": "answer", "bundle": self.bundle, "request": "status"}).encode()
            request = Request(f"http://127.0.0.1:{server.server_port}/v1/request", data=body, headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read())
            self.assertEqual(payload["mode"], "deterministic")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_remote_binding_requires_explicit_opt_in(self):
        with self.assertRaisesRegex(ValueError, "remote binding"):
            serve("0.0.0.0", 0)

    def test_remote_binding_requires_token(self):
        with self.assertRaisesRegex(ValueError, "bearer token"):
            serve("0.0.0.0", 0, allow_remote=True)


if __name__ == "__main__":
    unittest.main()
