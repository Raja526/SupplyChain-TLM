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

It now also includes an optional `TesseractProvider`. Install Tesseract separately, then call it with an image/PDF path. The current adapter returns page-1 text; production layout and page-level provenance remain future work.

Run the installed OCR pipeline:

```bash
python3 -m src.supplychain_tlm.ocr_cli invoice.png
```

The command runs Tesseract, applies the baseline field extractor, and reports whether human review is required.

The reusable `ingest_document()` function composes the same stages programmatically and can attach uncertain results to `ReviewQueue`.

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

## TLM integration boundary

`TLMBackend` defines the future model interface. The included `RuleBasedSupplyChainTLM` is only a deterministic baseline: it explains validation results and suggests review or approval, but it cannot execute tools.

Run the current answer path:

```bash
python3 -m src.supplychain_tlm.answer_cli \
  examples/shipment_bundle.json \
  "Can this shipment be released?"
```

This prints the answer, confidence, references, and suggested action. It never executes an enterprise tool.

Use a local CPU executable instead of the baseline backend:

```bash
python3 -m src.supplychain_tlm.answer_cli \
  examples/shipment_bundle.json "Can this shipment be released?" \
  --command /path/to/cpu-inference-binary \
  --timeout 180
```

For the existing Qwen C chat binary, use the included wrapper:

```bash
export QWEN_CHAT_BIN=~/Downloads/llm-in-c/qwen3.5-2b-in-c/bin/qwen36-chat
export QWEN_MODEL=/path/to/Qwen3.5-2B
export QWEN_CONFIG="$QWEN_MODEL/config.json"
export QWEN_TOKENIZER="$QWEN_MODEL/tokenizer.json"
export QWEN_MAX_NEW=128

python3 -m src.supplychain_tlm.answer_cli \
  examples/shipment_bundle.json \
  "Can this shipment be released?" \
  --command scripts/qwen_chat_backend.sh
```

The wrapper passes text to the Qwen executable only. Approval and enterprise tools remain controlled by this parent project.

For CPU performance, keep the validated FP32/OpenBLAS path as the default:

```bash
export QWEN_THINKING=0
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=12
```

On the local Qwen3.5-2B checkpoint, a one-token prompt measured about 4.0 seconds with FP32/OpenBLAS, 5.2 seconds with `QWEN_LINEAR_INT8=1`, and 7.5 seconds with `QWEN_INT8=1`. INT8 remains opt-in and experimental; it is not enabled automatically.

Check a checkpoint before connecting it:

```bash
python3 -m src.supplychain_tlm.checkpoint /path/to/Qwen3.5-2B
```

The preflight rejects missing files and architecture mismatches, including accidentally pointing the 2B backend at the 35B checkpoint.

Training examples can be split reproducibly by example ID:

```python
from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.split import split_examples

split = split_examples(load_jsonl("examples/training_tasks.jsonl"))
```

The split is deterministic and keeps examples disjoint, which makes later CPU-model evaluation repeatable.

`format_prompt()` converts the same context into a compact prompt contract for a CPU model backend. The safety boundary is included in the prompt, but enforcement remains in deterministic code. The prompt intentionally includes only routed domain facts, validation status, and reference IDs to reduce CPU prefill work.

`ProcessTLMBackend` connects that prompt to a local executable through stdin and returns text only. It supports timeouts, nonzero-exit handling, and removes known Qwen inference telemetry lines from stdout; it does not pass tool capabilities to the model process.

## Training and evaluation tasks

`examples/training_tasks.jsonl` is the initial versioned task format for future compact-model training and evaluation. Each example contains a domain, instruction, structured context, target response, and safety label such as `request_review`, `request_approval`, or `refuse_action`.

Evaluate the current baseline:

```bash
python3 -m src.supplychain_tlm.evaluation examples/training_tasks.jsonl
```

Benchmark the current backend:

```bash
python3 -m src.supplychain_tlm.benchmark examples/training_tasks.jsonl
```

The same harness can later compare a real CPU inference backend by passing it to the benchmark function.

`build_release_plan()` exposes the autonomous workflow as explicit states: validation, retrieval, human review, approval, and execution. This is a plan only; it does not perform the final action.

Uncertain extraction results can be placed into the durable human-review queue. Resolved items are recorded as append-only JSONL events before automation continues.

Manage the queue from the terminal:

```bash
python3 -m src.supplychain_tlm.review_cli --queue review/review.jsonl enqueue document.txt
python3 -m src.supplychain_tlm.review_cli --queue review/review.jsonl list
python3 -m src.supplychain_tlm.review_cli --queue review/review.jsonl resolve ITEM_ID analyst-1 corrected
```

## Roadmap

1. Document schemas and deterministic validation.
2. OCR/document-ingestion adapters.
3. Retrieval over logistics knowledge and rules.
4. Compact CPU SupplyChain-TLM training/evaluation pipeline.
5. Domain adapters for financial, shipping, customs, warehouse, and compliance tasks.
6. Planner with approval gates and auditable tool calls.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design and safety boundaries.
