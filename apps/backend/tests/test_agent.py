from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from notas_ia.agent.runtime import AgentRuntime
from notas_ia.agent.tools import FastMCPToolCatalog, ToolDescriptor
from notas_ia.domain.models import GenerationResult, ToolCall
from notas_ia.errors import ToolError
from notas_ia.operations import HandoffTemplateRegistry


def result(text="", calls=None, model="fake"):
    return GenerationResult(
        text=text, model=model, finish_reason="stop", input_tokens=10,
        output_tokens=3, latency_ms=5, tool_calls=calls or [],
    )


class FakeProvider:
    def __init__(self, results):
        self.results = list(results)
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return self.results.pop(0)


class FakeSession:
    def __init__(self, responses, degraded=None):
        self.responses = responses
        self.calls = []
        self.degraded_services = degraded or []
        self.descriptors = [
            ToolDescriptor(
                "legal_search_legal_sources", "Busca legislação",
                {"type": "object", "properties": {"query": {"type": "string"}}},
            ),
            ToolDescriptor(
                "operations_offer_human_handoff", "Oferta de transbordo",
                {"type": "object", "properties": {"reason": {"type": "string"}}},
            ),
            ToolDescriptor(
                "operations_escalate_immediate", "Escalada imediata",
                {"type": "object", "properties": {}},
            ),
            ToolDescriptor(
                "information_get_general_help_resources", "Canais gerais",
                {"type": "object", "properties": {}},
            ),
            ToolDescriptor(
                "information_get_violence_type_overview", "Tipos de violência",
                {"type": "object", "properties": {}},
            ),
        ]

    async def call(self, name, arguments):
        self.calls.append((name, arguments))
        response = self.responses[name]
        if isinstance(response, Exception):
            raise response
        return response


class FakeCatalog:
    def __init__(self, responses):
        self.fake_session = FakeSession(responses)

    @asynccontextmanager
    async def session(self):
        yield self.fake_session


@pytest.fixture
def profile():
    return SimpleNamespace(temperature=0.2, max_output_tokens=128)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def templates():
    return HandoffTemplateRegistry(
        Path(__file__).parents[1] / "src" / "notas_ia" / "prompts"
    )


def test_safety_regression_fixture_covers_figurative_and_literal_cases():
    fixture = Path(__file__).parent / "fixtures" / "safety-regressions.v1.json"
    cases = json.loads(fixture.read_text(encoding="utf-8"))["cases"]
    identifiers = {item["id"] for item in cases}
    assert {
        "figurative-killed-laughing",
        "figurative-died-of-fear",
        "literal-current-threat",
        "revoke-minimal-alarm",
    } <= identifiers


@pytest.mark.anyio
async def test_legal_tool_then_cited_answer(profile, templates):
    call = ToolCall("c1", "legal_search_legal_sources", {"query": "violência patrimonial"})
    provider = FakeProvider([result(calls=[call]), result("A lei descreve a retenção [F1].")])
    catalog = FakeCatalog({"legal_search_legal_sources": {
        "effective_strategy": "bm25", "fallback_reason": None,
        "corpus_version": "v1", "results": [{
            "chunk_id": "lei:art1", "document": "Lei de teste", "section": "Art. 1",
            "url": "https://example.test", "verified_at": "2026-01-01",
            "text": "Retenção de documentos.",
        }],
    }})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "O que diz a lei?"}]
    )
    assert outcome.text.endswith("[F1].")
    assert outcome.sources[0]["chunk_id"] == "lei:art1"
    assert outcome.tools_used == ["legal_search_legal_sources"]
    assert len(provider.requests[0].tools) == 5


@pytest.mark.anyio
async def test_handoff_has_priority_and_stops_generation(profile, templates):
    legal_calls = [
        ToolCall(f"c{index}", "legal_search_legal_sources", {"query": "ameaça"})
        for index in range(1, 5)
    ]
    handoff = ToolCall(
        "c5", "operations_escalate_immediate", {},
    )
    handoff_result = {
        "action": "human_handoff", "mode": "immediate",
        "reason": "possible_current_danger", "status": "simulated",
        "human_available": False, "template_id": "handoff-immediate-v1",
        "stop_agent": True,
    }
    provider = FakeProvider([result(calls=[*legal_calls, handoff])])
    catalog = FakeCatalog({"operations_escalate_immediate": handoff_result})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "Ele está aqui."}]
    )
    assert outcome.stop_reason == "controlled_handoff"
    assert outcome.handoff["human_available"] is False
    assert "190" in outcome.text
    assert len(provider.requests) == 1


@pytest.mark.anyio
async def test_immediate_handoff_uses_a_dedicated_tool(profile, templates):
    handoff = ToolCall(
        "c1", "operations_escalate_immediate", {},
    )
    handoff_result = {
        "action": "human_handoff", "mode": "immediate",
        "reason": "possible_current_danger", "status": "simulated",
        "human_available": False, "template_id": "handoff-immediate-v1",
        "stop_agent": True,
    }
    provider = FakeProvider([result(calls=[handoff])])
    catalog = FakeCatalog({"operations_escalate_immediate": handoff_result})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "Ele está tentando entrar agora."}]
    )
    assert catalog.fake_session.calls[0] == (
        "operations_escalate_immediate", {}
    )
    assert outcome.stop_reason == "controlled_handoff"


@pytest.mark.anyio
async def test_current_correction_blocks_handoff_inherited_from_history(profile, templates):
    handoff = ToolCall(
        "c1", "operations_offer_human_handoff",
        {"reason": "explicit_human_request"},
    )
    provider = FakeProvider([
        result(calls=[handoff]),
        result("Entendi: foi apenas um teste e não há perigo. Como posso ajudar?"),
    ])
    catalog = FakeCatalog({"operations_offer_human_handoff": {}})

    outcome = await AgentRuntime(catalog, templates).run(provider, profile, [
        {"role": "user", "content": "SOCORRO"},
        {"role": "assistant", "content": "Resposta controlada anterior."},
        {"role": "user", "content": (
            "Estava te testando; não há perigo e não quero atendimento humano."
        )},
    ])

    assert outcome.handoff is None
    assert outcome.tools_used == []
    assert catalog.fake_session.calls == []
    assert len(provider.requests) == 2
    assert provider.requests[1].messages[-1]["role"] == "tool"
    assert "rejected" in provider.requests[1].messages[-1]["content"]


@pytest.mark.anyio
async def test_explicit_human_request_must_be_affirmative_in_current_turn(profile, templates):
    handoff = ToolCall(
        "c1", "operations_offer_human_handoff",
        {"reason": "explicit_human_request"},
    )
    handoff_result = {
        "action": "human_handoff", "mode": "offer",
        "reason": "explicit_human_request", "status": "simulated",
        "human_available": False, "template_id": "handoff-offer-v1",
        "stop_agent": True,
    }
    provider = FakeProvider([result(calls=[handoff])])
    catalog = FakeCatalog({"operations_offer_human_handoff": handoff_result})

    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile,
        [{"role": "user", "content": "Quero falar com uma pessoa."}],
    )

    assert outcome.stop_reason == "controlled_handoff"
    assert len(catalog.fake_session.calls) == 1


@pytest.mark.anyio
async def test_tool_error_returns_to_llm_for_next_iteration(profile, templates):
    failed = ToolCall("c1", "legal_search_legal_sources", {"query": "lei"})
    provider = FakeProvider([
        result(calls=[failed]),
        result("Não consegui consultar a fonte neste momento."),
    ])
    catalog = FakeCatalog({"legal_search_legal_sources": ToolError("índice indisponível")})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "O que diz a lei?"}]
    )
    assert outcome.text == "Não consegui consultar a fonte neste momento."
    assert outcome.tool_executions[0]["status"] == "failed"
    assert len(provider.requests) == 2
    assert '"status": "error"' in provider.requests[1].messages[-1]["content"]


@pytest.mark.anyio
async def test_curated_information_is_returned_as_bounded_tool_context(profile, templates):
    call = ToolCall("c1", "information_get_general_help_resources", {})
    provider = FakeProvider([result(calls=[call]), result("O canal 180 pode orientar." )])
    catalog = FakeCatalog({"information_get_general_help_resources": {
        "resource_id": "general-help-resources", "version": "v1",
        "reviewed_at": "2026-11-01", "scope": "informação geral",
        "content": "Ligue 180.", "sources": [],
    }})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "Quais canais existem?"}]
    )
    assert outcome.text == "O canal 180 pode orientar."
    assert outcome.tool_executions[0]["source_ids"] == ["resource:general-help-resources"]
    assert "general-help-resources" in provider.requests[1].messages[-1]["content"]


@pytest.mark.anyio
async def test_ungrounded_emergency_channel_is_replaced_by_controlled_fallback(profile, templates):
    """A model must not invent an emergency-channel association after a tool failure."""
    provider = FakeProvider([result("Ligue para o SAMU pelo 190 imediatamente.")])
    outcome = await AgentRuntime(FakeCatalog({}), templates).run(
        provider, profile, [{"role": "user", "content": "Estou preocupada."}]
    )
    assert outcome.stop_reason == "controlled_resource_fallback"
    assert "190" not in outcome.text
    assert "SAMU" not in outcome.text


@pytest.mark.anyio
async def test_curated_resource_allows_its_channel_information(profile, templates):
    call = ToolCall("c1", "information_get_general_help_resources", {})
    provider = FakeProvider([
        result(calls=[call]), result("Em emergência, a Polícia Militar atende pelo 190."),
    ])
    catalog = FakeCatalog({"information_get_general_help_resources": {
        "resource_id": "general-help-resources", "version": "v1",
        "reviewed_at": "2026-11-01", "scope": "informação geral",
        "content": "Em emergência, acione a Polícia Militar pelo 190.", "sources": [],
    }})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "Qual canal uso?"}]
    )
    assert outcome.stop_reason == "final"
    assert outcome.text.endswith("190.")


@pytest.mark.anyio
async def test_invalid_citation_falls_back_after_one_repair(profile, templates):
    call = ToolCall("c1", "legal_search_legal_sources", {"query": "lei"})
    provider = FakeProvider([
        result(calls=[call]), result("Afirmação sem fonte."), result("Fonte inventada [F99].")
    ])
    catalog = FakeCatalog({"legal_search_legal_sources": {
        "effective_strategy": "bm25", "fallback_reason": None,
        "corpus_version": "v1", "results": [{
            "chunk_id": "lei:art1", "document": "Lei", "section": "Art. 1",
            "url": "https://example.test", "verified_at": "2026-01-01", "text": "Texto",
        }],
    }})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "Pergunta"}]
    )
    assert outcome.stop_reason == "citation_fallback"
    assert not outcome.sources
    assert "referências verificáveis" in outcome.text


@pytest.mark.anyio
async def test_real_catalog_keeps_operations_when_legal_mcp_is_down():
    catalog = FastMCPToolCatalog("http://127.0.0.1:9/mcp", timeout=0.2)
    async with catalog.session() as session:
        assert session.degraded_services == ["legal"]
        assert {item.name for item in session.descriptors} == {
            "operations_offer_human_handoff", "operations_escalate_immediate",
            "information_get_general_help_resources",
            "information_get_violence_type_overview",
        }
        result = await session.call("operations_offer_human_handoff", {
            "reason": "explicit_human_request",
        })
    assert result["stop_agent"] is True
    assert result["human_available"] is False
    async with catalog.session() as session:
        immediate = await session.call("operations_escalate_immediate", {})
    assert immediate["reason"] == "possible_current_danger"

