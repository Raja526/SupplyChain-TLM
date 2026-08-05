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

## Roadmap

1. Document schemas and deterministic validation.
2. OCR/document-ingestion adapters.
3. Retrieval over logistics knowledge and rules.
4. Compact CPU SupplyChain-TLM training/evaluation pipeline.
5. Domain adapters for financial, shipping, customs, warehouse, and compliance tasks.
6. Planner with approval gates and auditable tool calls.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design and safety boundaries.
