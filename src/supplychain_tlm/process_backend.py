"""Text-only adapter for a local CPU model executable."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess

from .context import DecisionContext
from .model import TLMResponse
from .prompt import format_prompt


def clean_model_output(output: str) -> str:
    """Remove known inference telemetry from text-only local model output."""
    # Reasoning traces are not the user-facing answer. If a backend emits an
    # incomplete trace, discard it so the caller can use deterministic fallback.
    if "<think>" in output.lower():
        start = output.lower().find("<think>")
        end = output.lower().find("</think>", start)
        output = output[end + len("</think>"):] if end >= 0 else output[:start]
    ignored_prefixes = (
        "qwen config:",
        "prompt_tokens=",
        "timing:",
        "generated_tokens=",
    )
    lines = [line.strip() for line in output.splitlines()]
    useful = [line for line in lines if line and not line.lower().startswith(ignored_prefixes)]
    return "\n".join(useful).strip()


def safe_action_for(context: DecisionContext) -> str | None:
    """Derive workflow metadata from deterministic state, never model text."""
    facts = dict((key, value) for _, key, value in context.domain_facts)
    request = context.request.lower()
    if facts.get("approval_bypass_requested", "false").lower() == "true" or any(
        phrase in request
        for phrase in (
            "without approval",
            "bypass approval",
            "skip approval",
            "ignore approval",
            "without authorization",
            "bypass authorization",
            "release immediately",
            "execute immediately",
            "post immediately",
            "approve payment even though",
            "immediately",
        )
    ):
        return "refuse_action"
    if not context.validation_passed:
        return "request_document_review"
    action_terms = ("release", "clearance", "clear", "post", "approve", "execute", "dispatch", "leave the port", "depart", "proceed", "export", "payment")
    if any(term in request for term in action_terms):
        return "request_approval"
    return None


def enforce_safety_notice(answer: str, action: str | None) -> str:
    """Make the deterministic workflow requirement explicit beside model text."""
    notices = {
        "request_document_review": "Deterministic control: release is blocked until document review resolves the validation issues.",
        "request_approval": "Deterministic control: procurement_manager approval is required before any release action.",
        "refuse_action": "Deterministic control: the requested action is refused by policy.",
    }
    notice = notices.get(action)
    return f"{answer}\n\n{notice}" if notice else answer


@dataclass(frozen=True)
class ProcessTLMBackend:
    command: tuple[str, ...]
    timeout_seconds: float = 60.0
    name: str = "local_process"

    def answer(self, context: DecisionContext) -> TLMResponse:
        if not self.command:
            raise ValueError("local model command cannot be empty")
        try:
            completed = subprocess.run(self.command, input=format_prompt(context), text=True, capture_output=True, timeout=self.timeout_seconds, check=False)
        except subprocess.TimeoutExpired as error:
            raise TimeoutError(f"local model timed out after {self.timeout_seconds}s") from error
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"exit code {completed.returncode}"
            raise RuntimeError(f"local model failed: {detail}")
        answer = clean_model_output(completed.stdout)
        if not answer:
            raise RuntimeError("local model returned no usable answer")
        action = safe_action_for(context)
        return TLMResponse(enforce_safety_notice(answer, action), 0.0, context.references, action)
