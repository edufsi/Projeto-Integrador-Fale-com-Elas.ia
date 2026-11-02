from __future__ import annotations

from pathlib import Path

from notas_ia.evaluation.artifacts import audit_payload, preserve_human_audit, render_html
from notas_ia.evaluation.datasets import load_suites, validate_bundles
from notas_ia.evaluation.metrics import build_report
from notas_ia.evaluation.presets import PRESETS
from notas_ia.evaluation import runner


def test_datasets_follow_source_files_without_fixed_cardinality():
    root = Path(__file__).parents[3] / "data" / "archive" / "evaluation-corpus"
    bundles = {item.suite: item for item in load_suites(["all"], root)}
    assert bundles["exploratory"].episodes
    assert bundles["gold_draft"].episodes
    assert bundles["safety"].review_status == "code_regression"
    assert bundles["emergency"].runnable is True
    assert bundles["emergency"].review_status == "draft_pending_specialist_review"
    assert bundles["emergency"].episodes
    validate_bundles(list(bundles.values()))


def test_presets_cover_prompt_influencing_modes():
    assert PRESETS["qwen-only"].classification_mode == "disabled"
    assert PRESETS["qwen-qwen-shadow"].classification_mode == "shadow"
    assert PRESETS["qwen-qwen-context"].agent_context_classifier == "local-qwen4"
    assert PRESETS["qwen-kev-context"].agent_context_classifier == "kev4b"
    assert PRESETS["llama8-qwen-shadow"].model_profile == "local-llama8"
    assert PRESETS["llama8-llama8-shadow"].online_classifiers == ("local-llama8",)
    assert PRESETS["llama8-kev-shadow"].online_classifiers == ("kev4b",)


def test_report_and_audit_keep_human_review_separate():
    record = {
        "record_id": "exploratory:case", "episode_id": "case", "suite": "exploratory",
        "review_status": "single_reviewed", "history": [], "message": "socorro",
        "expected": {"types": {"fisica": False, "psicologica": False, "sexual": False,
                                 "patrimonial": False, "moral": False, "vicaria": False},
                     "intencao": "ajuda_urgente", "urgencia": "imediata",
                     "acao_esperada": "transbordar_imediatamente"},
        "response_rubric": {}, "round_trip_ms": 10, "observed_action": "immediate_handoff",
        "response": {"assistant_message": {"content": "Resposta controlada."},
                     "usage": {"latency_ms": 5, "input_tokens": 2, "output_tokens": 1},
                     "handoff": {"mode": "immediate"}, "agent": {"tools_used": [], "tool_executions": []},
                     "classifications": []},
    }
    report = build_report([record], [])
    assert report["by_review_status"]["single_reviewed"]["agent"]["immediate"]["tp"] == 1
    audit = audit_payload([record])
    assert audit["items"][0]["auditoria_humana"]["status"] == "pendente"
    retained = preserve_human_audit(audit, {"items": [{
        "record_id": "exploratory:case",
        "auditoria_humana": {"status": "revisado", "comentario": "parece adequada"},
    }]})
    assert retained["items"][0]["auditoria_humana"]["status"] == "revisado"
    assert "Auditoria" in render_html(audit, "Auditoria")


def test_runner_replays_real_public_contract_with_fake_backend(monkeypatch, tmp_path):
    """The executor talks only to the HTTP client boundary, never internal services.

    Replacing that boundary verifies conversation creation, ordered replay and the
    durable artifacts without a model, a network service or SQLite implementation.
    """
    class FakeBackend:
        def __init__(self, base_url, timeout):
            self.sent = []

        def close(self):
            pass

        def get(self, path):
            responses = {
                "/health/ready": {"status": "ok"},
                "/version": {"version": "test"},
                "/v1/classifier-profiles": {
                    "mode": "disabled", "online_classifiers": [],
                    "agent_context_classifier": None, "items": [],
                },
                "/v1/model-profiles": {"items": [{"name": "local-qwen"}]},
            }
            return responses[path]

        def create_conversation(self, model_profile, assistant_profile, memory_profile):
            return {"id": f"conversation-{len(self.sent)}", "model_profile": model_profile,
                    "assistant_profile": assistant_profile, "memory_profile": memory_profile,
                    "prompt_version": "test-v1"}

        def send(self, conversation_id, content):
            self.sent.append((conversation_id, content))
            return {
                "assistant_message": {"content": "Resposta de teste."},
                "usage": {"latency_ms": 2, "input_tokens": 3, "output_tokens": 2},
                "agent": {"tools_used": [], "tool_executions": [], "stop_reason": "final"},
                "handoff": None, "classifications": [], "sources": [],
                "context": {"memory_profile": "recent-window-v1"},
            }, 4

    monkeypatch.setattr(runner, "LiveBackendClient", FakeBackend)
    root = Path(__file__).parents[3] / "data" / "archive" / "evaluation-corpus"
    outcome = runner.run_evaluation(
        "http://fake", "qwen-only", ["safety"], tmp_path / "run", str(root), timeout=1,
    )
    records = (tmp_path / "run" / "records.jsonl").read_text(encoding="utf-8").splitlines()
    expected = sum(len(item.turns) for item in load_suites(["safety"], root)[0].episodes)
    assert outcome["manifest"]["records"] == expected
    assert len(records) == expected
    assert (tmp_path / "run" / "audit.html").exists()
