# SupplyChain-TLM PoC demo

Run the complete local demonstration:

```bash
cd ~/Downloads/llm-in-c/tlm-development-for-cpus
./scripts/demo.sh
```

## Suggested narration

1. “The system receives a shipment bundle containing an invoice, purchase order, packing list, and bill of lading.”
2. “Deterministic validation compares the documents before any action is proposed.”
3. “The first pass is review-only; the model or planner cannot execute an ERP operation.”
4. “A procurement approval is then supplied explicitly.”
5. “The ERP call is still a dry run, and the audit trail records the workflow.”
6. “When the invoice total is changed to disagree with the purchase order, validation blocks the release and no ERP action is executed.”

## What this proves

- Cross-document validation runs before action planning.
- Approval is a separate gate from model reasoning.
- The tool call is idempotent and auditable.
- A cross-document mismatch stops the workflow before execution.
- The current connector is intentionally a dry-run adapter.

## Be explicit about the boundary

This PoC does not connect to live SAP, Oracle, WMS, email, or production OCR. Those integrations require vendor sandbox access, credentials, operational monitoring, and security review.

For a CPU-model demonstration, configure the local Qwen wrapper separately. Keep the deterministic workflow as the safety boundary; the language model must not receive direct enterprise credentials or tool execution authority.
