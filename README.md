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

## Roadmap

1. Document schemas and deterministic validation.
2. OCR/document-ingestion adapters.
3. Retrieval over logistics knowledge and rules.
4. Compact CPU SupplyChain-TLM training/evaluation pipeline.
5. Domain adapters for financial, shipping, customs, warehouse, and compliance tasks.
6. Planner with approval gates and auditable tool calls.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design and safety boundaries.
