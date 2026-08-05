"""Container healthcheck for the authenticated local service."""

from __future__ import annotations

import os
from urllib.request import Request, urlopen


token = os.environ.get("SUPPLYCHAIN_SERVICE_TOKEN", "")
request = Request("http://127.0.0.1:8080/healthz", headers={"Authorization": f"Bearer {token}"})
with urlopen(request, timeout=3) as response:
    if response.status != 200:
        raise SystemExit(1)
