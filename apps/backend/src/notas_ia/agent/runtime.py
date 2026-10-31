from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from ..domain.models import ChatRequest, GenerationResult, ToolCall
from ..errors import ProviderBadResponseError, ToolError


CITATION_RE = re.compile(r"\[(F\d+)\]")
HANDOFF_TOOL = "operations_request_human_handoff"
HANDOFF_REVOCATION_PATTERNS = (
    r"\b(?:era|foi|estava fazendo) (?:so )?(?:um )?teste\b",
    r"\b(?:so|apenas) (?:um )?teste\b",
    r"\bfalso alarme\b",
    r"\bnao (?:ha|existe|estou em|corro) perigo\b",
    r"\bnao (?:e|eh) (?:uma )?emergencia\b",
    r"\bnao (?:quero|preciso de) (?:um )?atendimento humano\b",
    r"\bnao (?:quero|preciso) falar com (?:uma pessoa|alguem|um atendente|atendente)\b",
)
EXPLICIT_HUMAN_REQUEST_PATTERNS = (
    r"\b(?:quero|preciso|gostaria de|prefiro) (?:ser atendid[ao] por|falar com) "
    r"(?:uma pessoa|alguem|um atendente|atendente|um humano)\b",
    r"\b(?:quero|preciso de|gostaria de) (?:um )?atendimento humano\b",
    r"\b(?:chame|me passe para|me transfira para) (?:uma pessoa|alguem|um atendente|atendente)\b",
    r"\b(?:tem|ha) (?:algum )?(?:atendente|humano)\b",
)
CITATION_FALLBACK = (
    "Não consegui produzir uma resposta jurídica com referências verificáveis neste "
    "momento. Posso tentar reformular a pesquisa ou continuar com informações gerais, "
    "sem apresentar uma conclusão jurídica."
)


@dataclass
class AgentOutcome:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    sources: list[dict[str, Any]] = field(default_factory=list)
    tool_executions: list[dict[str, Any]] = field(default_factory=list)
    handoff: dict[str, Any] | None = None
    attempts: list[tuple[str, GenerationResult]] = field(default_factory=list)
    tools_available: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    degraded_services: list[str] = field(default_factory=list)
    stop_reason: str = "final"


class AgentRuntime:
    def __init__(self, tool_catalog, template_registry, max_rounds: int = 2,
                 max_calls: int = 3, tool_context_budget_tokens: int = 1600):
        self.tool_catalog = tool_catalog
        self.templates = template_registry
        self.max_rounds = max_rounds
        self.max_calls = max_calls
        self.tool_context_chars = tool_context_budget_tokens * 4

    async def run(self, provider, profile, context_messages: list[dict[str, Any]]) -> AgentOutcome:
        messages = list(context_messages)
        attempts: list[tuple[str, GenerationResult]] = []
        executions: list[dict[str, Any]] = []
        tools_used: list[str] = []
        sources_by_ref: dict[str, dict[str, Any]] = {}
        chunk_refs: dict[str, str] = {}
        used_tool_chars = 0
        total_calls = 0

        async with self.tool_catalog.session() as session:
            descriptors = session.descriptors
            schemas = [item.as_llm_tool() for item in descriptors]
            available = [item.name for item in descriptors]
            for round_number in range(self.max_rounds + 1):
                result = await provider.generate(ChatRequest(
                    messages=messages,
                    temperature=profile.temperature,
                    max_output_tokens=profile.max_output_tokens,
                    tools=schemas,
                ))
                attempts.append(("agent_plan" if result.tool_calls else "agent_final", result))
                if not result.tool_calls:
                    text, cited, citation_result = await self._validate_citations(
                        result.text.strip(), sources_by_ref, provider, profile, messages,
                        schemas, attempts,
                    )
                    return self._outcome(
                        text, result.model, attempts, executions, available, tools_used,
                        session.degraded_services,
                        [sources_by_ref[ref] for ref in cited],
                        "citation_fallback" if citation_result == "fallback" else "final",
                    )

                if round_number >= self.max_rounds:
                    raise ToolError("A LLM excedeu o limite de rodadas de ferramentas")
                handoff_calls = [
                    call for call in result.tool_calls
                    if call.name == HANDOFF_TOOL
                ]
                latest_user_text = self._latest_user_text(messages)
                allowed_handoffs = [
                    call for call in handoff_calls
                    if self._handoff_allowed(call, latest_user_text)
                ]
                blocked_handoffs = [
                    call for call in handoff_calls if call not in allowed_handoffs
                ]
                if allowed_handoffs:
                    calls = allowed_handoffs[:1]
                elif handoff_calls:
                    calls = [call for call in result.tool_calls if call.name != HANDOFF_TOOL]
                else:
                    calls = result.tool_calls
                # Uma solicitação de transbordo prevalece inclusive quando o modelo
                # também sugeriu pesquisas. As chamadas descartadas não contam como
                # execuções do backend.
                total_calls += len(calls)
                if total_calls > self.max_calls:
                    raise ToolError("A LLM excedeu o limite de chamadas de ferramentas")
                messages.append(self._assistant_tool_message(result.tool_calls))

                for call in blocked_handoffs:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": json.dumps({
                            "status": "rejected",
                            "reason": "handoff_not_supported_by_current_user_message",
                            "instruction": (
                                "Não execute transbordo. Reconheça a correção ou negação "
                                "da mensagem atual e responda normalmente."
                            ),
                        }, ensure_ascii=False),
                    })

                for call in calls:
                    data = await session.call(call.name, call.arguments)
                    tools_used.append(call.name)
                    execution = {
                        "tool_name": call.name,
                        "status": "completed",
                        "strategy": None,
                        "source_ids": [],
                    }
                    if call.name == HANDOFF_TOOL:
                        handoff = dict(data)
                        text = self.templates.render(handoff["template_id"])
                        executions.append(execution)
                        outcome = self._outcome(
                            text, result.model, attempts, executions, available, tools_used,
                            session.degraded_services, [], "controlled_handoff",
                        )
                        outcome.handoff = handoff
                        return outcome

                    content, new_sources, used_chars = self._legal_tool_content(
                        data, sources_by_ref, chunk_refs,
                        max(0, self.tool_context_chars - used_tool_chars),
                    )
                    used_tool_chars += used_chars
                    execution["strategy"] = data.get("effective_strategy")
                    execution["source_ids"] = [item["chunk_id"] for item in new_sources]
                    executions.append(execution)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": content,
                    })

        raise ProviderBadResponseError("O agente terminou sem produzir resposta")

    @staticmethod
    def _latest_user_text(messages: list[dict[str, Any]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return str(message.get("content") or "")
        return ""

    @staticmethod
    def _normalized_text(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        return "".join(char for char in decomposed if not unicodedata.combining(char))

    @classmethod
    def _handoff_allowed(cls, call: ToolCall, latest_user_text: str) -> bool:
        text = cls._normalized_text(latest_user_text)
        if any(re.search(pattern, text) for pattern in HANDOFF_REVOCATION_PATTERNS):
            return False
        if call.arguments.get("reason") != "explicit_human_request":
            return True
        return any(
            re.search(pattern, text) for pattern in EXPLICIT_HUMAN_REQUEST_PATTERNS
        )

    async def _validate_citations(self, text, sources, provider, profile, messages,
                                  schemas, attempts):
        cited = list(dict.fromkeys(CITATION_RE.findall(text)))
        invalid = [item for item in cited if item not in sources]
        missing = bool(sources) and not cited
        if not invalid and not missing:
            return text, cited, "valid"
        valid_names = ", ".join(sources) or "nenhuma"
        repair_messages = [*messages, {
            "role": "system",
            "content": (
                "Corrija a resposta final. Use somente referências existentes no formato "
                f"[F1]. Referências válidas: {valid_names}. Não invente fontes."
            ),
        }]
        repaired = await provider.generate(ChatRequest(
            messages=repair_messages,
            temperature=0.1,
            max_output_tokens=profile.max_output_tokens,
            tools=[],
        ))
        attempts.append(("agent_final", repaired))
        repaired_text = repaired.text.strip()
        repaired_cited = list(dict.fromkeys(CITATION_RE.findall(repaired_text)))
        if (repaired_cited and all(item in sources for item in repaired_cited)) or not sources:
            return repaired_text, repaired_cited, "repaired"
        return CITATION_FALLBACK, [], "fallback"

    @staticmethod
    def _assistant_tool_message(calls: list[ToolCall]) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": call.id, "name": call.name, "arguments": call.arguments}
                for call in calls
            ],
        }

    @staticmethod
    def _legal_tool_content(data, sources_by_ref, chunk_refs, budget_chars):
        compact = {
            "effective_strategy": data.get("effective_strategy"),
            "fallback_reason": data.get("fallback_reason"),
            "corpus_version": data.get("corpus_version"),
            "results": [],
        }
        added = []
        used = 0
        for source in data.get("results", []):
            chunk_id = source["chunk_id"]
            ref = chunk_refs.get(chunk_id)
            if not ref:
                ref = f"F{len(chunk_refs) + 1}"
                chunk_refs[chunk_id] = ref
            base = {
                "reference": ref,
                "chunk_id": chunk_id,
                "document": source["document"],
                "section": source["section"],
                "url": source["url"],
                "verified_at": source.get("verified_at"),
            }
            prefix = json.dumps(base, ensure_ascii=False)
            remaining = budget_chars - used - len(prefix)
            if remaining <= 80:
                break
            text = source["text"]
            truncated = len(text) > remaining
            excerpt = text[:remaining].rsplit(" ", 1)[0] if truncated else text
            item = {**base, "text": excerpt, "truncated": truncated}
            compact["results"].append(item)
            used += len(json.dumps(item, ensure_ascii=False))
            if ref not in sources_by_ref:
                public_source = {key: value for key, value in base.items()}
                sources_by_ref[ref] = public_source
                added.append(public_source)
        compact["omitted_for_budget"] = max(0, len(data.get("results", [])) - len(compact["results"]))
        return json.dumps(compact, ensure_ascii=False), added, used

    @staticmethod
    def _outcome(text, model, attempts, executions, available, used, degraded,
                 sources, stop_reason):
        input_values = [item.input_tokens for _, item in attempts if item.input_tokens is not None]
        output_values = [item.output_tokens for _, item in attempts if item.output_tokens is not None]
        return AgentOutcome(
            text=text,
            model=model,
            input_tokens=sum(input_values) if input_values else None,
            output_tokens=sum(output_values) if output_values else None,
            latency_ms=sum(item.latency_ms for _, item in attempts),
            sources=sources,
            tool_executions=executions,
            attempts=attempts,
            tools_available=available,
            tools_used=list(dict.fromkeys(used)),
            degraded_services=degraded,
            stop_reason=stop_reason,
        )

