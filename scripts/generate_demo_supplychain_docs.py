"""Generate synthetic, non-production supply-chain document images for OCR tests."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


OUTPUT = Path.home() / "Downloads" / "llm-in-c" / "supplychain-test-docs" / "filled_demo"
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)

DOCUMENTS = {
    "invoice_demo.png": (
        "COMMERCIAL INVOICE",
        "Invoice Number: INV-100\nDate: 2026-08-06\nPO Number: PO-100\nCurrency: USD\n\nSKU: SKU-1\nDescription: Demo Widget\nQuantity: 10\nUnit Price: 100.00\nTotal Payable: 1000.00\n\nShipment ID: SHIP-100",
    ),
    "purchase_order_demo.png": (
        "PURCHASE ORDER",
        "PO Number: PO-100\nDate: 2026-08-01\nCurrency: USD\n\nSKU: SKU-1\nDescription: Demo Widget\nQuantity: 10\nUnit Price: 100.00\nTotal PO Amount: 1000.00",
    ),
    "packing_list_demo.png": (
        "PACKING LIST",
        "Packing List Number: PL-100\nShipment ID: SHIP-100\nPO Number: PO-100\n\nSKU: SKU-1\nDescription: Demo Widget\nQuantity: 10\nPackages: 1",
    ),
    "bill_of_lading_demo.png": (
        "BILL OF LADING",
        "B/L Number: BL-100\nShipment ID: SHIP-100\nPO Number: PO-100\nContainer Number: MSCU1234567\n\nSKU: SKU-1\nDescription: Demo Widget\nQuantity: 10",
    ),
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, (title, body) in DOCUMENTS.items():
        image = Image.new("RGB", (1800, 2200), "white")
        draw = ImageDraw.Draw(image)
        draw.text((100, 100), title, fill="black", font=TITLE)
        draw.line((100, 190, 1700, 190), fill="black", width=3)
        draw.multiline_text((100, 260), body, fill="black", font=FONT, spacing=24)
        image.save(OUTPUT / filename)
    print(f"generated {len(DOCUMENTS)} files in {OUTPUT}")


if __name__ == "__main__":
    main()
