"""Small dependency-free capability router used by the initial scaffold."""

from __future__ import annotations

from dataclasses import dataclass
import re
import sys


@dataclass(frozen=True)
class Route:
    capability: str
    confidence: float
    reasons: tuple[str, ...]


_KEYWORDS = {
    "financial": ("invoice", "purchase order", "payment", "currency", "tax", "letter of credit"),
    "shipping": ("shipment", "bill of lading", "bol", "air waybill", "container", "vessel", "voyage", "carrier"),
    "customs": ("hs code", "tariff", "duty", "customs", "incoterm", "certificate"),
    "warehouse": ("goods receipt", "inventory", "bin", "pick list", "delivery note", "warehouse"),
    "compliance": ("dangerous goods", "sanction", "export control", "restriction", "insurance"),
}


def route_request(text: str) -> tuple[Route, ...]:
    """Return ranked business-capability routes for a request.

    This is deliberately deterministic. A future model router can implement the
    same contract while retaining the planner/tool safety boundary.
    """
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    routes: list[Route] = []
    for capability, keywords in _KEYWORDS.items():
        reasons = tuple(keyword for keyword in keywords if keyword in normalized)
        if reasons:
            confidence = min(0.99, 0.55 + 0.1 * len(reasons))
            routes.append(Route(capability, confidence, reasons))
    return tuple(sorted(routes, key=lambda item: (-item.confidence, item.capability)))


def main() -> int:
    text = " ".join(sys.argv[1:]) or "Can this shipment be released if the invoice and HS code disagree?"
    routes = route_request(text)
    print(f"request: {text}")
    if not routes:
        print("route: general_supply_chain")
        return 0
    for route in routes:
        print(f"route: {route.capability} confidence={route.confidence:.2f} reasons={','.join(route.reasons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
