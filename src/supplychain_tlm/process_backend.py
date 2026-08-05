"""Text-only adapter for a local CPU model executable."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess

from .context import DecisionContext
from .model import TLMResponse
from .prompt import format_prompt


def clean_model_output(output: str) -> str:
    """Remove known inference telemetry from text-only local model output."""
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
    if facts.get("approval_present", "true").lower() == "false":
        return "refuse_action"
    if not context.validation_passed:
        return "request_document_review"
    if "release" in context.request.lower() or "clearance" in context.request.lower():
        return "request_approval"
    return None


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
        return TLMResponse(answer, 0.0, context.references, safe_action_for(context))
