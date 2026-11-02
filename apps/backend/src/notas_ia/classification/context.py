from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from ..domain.models import Message, Summary


@dataclass(frozen=True)
class ClassificationSnapshot:
    """Estado factual congelado antes do agente receber qualquer inferência."""

    payload: dict
    canonical_json: str
    sha256: str


class ClassificationContextBuilder:
    def __init__(self, recent_messages: int):
        self.recent_messages = recent_messages

    def build(self, taxonomy_version: str, history: list[Message],
              summary: Summary | None) -> ClassificationSnapshot:
        if not history or history[-1].role != "user":
            raise ValueError("O snapshot deve terminar na mensagem atual da usuária")
        # Classification is about signals reported by the user. Prior assistant text
        # may contain examples, emergency numbers or a previous model error; treating
        # it as evidence contaminates the label for the next turn. The factual summary
        # is retained because its contract excludes assistant conclusions and RAG.
        after_summary = [
            item for item in history
            if (not summary or item.sequence > summary.through_sequence)
            and item.role == "user"
        ]
        selected = after_summary[-self.recent_messages:]
        payload = {
            "taxonomy_version": taxonomy_version,
            "summary": summary.content if summary else None,
            "summary_through_sequence": summary.through_sequence if summary else None,
            "messages": [
                {
                    "message_id": item.id,
                    "sequence": item.sequence,
                    "role": item.role,
                    "content": item.content,
                }
                for item in selected
            ],
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return ClassificationSnapshot(
            payload=payload,
            canonical_json=canonical,
            sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        )
