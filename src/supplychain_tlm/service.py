"""Small localhost service boundary for orchestration integrations."""

from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import os
from functools import partial
import threading
import time
from typing import Any

from .erp import DryRunERPClient, ERPToolAdapter
from .context import build_decision_context
from .ingest import load_bundle
from .model import RuleBasedSupplyChainTLM
from .tools import ApprovalGate, JsonlAuditLog, ToolPolicy
from .workflow import ReleaseWorkflow


class ServiceMetrics:
    def __init__(self) -> None:
        self.started_at = time.time()
        self.requests_total = 0
        self.responses_2xx = 0
        self.responses_4xx = 0
        self._lock = threading.Lock()

    def record(self, status: int) -> None:
        with self._lock:
            self.requests_total += 1
            if 200 <= status < 300:
                self.responses_2xx += 1
            elif 400 <= status < 500:
                self.responses_4xx += 1

    def prometheus(self) -> bytes:
        with self._lock:
            body = (
                f"supplychain_requests_total {self.requests_total}\n"
                f"supplychain_responses_2xx_total {self.responses_2xx}\n"
                f"supplychain_responses_4xx_total {self.responses_4xx}\n"
                f"supplychain_uptime_seconds {max(0.0, time.time() - self.started_at):.3f}\n"
            )
        return body.encode("utf-8")


def answer_payload(bundle_path: str, request: str) -> dict[str, Any]:
    """Return a deterministic answer payload; no external tools are called."""
    context = build_decision_context(request, load_bundle(bundle_path))
    response = RuleBasedSupplyChainTLM().answer(context)
    return {
        "mode": "deterministic",
        "answer": response.answer,
        "confidence": response.confidence,
        "suggested_action": response.suggested_action,
        "references": list(response.references),
    }


def release_payload(bundle_path: str, approver: str | None = None, audit_path: str = "audit/service.jsonl") -> dict[str, Any]:
    """Prepare or execute a safe dry-run release through the approval gate."""
    audit = JsonlAuditLog(audit_path)
    erp = ERPToolAdapter(DryRunERPClient())
    policy = ToolPolicy(frozenset({erp.name}), frozenset({"release_shipment"}), "procurement_manager")
    workflow = ReleaseWorkflow(ApprovalGate(audit=audit, policy=policy), erp)
    bundle = load_bundle(bundle_path)
    if not approver:
        result = workflow.prepare(bundle)
        return {"mode": "review_only", "validation_passed": result.plan.validation_passed, "proposal": asdict(result.plan.proposals[0]), "audit": audit_path}
    result = workflow.approve_and_execute(bundle, approver)
    return {"mode": "approved_dry_run" if result.tool_result else "blocked", "validation_passed": result.plan.validation_passed, "tool_result": result.tool_result, "audit": audit_path}


def handle_json(payload: str) -> str:
    """Handle one newline-delimited JSON request for embedding in a service."""
    request = json.loads(payload)
    if request.get("operation") == "answer":
        result = answer_payload(str(request["bundle"]), str(request["request"]))
    elif request.get("operation") == "release":
        result = release_payload(str(request["bundle"]), request.get("approver"), str(request.get("audit", "audit/service.jsonl")))
    else:
        raise ValueError("operation must be answer or release")
    return json.dumps(result, sort_keys=True)


class AgentRequestHandler(BaseHTTPRequestHandler):
    """Minimal POST /v1/request transport for localhost orchestration."""

    def __init__(self, request: Any, client_address: Any, server: Any, auth_token: str | None = None) -> None:
        self.auth_token = auth_token
        self.metrics = getattr(server, "service_metrics", ServiceMetrics())
        super().__init__(request, client_address, server)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.auth_token and self.headers.get("Authorization") != f"Bearer {self.auth_token}":
            self.metrics.record(401)
            self.send_error(401, "authorization required")
            return
        if self.path != "/v1/request":
            self.metrics.record(404)
            self.send_error(404, "use POST /v1/request")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 1_000_000:
                raise ValueError("request body must be between 1 byte and 1 MB")
            result = handle_json(self.rfile.read(size).decode("utf-8"))
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            self.metrics.record(400)
            self.send_error(400, str(error))
            return
        body = result.encode("utf-8")
        self.send_response(200)
        self.metrics.record(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/metrics":
            if self.auth_token and self.headers.get("Authorization") != f"Bearer {self.auth_token}":
                self.metrics.record(401)
                self.send_error(401, "authorization required")
                return
            self.send_response(200)
            self.metrics.record(200)
            body = self.metrics.prometheus()
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path != "/healthz":
            self.metrics.record(404)
            self.send_error(404, "use GET /healthz")
            return
        if self.auth_token and self.headers.get("Authorization") != f"Bearer {self.auth_token}":
            self.metrics.record(401)
            self.send_error(401, "authorization required")
            return
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.metrics.record(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8080, *, allow_remote: bool = False, token: str | None = None) -> None:
    """Serve the restricted JSON endpoint; localhost is the safe default."""
    if not allow_remote and host not in {"localhost", "127.0.0.1", "::1"}:
        try:
            is_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_loopback = False
        if not is_loopback:
            raise ValueError("remote binding requires allow_remote=True")
    if allow_remote and not token:
        raise ValueError("remote binding requires a bearer token")
    handler = partial(AgentRequestHandler, auth_token=token)
    server = ThreadingHTTPServer((host, port), handler)
    server.service_metrics = ServiceMetrics()
    print(f"supplychain service listening on http://{host}:{port}/v1/request")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local SupplyChain-TLM JSON service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--allow-remote", action="store_true", help="allow binding beyond localhost")
    parser.add_argument("--token", default=os.environ.get("SUPPLYCHAIN_SERVICE_TOKEN"), help="bearer token; required with --allow-remote")
    args = parser.parse_args(argv)
    serve(args.host, args.port, allow_remote=args.allow_remote, token=args.token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
