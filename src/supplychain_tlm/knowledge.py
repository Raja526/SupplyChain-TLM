"""Small local retrieval layer for SupplyChain-TLM development."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    text: str
    source: str = "local"


@dataclass(frozen=True)
class SearchResult:
    document: KnowledgeDocument
    score: float
    matched_terms: tuple[str, ...]


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) > 2}


class KnowledgeIndex:
    def __init__(self, documents: tuple[KnowledgeDocument, ...] = ()) -> None:
        self.documents = documents

    def add(self, document: KnowledgeDocument) -> None:
        self.documents = (*self.documents, document)

    def search(self, query: str, limit: int = 3) -> tuple[SearchResult, ...]:
        query_terms = _terms(query)
        results = []
        for document in self.documents:
            matched = tuple(sorted(query_terms & _terms(document.title + " " + document.text)))
            if matched:
                results.append(SearchResult(document, len(matched) / max(1, len(query_terms)), matched))
        return tuple(sorted(results, key=lambda item: (-item.score, item.document.document_id))[:limit])


DEFAULT_KNOWLEDGE = KnowledgeIndex((
    KnowledgeDocument("incoterms-2020", "Incoterms", "Incoterms describe responsibilities, costs, and risk transfer between seller and buyer. Confirm the agreed rule and named place against the commercial documents.", "internal-reference"),
    KnowledgeDocument("hs-codes", "HS codes", "HS classification supports customs declarations. Product classification should be checked against the goods description and the applicable tariff authority.", "internal-reference"),
    KnowledgeDocument("shipment-release", "Shipment release", "A release decision should compare commercial documents, transport documents, customs status, and required approvals before an enterprise action.", "internal-reference"),
))
