"""Stable prompt construction for a future compact SupplyChain-TLM."""

from __future__ import annotations

from .context import DecisionContext


def format_prompt(context: DecisionContext) -> str:
    lines = [
        "You are SupplyChain-TLM, an evidence-grounded logistics assistant.",
        "Explain decisions using only the supplied context.",
        "Never execute tools, claim that an action was completed, or bypass validation and approval.",
        "",
        f"REQUEST: {context.request}",
        f"VALIDATION_PASSED: {str(context.validation_passed).lower()}",
        f"VALIDATION_ISSUES: {', '.join(context.validation_issue_codes) or 'none'}",
        f"CAPABILITIES: {', '.join(context.capabilities) or 'general_supply_chain'}",
        "FACTS:",
    ]
    lines.extend(f"- {capability}.{key} = {value}" for capability, key, value in context.domain_facts)
    lines.append(f"REFERENCES: {', '.join(context.references) or 'none'}")
    lines.extend(("", "Respond with:", "1. concise explanation", "2. evidence used", "3. suggested next step", "4. whether human approval or review is required"))
    return "\n".join(lines)
