from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ..config import ModelProfile, ServerSettings
from ..domain.models import ChatRequest, Message, Summary
from ..errors import ChatAPIError
from ..providers import ModelRegistry
from .context import estimate_chat_tokens


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SummaryService:
    def __init__(self, repository, models: ModelRegistry, server: ServerSettings):
        self.repository = repository
        self.models = models
        self.server = server

    def _request_messages(self, prompt: str, previous: Summary | None,
                          candidates: list[Message], budget: int) -> tuple[list[dict], int]:
        prefix = "Resumo anterior:\n" + (previous.content if previous else "(nenhum)")
        selected: list[Message] = []
        for item in candidates:
            transcript = "\n".join(
                f"[{message.sequence}] {message.role}: {message.content}"
                for message in selected + [item]
            )
            request = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": prefix + "\n\nMensagens novas:\n" + transcript},
            ]
            if estimate_chat_tokens(request) > budget:
                break
            selected.append(item)
        if not selected:
            raise ValueError("Nenhuma mensagem antiga cabe no pedido de resumo")
        transcript = "\n".join(
            f"[{message.sequence}] {message.role}: {message.content}" for message in selected
        )
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": prefix + "\n\nMensagens novas:\n" + transcript},
        ], selected[-1].sequence

    async def maybe_update(self, conversation_id: str, user_message: Message,
                           prompt: str, model_profile: ModelProfile
                           ) -> tuple[Summary | None, bool, str]:
        previous = self.repository.get_latest_summary(conversation_id)
        through = previous.through_sequence if previous else 0
        unsummarized = self.repository.list_messages(conversation_id, through, 10000)
        estimated = estimate_chat_tokens([
            {"role": item.role, "content": item.content} for item in unsummarized
        ]) if unsummarized else 0
        should_update = (
            len(unsummarized) > self.server.summary_trigger_messages
            or estimated > self.server.summary_trigger_tokens
        )
        candidates = unsummarized[:-self.server.recent_messages]
        if not should_update or not candidates:
            return previous, False, "complete"

        provider = self.models.provider(model_profile.name)
        input_budget = model_profile.context_budget_tokens - model_profile.max_output_tokens
        started_at = _now()
        try:
            messages, target_sequence = self._request_messages(
                prompt, previous, candidates, input_budget
            )
            result = await provider.generate(ChatRequest(
                messages=messages,
                temperature=0.1,
                max_output_tokens=min(512, model_profile.max_output_tokens),
            ))
            summary = Summary(
                id=str(uuid4()),
                conversation_id=conversation_id,
                version=(previous.version + 1) if previous else 1,
                content=result.text.strip(),
                through_sequence=target_sequence,
                model_profile=model_profile.name,
                model=result.model,
                created_at=_now(),
            )
            self.repository.save_summary(summary)
            self.repository.record_attempt({
                "conversation_id": conversation_id,
                "user_message_id": user_message.id,
                "purpose": "summary",
                "provider": model_profile.provider,
                "model": result.model,
                "latency_ms": result.latency_ms,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "status": "completed",
                "error_code": None,
                "created_at": started_at,
            })
            return summary, True, "complete"
        except Exception as exc:
            error_code = exc.code if isinstance(exc, ChatAPIError) else type(exc).__name__
            self.repository.record_attempt({
                "conversation_id": conversation_id,
                "user_message_id": user_message.id,
                "purpose": "summary",
                "provider": model_profile.provider,
                "model": model_profile.model,
                "latency_ms": None,
                "input_tokens": None,
                "output_tokens": None,
                "status": "failed",
                "error_code": error_code,
                "created_at": started_at,
            })
            return previous, False, "summary_failed_recent_only"
