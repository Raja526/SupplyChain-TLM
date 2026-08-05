# SupplyChain-TLM architecture

## Objective

Build a compact model and agent runtime that can understand supply-chain documents, explain discrepancies, and propose next actions while keeping external side effects behind explicit tools and approvals.

## Layers

### 1. Document intelligence

Inputs include invoices, purchase orders, packing lists, bills of lading, certificates, and customs documents. This layer performs OCR, classification, field extraction, table extraction, normalization, and provenance tracking.

### 2. Shared SupplyChain-TLM

The model provides logistics language understanding, document-grounded question answering, discrepancy explanations, and structured reasoning support. It should not directly call SAP, send email, execute SQL, or mutate workflows.

### 3. Domain adapters

Adapters specialize the shared model by business capability rather than by isolated document type:

- Financial: invoices, purchase orders, currency, tax, payment terms.
- Shipping: bills of lading, containers, vessels, voyages, carriers.
- Customs: HS codes, tariffs, duties, certificates, Incoterms.
- Warehouse: goods receipt, delivery notes, inventory, bins, pick lists.
- Compliance: dangerous goods, sanctions, export controls, restrictions.

The first implementation can use deterministic routing and prompt/schema adapters. LoRA or sparse experts can be evaluated later after a shared baseline exists.

### 4. Planner and workflow manager

The planner converts validated facts and a user goal into a proposed sequence of steps. Every action should have a typed input, a reason, an authorization requirement, and an audit record.

### 5. Tools

Tools own side effects: OCR services, ERP APIs, databases, email, Teams/Slack, and search systems. The model proposes tool calls; the tool layer validates and executes them.

## Safety boundary

No external action should occur solely because a model generated text. The minimum control flow is:

```text
extract → validate → propose → approval/policy check → execute → audit
```

The current planner implements only the `propose` stage. Enterprise connectors and execution are intentionally absent until approval, policy, idempotency, and audit contracts are defined.

The tool contract now requires all four controls: a typed operation, an idempotency key, an approval record, and audit events for blocked, started, and completed calls.

Policy checks occur before execution. A completed idempotency key is rejected on reuse, preventing accidental duplicate ERP mutations during retries.

Audit events can be persisted as JSON Lines. This is a local development format; production deployments should forward the same event contract to a durable, access-controlled audit system.

`ReleaseWorkflow` is the current reference composition. It keeps preparation separate from `approve_and_execute`, making it possible to insert a human-review UI or policy service between proposal and execution.

The text extractor is only a first-pass adapter after OCR. Extracted values must retain source-page provenance and confidence before being admitted into a production validation workflow.

The current extractor exposes field confidence and a `needs_human_review` gate. A future document-review service should preserve the original OCR span, page, bounding box, extractor version, and reviewer decision.

The local knowledge index is context retrieval only. It does not make a compliance decision; retrieved references must be shown with their source and evaluated against current company policy and authoritative regulations.

Planner outputs carry reference IDs so a reviewer can inspect the guidance used during proposal generation. References never override deterministic validation or approval policy.

Domain adapters expose capability-specific views over the same typed document bundle. This preserves cross-document context while allowing specialized prompts, rules, or future LoRA/sparse experts.

The decision-context layer is the planned interface between these components and a compact TLM. It carries facts and evidence, while action authorization remains outside the model.

The context has a stable JSON representation for prompt construction, evaluation fixtures, and later model-serving APIs.

The TLM backend receives `DecisionContext` and returns an answer, confidence, references, and a suggested action. Suggested actions remain proposals; only the planner, approval gate, and tool policy can authorize side effects.

The process backend is intentionally narrow: prompt in, text out, timeout and nonzero-exit handling. Tool execution remains in the parent process behind policy and approval gates.

Prompt construction is deterministic and inspectable. A model may produce language, but it cannot grant itself approval or directly invoke tools.

The review queue provides the human-in-the-loop path for uncertain extraction. A document should not be promoted to trusted structured data merely because an OCR or model component produced fields.

OCR providers are replaceable. The Tesseract adapter is an optional subprocess integration with timeout and failure handling; it is not required for the core tests or JSON workflow.

## Example decision

“Can this shipment be released?” may require comparing the purchase order, invoice, packing list, bill of lading, HS code, Incoterm, insurance, and clearance status. This is why a shared model plus cross-document context is preferable to one model per document type.

## CPU-first constraints

- Start with a compact shared model, approximately 300M–700M parameters.
- Keep schemas, rules, and tool contracts deterministic.
- Measure prompt latency, decode speed, memory use, and extraction accuracy separately.
- Prefer retrieval and adapters over duplicating full models.
- Keep model weights and customer documents outside source control.
