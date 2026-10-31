from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ..agent import AgentRuntime
from ..config import ChatSettings
from ..domain.models import Conversation, Message
from ..errors import ChatAPIError, InputTooLargeError, InvalidInputError, NotFoundError
from ..providers import ModelRegistry
from .context import ContextBuilder
from .prompts import PromptRegistry
from .runtime import AllowLocalAccess, ConversationLocks
from .summary import SummaryService


MEMORY_PROFILES = {"recent-window-v1", "summary-window-v1"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TurnService:
    def __init__(self, settings: ChatSettings, repository, models: ModelRegistry,
                 prompts: PromptRegistry, agent: AgentRuntime, access=None):
        self.settings = settings
        self.repository = repository
        self.models = models
        self.prompts = prompts
        self.agent = agent
        self.access = access or AllowLocalAccess()
        self.context_builder = ContextBuilder(settings.server.recent_messages)
        self.summaries = SummaryService(repository, models, settings.server)
        self.locks = ConversationLocks(settings.server.lock_timeout_seconds)

    def create_conversation(self, model_profile: str | None,
                            assistant_profile: str | None,
                            memory_profile: str | None = None) -> Conversation:
        model_name = model_profile or self.settings.server.default_model_profile
        assistant_name = assistant_profile or self.settings.server.default_assistant_profile
        memory_name = memory_profile or self.settings.server.default_memory_profile
        profile = self.models.profile(model_name)
        if not profile.supports_tools:
            raise InvalidInputError(f"O perfil {model_name} não suporta ferramentas")
        if memory_name not in MEMORY_PROFILES:
            raise InvalidInputError(f"Perfil de memória desconhecido: {memory_name}")
        prompt = self.prompts.get(assistant_name)
        now = _now()
        return self.repository.create_conversation(Conversation(
            id=str(uuid4()), model_profile=model_name, assistant_profile=assistant_name,
            prompt_version=prompt.version, created_at=now, updated_at=now,
            next_sequence=1, memory_profile=memory_name,
        ))

    async def get_conversation(self, conversation_id: str, after_sequence: int,
                               limit: int) -> dict:
        await self.access.authorize(conversation_id)
        conversation = self.repository.get_conversation(conversation_id)
        if not conversation:
            raise NotFoundError("Conversa não encontrada")
        summary = self.repository.get_latest_summary(conversation_id)
        messages = self.repository.list_messages(conversation_id, after_sequence, limit)
        return {
            "id": conversation.id,
            "model_profile": conversation.model_profile,
            "assistant_profile": conversation.assistant_profile,
            "memory_profile": conversation.memory_profile,
            "prompt_version": conversation.prompt_version,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "summary": ({
                "version": summary.version, "content": summary.content,
                "through_sequence": summary.through_sequence,
                "created_at": summary.created_at,
            } if summary else None),
            "messages": [self._message_dict(item) for item in messages],
            "sources": self.repository.list_sources(conversation_id),
            "handoff_events": self.repository.list_handoff_events(conversation_id),
        }

    async def delete_conversation(self, conversation_id: str) -> None:
        await self.access.authorize(conversation_id)
        async with self.locks.hold(conversation_id):
            if not self.repository.delete_conversation(conversation_id):
                raise NotFoundError("Conversa não encontrada")

    async def send_message(self, conversation_id: str, client_message_id: str,
                           content: str) -> dict:
        await self.access.authorize(conversation_id)
        if len(content) > self.settings.server.max_message_chars:
            raise InputTooLargeError("A mensagem excede o limite configurado")
        async with self.locks.hold(conversation_id):
            state, user_message, cached = self.repository.begin_turn(
                conversation_id, client_message_id, content
            )
            if state == "completed":
                return cached
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation:
                raise NotFoundError("Conversa não encontrada")
            profile = self.models.profile(conversation.model_profile)
            prompts = self.prompts.get(conversation.assistant_profile)
            summary = None
            summary_updated = False
            context_status = "complete"
            if conversation.memory_profile == "summary-window-v1":
                summary, summary_updated, context_status = await self.summaries.maybe_update(
                    conversation_id, user_message, prompts.summary, profile
                )
            history = self.repository.list_messages(conversation_id, 0, 10000)
            context = self.context_builder.build(
                prompts.assistant, history, summary,
                profile.context_budget_tokens - profile.max_output_tokens
                - self.settings.server.tool_context_budget_tokens,
            )
            provider = self.models.provider(profile.name)
            started_at = _now()
            try:
                outcome = await self.agent.run(provider, profile, context.messages)
                current = self.repository.get_conversation(conversation_id)
                assistant = Message(
                    id=str(uuid4()), conversation_id=conversation_id,
                    sequence=current.next_sequence, role="assistant",
                    content=outcome.text.strip(), status="complete", created_at=_now(),
                )
                response = {
                    "conversation_id": conversation_id,
                    "turn": self.repository.count_user_messages(conversation_id),
                    "user_message_id": user_message.id,
                    "assistant_message": self._message_dict(assistant),
                    "model": {"profile": profile.name, "provider": profile.provider,
                              "model": outcome.model},
                    "context": {
                        "memory_profile": conversation.memory_profile,
                        "summary_used": context.summary_used,
                        "summary_updated": summary_updated,
                        "messages_used": context.source_messages,
                        "estimated_input_tokens": context.estimated_tokens,
                        "status": "degraded" if outcome.degraded_services else context_status,
                    },
                    "usage": {"input_tokens": outcome.input_tokens,
                              "output_tokens": outcome.output_tokens,
                              "latency_ms": outcome.latency_ms},
                    "sources": outcome.sources,
                    "agent": {
                        "tools_available": outcome.tools_available,
                        "tools_used": outcome.tools_used,
                        "tool_calls": len(outcome.tool_executions),
                        "stop_reason": outcome.stop_reason,
                        "degraded_services": outcome.degraded_services,
                    },
                    "handoff": outcome.handoff,
                }
                attempts = [
                    self._attempt(
                        conversation_id, user_message.id, purpose, profile.provider,
                        result.model, "completed", started_at, result.latency_ms,
                        result.input_tokens, result.output_tokens, None,
                    ) for purpose, result in outcome.attempts
                ]
                if outcome.handoff:
                    attempts.append(self._attempt(
                        conversation_id, user_message.id, "controlled_template", "server",
                        outcome.handoff["template_id"], "completed", _now(), 0,
                        None, None, None,
                    ))
                executions = [
                    {**item, "user_message_id": user_message.id}
                    for item in outcome.tool_executions
                ]
                handoff = ({**outcome.handoff, "user_message_id": user_message.id}
                           if outcome.handoff else None)
                self.repository.complete_turn(
                    conversation_id, client_message_id, assistant, response, attempts,
                    executions, outcome.sources, handoff,
                )
                return response
            except Exception as exc:
                code = exc.code if isinstance(exc, ChatAPIError) else type(exc).__name__
                self.repository.fail_turn(
                    conversation_id, client_message_id,
                    self._attempt(
                        conversation_id, user_message.id, "agent_plan", profile.provider,
                        profile.model, "failed", started_at, None, None, None, code,
                    ),
                )
                raise

    @staticmethod
    def _message_dict(message: Message) -> dict:
        return {
            "id": message.id, "sequence": message.sequence, "role": message.role,
            "content": message.content, "status": message.status,
            "created_at": message.created_at,
        }

    @staticmethod
    def _attempt(conversation_id: str, user_message_id: str, purpose: str,
                 provider: str, model: str, status: str, created_at: str,
                 latency_ms, input_tokens, output_tokens, error_code) -> dict:
        return {
            "conversation_id": conversation_id, "user_message_id": user_message_id,
            "purpose": purpose, "provider": provider, "model": model,
            "latency_ms": latency_ms, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "status": status,
            "error_code": error_code, "created_at": created_at,
        }

