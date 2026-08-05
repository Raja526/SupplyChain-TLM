"""Typed, model-independent supply-chain document structures."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentHeader:
    document_id: str
    document_type: str
    supplier: str = ""
    buyer: str = ""


@dataclass(frozen=True)
class LineItem:
    sku: str
    description: str = ""
    quantity: float = 0.0
    unit_price: float | None = None


@dataclass(frozen=True)
class Invoice:
    header: DocumentHeader
    po_number: str
    currency: str
    total_amount: float
    lines: tuple[LineItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PurchaseOrder:
    header: DocumentHeader
    po_number: str
    currency: str
    total_amount: float
    lines: tuple[LineItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PackingList:
    header: DocumentHeader
    shipment_id: str
    lines: tuple[LineItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BillOfLading:
    header: DocumentHeader
    shipment_id: str
    container_numbers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)
