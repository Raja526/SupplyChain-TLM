"""Text-only adapter for a local CPU model executable."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess

from .context import DecisionContext
from .model import TLMResponse
from .prompt import format_prompt


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
        return TLMResponse(completed.stdout.strip(), 0.0, context.references)
