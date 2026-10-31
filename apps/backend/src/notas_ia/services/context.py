from __future__ import annotations

import math
from dataclasses import dataclass

from ..domain.models import Message, Summary
from ..errors import InputTooLargeError


def estimate_tokens(text: str) -> int:
    """Estimativa conservadora e substituível; não finge ser tokenização exata."""
    return max(1, math.ceil(len(text) / 4))


def estimate_chat_tokens(messages: list[dict[str, str]]) -> int:
    return sum(estimate_tokens(item["content"]) + 4 for item in messages) + 3


@dataclass(frozen=True)
class ContextResult:
    messages: list[dict[str, str]]
    estimated_tokens: int
    source_messages: int
    summary_used: bool


class ContextBuilder:
    def __init__(self, recent_messages: int):
        self.recent_messages = recent_messages

    def build(self, system_prompt: str, history: list[Message], summary: Summary | None,
              input_budget: int) -> ContextResult:
        summary_message = None
        if summary:
            summary_message = {
                "role": "system",
                "content": "Resumo factual da conversa anterior:\n" + summary.content,
            }
        minimum = [{"role": "system", "content": system_prompt}]
        if summary_message:
            minimum.append(summary_message)
        if not history or history[-1].role != "user":
            raise ValueError("O histórico deve terminar na mensagem atual da usuária")
        current = {"role": "user", "content": history[-1].content}
        minimum.append(current)
        if estimate_chat_tokens(minimum) > input_budget:
            raise InputTooLargeError(
                "Prompt, resumo e mensagem atual excedem o contexto do modelo"
            )

        after_summary = [item for item in history
                         if not summary or item.sequence > summary.through_sequence]
        selected = after_summary[-self.recent_messages:]
        while selected:
            candidate = [{"role": "system", "content": system_prompt}]
            if summary_message:
                candidate.append(summary_message)
            candidate.extend({"role": item.role, "content": item.content} for item in selected)
            if estimate_chat_tokens(candidate) <= input_budget:
                content_start = 2 if summary_message else 1
                while (len(candidate) > content_start
                       and candidate[content_start]["role"] == "assistant"):
                    candidate.pop(content_start)
                return ContextResult(candidate, estimate_chat_tokens(candidate),
                                     len(candidate) - content_start, bool(summary_message))
            selected.pop(0)

        return ContextResult(minimum, estimate_chat_tokens(minimum), 1, bool(summary_message))
