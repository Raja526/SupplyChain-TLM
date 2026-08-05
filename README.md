# SupplyChain-TLM

An experimental CPU-oriented foundation for an autonomous supply-chain agent.

The long-term system is designed around one shared SupplyChain-TLM with modular business-domain adapters and a separate planner/tool layer:

```text
Documents → extraction → validation → SupplyChain-TLM → planner → approved enterprise action
                                      ├─ Financial
                                      ├─ Shipping
                                      ├─ Customs
                                      ├─ Warehouse
                                      └─ Compliance
```

## Initial scope

This repository begins with the architecture boundary and a dependency-free domain router prototype. It does not yet train or ship a language model, connect to SAP, or execute external actions.

The design intentionally separates:

- model understanding and explanation;
- deterministic business validation;
- planning and approvals;
- enterprise tool execution.

## Run the prototype

```bash
python3 -m src.supplychain_tlm.router
python3 -m unittest discover -s tests -v
```

The prototype classifies a request into business capabilities. It is a routing scaffold, not an ML model.

## Validate a document bundle

The first deterministic validation layer compares invoice, purchase order, packing list, and bill of lading data:

```bash
python3 -m src.supplychain_tlm.validation
```

Validation failures are returned as typed issue codes such as `PO_NUMBER_MISMATCH`, `CURRENCY_MISMATCH`, and `MISSING_CONTAINER`. These checks are intentionally independent of the language model and should run before a planner proposes an enterprise action.

## Load extracted JSON

The ingestion boundary accepts structured output from a future OCR or document-extraction system:

```bash
python3 -m src.supplychain_tlm.ingest examples/shipment_bundle.json
```

The JSON loader performs schema conversion only. It does not trust the extracted data; the resulting typed documents still pass through deterministic validation.

## Extraction and planning boundaries

`src/supplychain_tlm/extraction.py` defines an OCR provider interface and a plain-text development provider. An OCR engine can be integrated later without changing the document schemas.

`src/supplychain_tlm/planner.py` creates approval-gated action proposals. It never calls an ERP, sends email, or mutates external state. Invalid document bundles produce a `blocked` proposal.

`src/supplychain_tlm/tools.py` defines the next boundary: tools require an explicit approval record, an idempotency key, and audit events. `FakeERPTool` is only a test double; it does not connect to a real ERP.

Tool policies can restrict allowed tool names, operations, and approver roles. Completed idempotency keys cannot be executed again.

`JsonlAuditLog` provides append-only audit persistence without a database dependency. It can be reloaded after a process restart for inspection or later migration into an enterprise audit store.

## Run the workflow pieces together

`ReleaseWorkflow` coordinates the local path from a typed bundle to a guarded fake ERP call. Invalid bundles stop before approval; valid bundles require an approver and then execute the test double.

## Run the command-line workflow

Review a proposal without executing a tool:

```bash
python3 -m src.supplychain_tlm.cli examples/shipment_bundle.json
```

Explicitly approve the local fake ERP action:

```bash
python3 -m src.supplychain_tlm.cli examples/shipment_bundle.json \
  --approve-as procurement_manager \
  --audit audit/workflow.jsonl
```

The CLI uses a fake ERP connector for development. It does not modify SAP, Oracle, email, or any external system.

## Baseline OCR-text extraction

For development fixtures, OCR text can be classified and scanned for common identifiers:

```python
from src.supplychain_tlm.text_extract import extract_fields

result = extract_fields("Bill of Lading\\nShipment ID: SHIP-100\\nContainer Number: MSCU1234567")
print(result.document_type, result.fields)
```

This baseline uses deterministic patterns. It is not a replacement for layout-aware OCR, table extraction, confidence calibration, or human review.

Each extracted field carries a confidence value. Unknown document types, warnings, or low-confidence fields set `needs_human_review=True` and should stop automatic progression.

## Local knowledge retrieval

The initial `KnowledgeIndex` provides deterministic local retrieval for SupplyChain-TLM development:

```python
from src.supplychain_tlm.knowledge import DEFAULT_KNOWLEDGE
results = DEFAULT_KNOWLEDGE.search("Which HS code and tariff checks are needed?")
```

This is a small lexical baseline. A production RAG layer should add versioned sources, embeddings or hybrid search, access control, citations, and freshness policies.

The release planner now attaches retrieved reference IDs to each `Plan`. These references are advisory evidence; validation remains the hard gate and the planner does not treat retrieved text as authorization.

## Domain adapters

`src/supplychain_tlm/domains.py` provides shared-fact adapters for Financial, Shipping, Customs, Warehouse, and Compliance capabilities. They are modular context providers, not separate models, and can feed the same SupplyChain-TLM.

`build_decision_context()` combines the request route, selected domain facts, retrieved references, and deterministic validation results into one model-ready context object.

Inspect the serialized context with:

```bash
python3 -m src.supplychain_tlm.context_cli \
  examples/shipment_bundle.json \
  "Can this shipment be released?"
```

## Roadmap

1. Document schemas and deterministic validation.
2. OCR/document-ingestion adapters.
3. Retrieval over logistics knowledge and rules.
4. Compact CPU SupplyChain-TLM training/evaluation pipeline.
5. Domain adapters for financial, shipping, customs, warehouse, and compliance tasks.
6. Planner with approval gates and auditable tool calls.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design and safety boundaries.
