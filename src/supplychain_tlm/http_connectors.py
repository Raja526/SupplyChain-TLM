"""Authenticated JSON-over-HTTP connector primitives for vendor adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class JSONHTTPClient:
    base_url: str
    token: str
    timeout_seconds: float = 30.0

    def call(self, path: str, payload: dict[str, object]) -> str:
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        request = Request(url, data=body, method="POST", headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise RuntimeError(f"connector HTTP error: {error.code}") from error
        except URLError as error:
            raise RuntimeError(f"connector network error: {error.reason}") from error
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
