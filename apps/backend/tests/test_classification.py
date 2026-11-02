from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import asynccontextmanager, contextmanager
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from notas_ia.app import create_app
from notas_ia.classification.context import ClassificationContextBuilder
from notas_ia.classification.service import SystemOneClassifier, validate_llm_result
from notas_ia.config import ClassificationSettings, ClassifierProfile
from notas_ia.errors import ProviderBadResponseError

from test_chat_api import EmptyToolCatalog, make_settings


@contextmanager
def workspace_tempdir():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        yield Path(directory)


def classification_transport(captured: list[dict]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured.append(body)
        messages = body["messages"]
        if "Você classifica indícios textuais" in messages[0]["content"]:
            state = json.loads(messages[-1]["content"])
            current = state["messages"][-1]
            if current["content"] == "INVALID":
                content = "não é JSON"
            else:
                content = json.dumps({
                    "violence_types": [{"label": "psicologica", "confidence": 0.8}],
                    "intent": {"label": "relato", "confidence": 0.75},
                    "urgency": {"label": "prioritaria", "confidence": 0.7},
                    "evidence": [{"dimension": "violence_type", "label": "psicologica",
                                  "message_id": current["message_id"], "quote": "ameaçou"}],
                    "audit_note": "Relato com possível ameaça.",
                }, ensure_ascii=False)
        else:
            content = "Resposta acolhedora."
        return httpx.Response(200, json={
            "model": "fake-model", "done": True, "message": {"content": content},
            "prompt_eval_count": 10, "eval_count": 2,
        })
    return httpx.MockTransport(handler)


def classified_settings(root: Path, mode: str):
    base = make_settings(root)
    profile = ClassifierProfile("fake-classifier", "llm", model_profile="fake")
    return replace(
        base,
        classifiers={"fake-classifier": profile},
        classification=ClassificationSettings(
            mode=mode, online_classifiers=("fake-classifier",),
            agent_context_classifier="fake-classifier" if mode == "agent_context" else None,
        ),
    )


class ClassificationValidationTests(unittest.TestCase):
    def test_snapshot_contains_only_user_declarations(self):
        from notas_ia.domain.models import Message
        history = [
            Message("u1", "c1", 1, "user", "SOCORRO", "accepted", "now"),
            Message("a1", "c1", 2, "assistant", "Ligue para a Polícia Militar pelo 190.", "complete", "now"),
            Message("u2", "c1", 3, "user", "Era apenas um teste.", "accepted", "now"),
            Message("a2", "c1", 4, "assistant", "Entendi.", "complete", "now"),
            Message("u3", "c1", 5, "user", "Meu marido me matou de rir ontem.", "accepted", "now"),
        ]
        snapshot = ClassificationContextBuilder(6).build("v1", history, None)
        assert [item["message_id"] for item in snapshot.payload["messages"]] == ["u1", "u2", "u3"]
        assert "190" not in snapshot.canonical_json

    def test_rejects_non_literal_evidence(self):
        from notas_ia.domain.models import Message
        snapshot = ClassificationContextBuilder(1).build("v1", [Message(
            "m1", "c1", 1, "user", "texto sem ameaça", "accepted", "now"
        )], None)
        payload = {
            "violence_types": [{"label": "psicologica", "confidence": 0.5}],
            "intent": {"label": "relato", "confidence": 0.5},
            "urgency": {"label": "indeterminada", "confidence": 0.5},
            "evidence": [{"dimension": "violence_type", "label": "psicologica",
                          "message_id": "m1", "quote": "ameaçou"}], "audit_note": "",
        }
        with self.assertRaises(ProviderBadResponseError):
            validate_llm_result("p", "m", json.dumps(payload), 1, None, None, snapshot)

    def test_rejects_out_of_range_confidence(self):
        from notas_ia.domain.models import Message
        snapshot = ClassificationContextBuilder(1).build("v1", [Message(
            "m1", "c1", 1, "user", "teste", "accepted", "now"
        )], None)
        payload = {
            "violence_types": [], "intent": {"label": "outro", "confidence": 2},
            "urgency": {"label": "indeterminada", "confidence": 0.5},
            "evidence": [], "audit_note": "",
        }
        with self.assertRaises(ProviderBadResponseError):
            validate_llm_result("p", "m", json.dumps(payload), 1, None, None, snapshot)


class SystemOneTests(unittest.IsolatedAsyncioTestCase):
    async def test_maps_typed_answers_without_inventing_evidence(self):
        from notas_ia.domain.models import Message
        snapshot = ClassificationContextBuilder(1).build("v1", [Message(
            "m1", "c1", 1, "user", "texto", "accepted", "now"
        )], None)
        answers = {
            f"type_{label}": {"noul": 0.8 if label == "psicologica" else 0.1}
            for label in ("fisica", "psicologica", "sexual", "patrimonial", "moral", "vicaria")
        }
        answers.update({
            "intent": {"choice": "relato", "confidence": 0.7},
            "urgency": {"choice": "prioritaria", "confidence": 0.6},
        })
        captured = []
        def handler(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200, json={"model": "kev", "answers": answers})
        profile = ClassifierProfile("kev", "system_one", api_url="http://kev.invalid/v1/systemone")
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await SystemOneClassifier(profile, client).classify(snapshot)
        self.assertEqual(result.violence_types[0]["label"], "psicologica")
        self.assertEqual(result.evidence, [])
        self.assertEqual(captured[0]["questions"]["urgency"]["type"], "choice")


class ClassificationModeTests(unittest.TestCase):
    def test_disabled_does_not_call_classifier_or_expose_artifacts(self):
        with workspace_tempdir() as root:
            captured: list[dict] = []
            app = create_app(settings=make_settings(root),
                             http_transport=classification_transport(captured),
                             tool_catalog=EmptyToolCatalog())
            with TestClient(app) as client:
                conversation_id = client.post("/v1/conversations", json={}).json()["id"]
                response = client.post(f"/v1/conversations/{conversation_id}/messages", json={
                    "client_message_id": str(uuid4()), "content": "ele ameaçou"
                })
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("classifications", response.json())
                self.assertEqual(len(captured), 1)

    def test_shadow_persists_without_modifying_agent_prompt(self):
        with workspace_tempdir() as root:
            captured: list[dict] = []
            app = create_app(settings=classified_settings(root, "shadow"),
                             http_transport=classification_transport(captured),
                             tool_catalog=EmptyToolCatalog())
            with TestClient(app) as client:
                conversation_id = client.post("/v1/conversations", json={}).json()["id"]
                response = client.post(f"/v1/conversations/{conversation_id}/messages", json={
                    "client_message_id": str(uuid4()), "content": "ele ameaçou"
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["classifications"][0]["status"], "completed")
                self.assertEqual(response.json()["classifications"][0]["input_tokens"], 10)
                self.assertEqual(response.json()["classifications"][0]["output_tokens"], 2)
                self.assertIsInstance(response.json()["classifications"][0]["latency_ms"], int)
                self.assertEqual(len(captured), 2)
                agent_prompt = captured[-1]["messages"]
                self.assertFalse(any("Hipótese classificatória" in item["content"] for item in agent_prompt))
                latest = client.get(
                    f"/v1/conversations/{conversation_id}/classifications/latest"
                ).json()
                self.assertEqual(len(latest["items"]), 1)

    def test_classifier_failure_does_not_fail_the_conversation(self):
        with workspace_tempdir() as root:
            app = create_app(settings=classified_settings(root, "shadow"),
                             http_transport=classification_transport([]),
                             tool_catalog=EmptyToolCatalog())
            with TestClient(app) as client:
                conversation_id = client.post("/v1/conversations", json={}).json()["id"]
                response = client.post(f"/v1/conversations/{conversation_id}/messages", json={
                    "client_message_id": str(uuid4()), "content": "INVALID"
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["classifications"][0]["status"], "failed")

    def test_agent_context_injects_only_compact_hypothesis(self):
        with workspace_tempdir() as root:
            captured: list[dict] = []
            app = create_app(settings=classified_settings(root, "agent_context"),
                             http_transport=classification_transport(captured),
                             tool_catalog=EmptyToolCatalog())
            with TestClient(app) as client:
                conversation_id = client.post("/v1/conversations", json={}).json()["id"]
                response = client.post(f"/v1/conversations/{conversation_id}/messages", json={
                    "client_message_id": str(uuid4()), "content": "ele ameaçou"
                })
                self.assertEqual(response.status_code, 200)
            agent_prompt = captured[-1]["messages"]
            hypothesis = [item["content"] for item in agent_prompt
                          if "Hipótese classificatória" in item["content"]]
            self.assertEqual(len(hypothesis), 1)
            self.assertIn('"confidence": 0.8', hypothesis[0])
            self.assertIn("Relato com possível ameaça", hypothesis[0])


if __name__ == "__main__":
    unittest.main()
