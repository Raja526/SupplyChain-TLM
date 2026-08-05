"""Stable prompt construction for a future compact SupplyChain-TLM."""

from __future__ import annotations

from .context import DecisionContext


def format_prompt(context: DecisionContext) -> str:
    lines = [
        "You are SupplyChain-TLM. Use only the evidence below.",
        "Never execute tools; do not claim completion or bypass validation/approval.",
        f"REQUEST: {context.request}",
        f"STATE: passed={str(context.validation_passed).lower()} issues={','.join(context.validation_issue_codes) or 'none'}",
        f"DOMAINS: {','.join(context.capabilities) or 'general_supply_chain'}",
        "EVIDENCE:",
    ]
    lines.extend(f"- {capability}.{key} = {value}" for capability, key, value in context.domain_facts)
    lines.append(f"SOURCES: {','.join(context.references) or 'none'}")
    lines.append("Answer briefly with: decision, evidence, next step, and whether human review/approval is required.")
    return "\n".join(lines)
