"""Authenticated JSON-over-HTTP connector primitives for vendor adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class JSONHTTPClient:
    base_url: str
    token: str
    timeout_seconds: float = 30.0
    max_attempts: int = 1
    retry_backoff_seconds: float = 0.2

    def __post_init__(self) -> None:
        if not self.token.strip():
            raise ValueError("connector token cannot be empty")
        if not self.base_url.startswith("https://") and not self.base_url.startswith(("http://localhost", "http://127.0.0.1", "http://[::1]")):
            raise ValueError("connector base_url must use HTTPS except for localhost tests")
        if self.timeout_seconds <= 0:
            raise ValueError("connector timeout must be positive")
        if self.max_attempts < 1 or self.retry_backoff_seconds < 0:
            raise ValueError("connector retry settings are invalid")

    def call(self, path: str, payload: dict[str, object], idempotency_key: str | None = None) -> str:
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        for attempt in range(self.max_attempts):
            request = Request(url, data=body, method="POST", headers=headers)
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as error:
                if error.code < 500 or attempt + 1 == self.max_attempts:
                    raise RuntimeError(f"connector HTTP error: {error.code}") from error
            except URLError as error:
                if attempt + 1 == self.max_attempts:
                    raise RuntimeError(f"connector network error: {error.reason}") from error
            time.sleep(self.retry_backoff_seconds * (attempt + 1))
        if not isinstance(data, dict) or "result" not in data:
            raise RuntimeError("connector response must contain a result")
        return str(data["result"])


@dataclass(frozen=True)
class SAPHTTPConnector:
    client: JSONHTTPClient

    def release_shipment(self, shipment_id: str, po_number: str) -> str:
        return self.client.call("sap/release", {"shipment_id": shipment_id, "po_number": po_number})

    def purchase_order_status(self, po_number: str) -> str:
        return self.client.call("sap/purchase-order-status", {"po_number": po_number})


@dataclass(frozen=True)
class OracleHTTPConnector:
    client: JSONHTTPClient

    def release_shipment(self, shipment_id: str, po_number: str) -> str:
        return self.client.call("oracle/release", {"shipment_id": shipment_id, "po_number": po_number})

    def purchase_order_status(self, po_number: str) -> str:
        return self.client.call("oracle/purchase-order-status", {"po_number": po_number})


@dataclass(frozen=True)
class WMSHTTPConnector:
    client: JSONHTTPClient

    def reserve_inventory(self, shipment_id: str, sku: str, quantity: float) -> str:
        return self.client.call("wms/reserve", {"shipment_id": shipment_id, "sku": sku, "quantity": quantity})

    def record_goods_receipt(self, shipment_id: str) -> str:
        return self.client.call("wms/goods-receipt", {"shipment_id": shipment_id})
