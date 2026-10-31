from __future__ import annotations

import asyncio
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from notas_ia.app import create_app
from notas_ia.config import (AssistantProfile, ChatSettings, MCPSettings, ModelProfile,
                             ServerSettings, load_settings)
from notas_ia.cli import _terminal_text
from notas_ia.domain.models import ChatRequest, Conversation, Message
from notas_ia.errors import ConflictError, ProviderBadResponseError
from notas_ia.providers import OllamaProvider, OpenAICompatibleProvider
from notas_ia.repositories import SQLiteConversationRepository


class EmptyToolSession:
    descriptors = []
    degraded_services = []

    async def call(self, name, arguments):
        raise AssertionError("Nenhuma ferramenta deveria ser chamada")


class EmptyToolCatalog:
    @asynccontextmanager
    async def session(self):
        yield EmptyToolSession()

    async def status(self):
        return {"status": "ok", "degraded_services": [], "tools": []}


@contextmanager
def workspace_tempdir():
    """O sandbox do desktop permite escrita no workspace, não no TEMP do Windows."""
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        yield directory


def make_settings(root: Path, provider: str = "ollama",
                  trigger_messages: int = 12, recent_messages: int = 6) -> ChatSettings:
    assistant = root / "assistant.md"
    summary = root / "summary.md"
    assistant.write_text("PROMPT DO ASSISTENTE", encoding="utf-8")
    summary.write_text("PROMPT DE RESUMO", encoding="utf-8")
    server = ServerSettings(
        database_path=root / "chat.sqlite3",
        host="127.0.0.1",
        port=8000,
        allowed_origins=("http://127.0.0.1:8765",),
        default_model_profile="fake",
        default_assistant_profile="test",
        default_memory_profile="recent-window-v1",
        recent_messages=recent_messages,
        summary_trigger_messages=trigger_messages,
        summary_trigger_tokens=100000,
        max_message_chars=1000,
        lock_timeout_seconds=3,
        max_tool_rounds=2,
        max_tool_calls=3,
        tool_context_budget_tokens=256,
    )
    model = ModelProfile(
        name="fake",
        provider=provider,
        api_url="http://model.invalid/chat",
        model="fake-model",
        api_key="secret" if provider == "openai_compatible" else "",
        context_budget_tokens=2048,
        max_output_tokens=128,
        timeout=2,
        temperature=0.2,
        supports_tools=True,
    )
    return ChatSettings(
        server=server,
        models={"fake": model},
        assistants={"test": AssistantProfile("test", assistant, summary)},
        mcp=MCPSettings("http://legal.invalid/mcp", 2),
        config_path=root / "config.ini",
    )


def ollama_transport(captured: list[dict], summary_fails: bool = False,
                     delay: float = 0.0) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        if delay:
            await asyncio.sleep(delay)
        body = json.loads(request.content)
        captured.append({"body": body, "headers": dict(request.headers)})
        is_summary = body["messages"][0]["content"] == "PROMPT DE RESUMO"
        if is_summary and summary_fails:
            return httpx.Response(503, json={"error": "temporário"})
        text = "Resumo consolidado." if is_summary else "Resposta acolhedora."
        return httpx.Response(200, json={
            "model": "fake-model",
            "message": {"role": "assistant", "content": text},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 12,
            "eval_count": 4,
        })
    return httpx.MockTransport(handler)


class ConfigurationTests(unittest.TestCase):
    def test_terminal_text_recovers_surrogateescaped_utf8(self):
        broken = "informa\udcc3\udca7\udcc3\udca3o"
        self.assertEqual(_terminal_text(broken), "informação")
        self.assertEqual(_terminal_text("texto válido"), "texto válido")

    def test_loads_profiles_and_secret_only_from_named_environment_variable(self):
        with workspace_tempdir() as directory:
            root = Path(directory)
            (root / "assistant.md").write_text("a", encoding="utf-8")
            (root / "summary.md").write_text("s", encoding="utf-8")
            config = root / "chat.ini"
            config.write_text("""[CHAT_API]
DEFAULT_MODEL_PROFILE=external
DEFAULT_ASSISTANT_PROFILE=test
DATABASE_PATH=db.sqlite3
[MODEL.external]
PROVIDER=openai_compatible
API_URL=https://example.invalid/v1/chat/completions
MODEL=external-model
API_KEY_ENV=TEST_CHAT_KEY
CONTEXT_BUDGET_TOKENS=4096
MAX_OUTPUT_TOKENS=256
[ASSISTANT.test]
PROMPT_PATH=assistant.md
SUMMARY_PROMPT_PATH=summary.md
""", encoding="utf-8")
            with patch.dict(os.environ, {"TEST_CHAT_KEY": "top-secret"}, clear=False):
                settings = load_settings(config)
            self.assertEqual(settings.models["external"].api_key, "top-secret")
            self.assertNotIn("top-secret", json.dumps(settings.models["external"].public_dict()))
            self.assertEqual(settings.server.database_path, (root / "db.sqlite3").resolve())


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_ollama_payload_and_response(self):
        captured: list[dict] = []
        with workspace_tempdir() as directory:
            async with httpx.AsyncClient(transport=ollama_transport(captured)) as client:
                provider = OllamaProvider(make_settings(Path(directory)).models["fake"], client)
                result = await provider.generate(ChatRequest(
                    [{"role": "user", "content": "oi"}], 0.2, 64
                ))
        self.assertEqual(result.text, "Resposta acolhedora.")
        self.assertFalse(captured[0]["body"]["stream"])
        self.assertFalse(captured[0]["body"]["think"])
        self.assertEqual(captured[0]["body"]["options"]["num_predict"], 64)
        self.assertNotIn("authorization", captured[0]["headers"])

    async def test_openai_compatible_payload_response_and_bearer(self):
        captured = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append({"body": json.loads(request.content), "headers": dict(request.headers)})
            return httpx.Response(200, json={
                "id": "r1", "model": "returned-model",
                "choices": [{"message": {"content": "texto"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 2},
            })

        with workspace_tempdir() as directory:
            profile = make_settings(Path(directory), "openai_compatible").models["fake"]
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                result = await OpenAICompatibleProvider(profile, client).generate(
                    ChatRequest([{"role": "user", "content": "oi"}], 0.3, 50)
                )
        self.assertEqual(result.text, "texto")
        self.assertEqual(result.input_tokens, 10)
        self.assertEqual(captured[0]["headers"]["authorization"], "Bearer secret")
        self.assertEqual(captured[0]["body"]["max_tokens"], 50)

    async def test_ollama_sends_tools_and_normalizes_tool_calls(self):
        captured = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(200, json={
                "model": "fake-model", "done": True,
                "message": {"content": "", "tool_calls": [{
                    "function": {
                        "name": "legal_search_legal_sources",
                        "arguments": {"query": "violência patrimonial", "top_k": None},
                    },
                }]},
            })

        tools = [{"type": "function", "function": {
            "name": "legal_search_legal_sources", "parameters": {"type": "object"},
        }}]
        with workspace_tempdir() as directory:
            profile = make_settings(Path(directory)).models["fake"]
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                result = await OllamaProvider(profile, client).generate(
                    ChatRequest([{"role": "user", "content": "pergunta"}], 0.2, 64, tools)
                )
        self.assertEqual(captured[0]["tools"], tools)
        self.assertEqual(result.tool_calls[0].name, "legal_search_legal_sources")
        self.assertIsNone(result.tool_calls[0].arguments["top_k"])

    async def test_openai_normalizes_json_string_tool_arguments(self):
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "model": "fake-model",
                "choices": [{"finish_reason": "tool_calls", "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call-1", "type": "function",
                        "function": {
                            "name": "operations_request_human_handoff",
                            "arguments": '{"mode":"offer","reason":"explicit_human_request"}',
                        },
                    }],
                }}],
            })

        with workspace_tempdir() as directory:
            profile = make_settings(Path(directory), "openai_compatible").models["fake"]
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                result = await OpenAICompatibleProvider(profile, client).generate(
                    ChatRequest([{"role": "user", "content": "humano"}], 0.2, 64, [])
                )
        self.assertEqual(result.tool_calls[0].id, "call-1")
        self.assertEqual(result.tool_calls[0].arguments["mode"], "offer")

    async def test_invalid_provider_response_is_rejected(self):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"message": {}}))
        ) as client:
            with workspace_tempdir() as directory:
                provider = OllamaProvider(make_settings(Path(directory)).models["fake"], client)
                with self.assertRaises(ProviderBadResponseError):
                    await provider.generate(ChatRequest([], 0.1, 10))


class RepositoryTests(unittest.TestCase):
    def test_idempotency_reuses_message_and_rejects_different_content(self):
        with workspace_tempdir() as directory:
            repository = SQLiteConversationRepository(Path(directory) / "db.sqlite3")
            repository.initialize()
            conversation = Conversation("c1", "fake", "test", "v1", "now", "now", 1)
            repository.create_conversation(conversation)
            state, message, cached = repository.begin_turn("c1", "key", "texto")
            self.assertEqual(state, "started")
            self.assertIsNone(cached)
            state, repeated, _ = repository.begin_turn("c1", "key", "texto")
            self.assertEqual(state, "retry")
            self.assertEqual(repeated.id, message.id)
            with self.assertRaises(ConflictError):
                repository.begin_turn("c1", "key", "outro texto")

    def test_failed_old_turn_cannot_be_retried_after_new_messages(self):
        with workspace_tempdir() as directory:
            repository = SQLiteConversationRepository(Path(directory) / "db.sqlite3")
            repository.initialize()
            repository.create_conversation(
                Conversation("c1", "fake", "test", "v1", "now", "now", 1)
            )
            _, first, _ = repository.begin_turn("c1", "old", "primeira")
            repository.fail_turn("c1", "old", {
                "conversation_id": "c1", "user_message_id": first.id,
                "purpose": "response", "provider": "ollama", "model": "fake",
                "latency_ms": None, "input_tokens": None, "output_tokens": None,
                "status": "failed", "error_code": "timeout", "created_at": "now",
            })
            repository.begin_turn("c1", "new", "segunda")
            with self.assertRaises(ConflictError):
                repository.begin_turn("c1", "old", "primeira")


class APITests(unittest.TestCase):
    def test_full_flow_persists_restarts_is_idempotent_and_deletes(self):
        with workspace_tempdir() as directory:
            root = Path(directory)
            settings = make_settings(root)
            captured: list[dict] = []
            app = create_app(settings=settings, http_transport=ollama_transport(captured),
                             tool_catalog=EmptyToolCatalog())
            client_id = str(uuid4())
            with TestClient(app) as client:
                created = client.post("/v1/conversations", json={}).json()
                conversation_id = created["id"]
                body = {"client_message_id": client_id, "content": "quero conversar"}
                first = client.post(
                    f"/v1/conversations/{conversation_id}/messages", json=body
                )
                self.assertEqual(first.status_code, 200)
                repeated = client.post(
                    f"/v1/conversations/{conversation_id}/messages", json=body
                )
                self.assertEqual(repeated.json(), first.json())
                self.assertEqual(len(captured), 1)

            restarted = create_app(settings=settings, http_transport=ollama_transport(captured),
                                   tool_catalog=EmptyToolCatalog())
            with TestClient(restarted) as client:
                stored = client.get(f"/v1/conversations/{conversation_id}").json()
                self.assertEqual([item["role"] for item in stored["messages"]],
                                 ["user", "assistant"])
                self.assertEqual(client.delete(
                    f"/v1/conversations/{conversation_id}"
                ).status_code, 204)
                self.assertEqual(client.get(
                    f"/v1/conversations/{conversation_id}"
                ).status_code, 404)

    def test_summary_is_created_and_failed_summary_falls_back(self):
        for should_fail in (False, True):
            with self.subTest(summary_fails=should_fail), workspace_tempdir() as directory:
                root = Path(directory)
                settings = make_settings(root, trigger_messages=2, recent_messages=2)
                captured: list[dict] = []
                app = create_app(
                    settings=settings,
                    http_transport=ollama_transport(captured, summary_fails=should_fail),
                    tool_catalog=EmptyToolCatalog(),
                )
                with TestClient(app) as client:
                    conversation_id = client.post("/v1/conversations", json={
                        "memory_profile": "summary-window-v1"
                    }).json()["id"]
                    for text in ("primeira", "segunda"):
                        response = client.post(
                            f"/v1/conversations/{conversation_id}/messages",
                            json={"client_message_id": str(uuid4()), "content": text},
                        )
                    self.assertEqual(response.status_code, 200)
                    expected = "summary_failed_recent_only" if should_fail else "complete"
                    self.assertEqual(response.json()["context"]["status"], expected)
                    stored = client.get(f"/v1/conversations/{conversation_id}").json()
                    self.assertEqual(stored["summary"] is None, should_fail)
                    if not should_fail:
                        self.assertEqual(stored["summary"]["content"], "Resumo consolidado.")
                        self.assertLess(stored["summary"]["through_sequence"],
                                        stored["messages"][-1]["sequence"])

    def test_two_concurrent_messages_are_serialized(self):
        with workspace_tempdir() as directory:
            settings = make_settings(Path(directory))
            app = create_app(settings=settings, http_transport=ollama_transport([], delay=0.03),
                             tool_catalog=EmptyToolCatalog())
            with TestClient(app) as client:
                conversation_id = client.post("/v1/conversations", json={}).json()["id"]

                def send(text: str):
                    return client.post(
                        f"/v1/conversations/{conversation_id}/messages",
                        json={"client_message_id": str(uuid4()), "content": text},
                    )

                with ThreadPoolExecutor(max_workers=2) as executor:
                    responses = list(executor.map(send, ["um", "dois"]))
                self.assertTrue(all(response.status_code == 200 for response in responses))
                self.assertEqual({response.json()["turn"] for response in responses}, {1, 2})
                stored = client.get(f"/v1/conversations/{conversation_id}").json()
                self.assertEqual([item["sequence"] for item in stored["messages"]], [1, 2, 3, 4])
                self.assertEqual([item["role"] for item in stored["messages"]],
                                 ["user", "assistant", "user", "assistant"])


if __name__ == "__main__":
    unittest.main()
