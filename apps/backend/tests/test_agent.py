from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from notas_ia.agent.runtime import AgentRuntime
from notas_ia.agent.tools import FastMCPToolCatalog, ToolDescriptor
from notas_ia.domain.models import GenerationResult, ToolCall
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
                "operations_request_human_handoff", "Transbordo",
                {"type": "object", "properties": {
                    "mode": {"type": "string"}, "reason": {"type": "string"},
                }},
            ),
        ]

    async def call(self, name, arguments):
        self.calls.append((name, arguments))
        return self.responses[name]


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
    assert len(provider.requests[0].tools) == 2


@pytest.mark.anyio
async def test_handoff_has_priority_and_stops_generation(profile, templates):
    legal_calls = [
        ToolCall(f"c{index}", "legal_search_legal_sources", {"query": "ameaça"})
        for index in range(1, 5)
    ]
    handoff = ToolCall(
        "c5", "operations_request_human_handoff",
        {"mode": "immediate", "reason": "possible_current_danger"},
    )
    handoff_result = {
        "action": "human_handoff", "mode": "immediate",
        "reason": "possible_current_danger", "status": "simulated",
        "human_available": False, "template_id": "handoff-immediate-v1",
        "stop_agent": True,
    }
    provider = FakeProvider([result(calls=[*legal_calls, handoff])])
    catalog = FakeCatalog({"operations_request_human_handoff": handoff_result})
    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile, [{"role": "user", "content": "Ele está aqui."}]
    )
    assert outcome.stop_reason == "controlled_handoff"
    assert outcome.handoff["human_available"] is False
    assert "190" in outcome.text
    assert len(provider.requests) == 1


@pytest.mark.anyio
async def test_current_correction_blocks_handoff_inherited_from_history(profile, templates):
    handoff = ToolCall(
        "c1", "operations_request_human_handoff",
        {"mode": "offer", "reason": "explicit_human_request"},
    )
    provider = FakeProvider([
        result(calls=[handoff]),
        result("Entendi: foi apenas um teste e não há perigo. Como posso ajudar?"),
    ])
    catalog = FakeCatalog({"operations_request_human_handoff": {}})

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
        "c1", "operations_request_human_handoff",
        {"mode": "offer", "reason": "explicit_human_request"},
    )
    handoff_result = {
        "action": "human_handoff", "mode": "offer",
        "reason": "explicit_human_request", "status": "simulated",
        "human_available": False, "template_id": "handoff-offer-v1",
        "stop_agent": True,
    }
    provider = FakeProvider([result(calls=[handoff])])
    catalog = FakeCatalog({"operations_request_human_handoff": handoff_result})

    outcome = await AgentRuntime(catalog, templates).run(
        provider, profile,
        [{"role": "user", "content": "Quero falar com uma pessoa."}],
    )

    assert outcome.stop_reason == "controlled_handoff"
    assert len(catalog.fake_session.calls) == 1


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
        assert [item.name for item in session.descriptors] == [
            "operations_request_human_handoff"
        ]
        result = await session.call("operations_request_human_handoff", {
            "mode": "offer", "reason": "explicit_human_request",
        })
    assert result["stop_agent"] is True
    assert result["human_available"] is False

