import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.supplychain_tlm.service import AgentRequestHandler, answer_payload, decision_payload, handle_json, release_payload, serve


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

    def test_tinyagentos_decision_dispatch(self):
        payload = decision_payload(self.bundle, "Can this shipment be released?", approved=False)
        self.assertEqual(payload["mode"], "tinyagentos_pipeline")
        self.assertEqual(payload["answer"]["suggested_action"], "refuse_action")
        self.assertEqual(payload["plan"]["proposals"][0]["status"], "proposed")

    def test_unknown_operation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "operation must be answer, decision, or release"):
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

    def test_authenticated_http_endpoint(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(AgentRequestHandler, auth_token="secret"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        body = json.dumps({"operation": "answer", "bundle": self.bundle, "request": "status"}).encode()
        try:
            unauthenticated = Request(f"http://127.0.0.1:{server.server_port}/v1/request", data=body)
            with self.assertRaises(HTTPError) as error:
                urlopen(unauthenticated, timeout=5)
            self.assertEqual(error.exception.code, 401)
            authenticated = Request(f"http://127.0.0.1:{server.server_port}/v1/request", data=body, headers={"Authorization": "Bearer secret"})
            with urlopen(authenticated, timeout=5) as response:
                self.assertEqual(json.loads(response.read())["mode"], "deterministic")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_health_endpoint(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), AgentRequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/healthz", timeout=5) as response:
                self.assertEqual(json.loads(response.read())["status"], "ok")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_metrics_endpoint_reports_requests(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), AgentRequestHandler)
        server.service_metrics = __import__("src.supplychain_tlm.service", fromlist=["ServiceMetrics"]).ServiceMetrics()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/healthz", timeout=5):
                pass
            with urlopen(f"http://127.0.0.1:{server.server_port}/metrics", timeout=5) as response:
                metrics = response.read().decode()
            self.assertIn("supplychain_requests_total 2", metrics)
            self.assertIn("supplychain_responses_2xx_total 2", metrics)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


if __name__ == "__main__":
    unittest.main()
