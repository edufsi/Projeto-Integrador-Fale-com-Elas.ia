from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx

from .artifacts import append_jsonl, audit_payload, read_jsonl, render_html, render_markdown, write_json
from .datasets import DatasetBundle, EvaluationEpisode, load_suites, validate_bundles
from .metrics import build_report, observed_action
from .presets import PRESETS, EvaluationPreset


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dataset_fingerprint(bundles: list[DatasetBundle]) -> str:
    value = {item.suite: item.sha256 for item in bundles}
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class LiveBackendClient:
    """Small HTTP client kept outside the domain so evaluation exercises the public API."""

    def __init__(self, base_url: str, timeout: float):
        self.client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def get(self, path: str) -> dict:
        response = self.client.get(path)
        response.raise_for_status()
        return response.json()

    def create_conversation(self, model_profile: str, assistant_profile: str | None,
                            memory_profile: str) -> dict:
        response = self.client.post("/v1/conversations", json={
            "model_profile": model_profile, "assistant_profile": assistant_profile,
            "memory_profile": memory_profile,
        })
        response.raise_for_status()
        return response.json()

    def send(self, conversation_id: str, content: str) -> tuple[dict, int]:
        started = time.perf_counter()
        response = self.client.post(f"/v1/conversations/{conversation_id}/messages", json={
            "client_message_id": str(uuid4()), "content": content,
        })
        response.raise_for_status()
        return response.json(), round((time.perf_counter() - started) * 1000)


def preflight(client: LiveBackendClient, preset: EvaluationPreset) -> dict:
    """Fail before writing a run if the live backend differs from its requested preset."""
    ready = client.get("/health/ready")
    version = client.get("/version")
    classifiers = client.get("/v1/classifier-profiles")
    models = client.get("/v1/model-profiles")
    known_models = {item["name"] for item in models.get("items", [])}
    if preset.model_profile not in known_models:
        raise RuntimeError(f"Backend não oferece o modelo exigido por {preset.name}: {preset.model_profile}")
    if classifiers.get("mode") != preset.classification_mode:
        raise RuntimeError(
            f"Preset {preset.name} exige classificação {preset.classification_mode}, "
            f"mas o backend está em {classifiers.get('mode')}"
        )
    if tuple(classifiers.get("online_classifiers", [])) != preset.online_classifiers:
        raise RuntimeError(
            f"Preset {preset.name} exige classificadores {preset.online_classifiers}, "
            f"mas o backend expõe {classifiers.get('online_classifiers', [])}"
        )
    if classifiers.get("agent_context_classifier") != preset.agent_context_classifier:
        raise RuntimeError("O classificador de contexto do backend não corresponde ao preset")
    return {"ready": ready, "version": version, "classifiers": classifiers, "models": models}


def _record(episode: EvaluationEpisode, turn, history: list[str], response: dict,
            round_trip_ms: int, conversation: dict) -> dict:
    return {
        "schema_version": "evaluation-turn-record.v1",
        "record_id": f"{episode.suite}:{turn.id}", "episode_id": episode.id,
        "suite": episode.suite, "review_status": episode.review_status,
        "history": history, "message": turn.message, "expected": turn.expected,
        "response_rubric": turn.response_rubric, "response": response,
        "round_trip_ms": round_trip_ms, "observed_action": observed_action(response),
        "conversation": {key: conversation.get(key) for key in (
            "id", "model_profile", "assistant_profile", "memory_profile", "prompt_version"
        )}, "recorded_at": _now(),
    }


def _run_episode(client: LiveBackendClient, episode: EvaluationEpisode, preset: EvaluationPreset,
                 assistant_profile: str | None, memory_profile: str) -> list[dict]:
    conversation = client.create_conversation(preset.model_profile, assistant_profile, memory_profile)
    history: list[str] = []
    for message in episode.seed_history:
        client.send(conversation["id"], message)
        history.append(message)
    records = []
    for turn in episode.turns:
        response, elapsed = client.send(conversation["id"], turn.message)
        records.append(_record(episode, turn, list(history), response, elapsed, conversation))
        history.append(turn.message)
    return records


def _write_outputs(output: Path, manifest: dict, records: list[dict], blocked: list[dict]) -> dict:
    report = build_report(records, blocked)
    audit = audit_payload(records)
    write_json(output / "manifest.json", manifest)
    write_json(output / "report.json", report)
    (output / "report.md").write_text(render_markdown(report, manifest), encoding="utf-8")
    write_json(output / "audit.json", audit)
    (output / "audit.html").write_text(
        render_html(audit, f"Auditoria — {manifest['run_id']}"), encoding="utf-8"
    )
    return report


def run_evaluation(base_url: str, preset_name: str, suites: list[str], output: Path,
                   archive: str | None = None, assistant_profile: str | None = None,
                   memory_profile: str = "recent-window-v1", timeout: float = 240,
                   resume: bool = False) -> dict:
    if preset_name not in PRESETS:
        raise ValueError(f"Preset desconhecido: {preset_name}")
    preset = PRESETS[preset_name]
    bundles = load_suites(suites, archive)
    validate_bundles(bundles)
    blocked = [{"suite": item.suite, "review_status": item.review_status,
                "reason": item.block_reason} for item in bundles if not item.runnable]
    runnable = [item for item in bundles if item.runnable]
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    records_path = output / "records.jsonl"
    previous = read_jsonl(records_path) if resume else []
    if records_path.exists() and not resume:
        raise FileExistsError("Diretório já contém records.jsonl; use --resume ou outro --output")
    expected_turns = {
        episode.id: len(episode.turns) for bundle in runnable for episode in bundle.episodes
    }
    completed_counts = {}
    for item in previous:
        if item.get("schema_version") == "evaluation-turn-record.v1":
            completed_counts[item["episode_id"]] = completed_counts.get(item["episode_id"], 0) + 1
    # Resume only complete episodes. Replaying a partial episode is intentional: it
    # recreates its conversation state and avoids silently scoring later turns without
    # their original history.
    completed_episodes = {
        episode_id for episode_id, count in completed_counts.items()
        if count >= expected_turns.get(episode_id, count + 1)
    }
    client = LiveBackendClient(base_url, timeout)
    try:
        state = preflight(client, preset)
        manifest = {
            "schema_version": "evaluation-run.v1", "run_id": output.name,
            "created_at": _now(), "base_url": base_url, "preset": preset.name,
            "requested": {"model_profile": preset.model_profile,
                          "classification_mode": preset.classification_mode,
                          "online_classifiers": list(preset.online_classifiers),
                          "agent_context_classifier": preset.agent_context_classifier,
                          "assistant_profile": assistant_profile,
                          "memory_profile": memory_profile},
            "backend": state,
            "datasets": [{"suite": item.suite, "review_status": item.review_status,
                          "sha256": item.sha256, "source": str(item.source_path),
                          "runnable": item.runnable} for item in bundles],
            "dataset_fingerprint": _dataset_fingerprint(bundles),
            "classification_context_contract": (
                "agent_context recebe somente hipótese compacta validada após a persona e "
                "antes do resumo/histórico; shadow não altera o prompt."
            ),
        }
        for bundle in runnable:
            for episode in bundle.episodes:
                if episode.id in completed_episodes:
                    continue
                try:
                    results = _run_episode(client, episode, preset, assistant_profile, memory_profile)
                    for result in results:
                        append_jsonl(records_path, result)
                except Exception as exc:
                    append_jsonl(records_path, {
                        "schema_version": "evaluation-episode-error.v1", "episode_id": episode.id,
                        "suite": bundle.suite, "review_status": bundle.review_status,
                        "error_type": type(exc).__name__, "error": str(exc), "recorded_at": _now(),
                    })
        all_rows = read_jsonl(records_path)
        records = [row for row in all_rows if row.get("schema_version") == "evaluation-turn-record.v1"]
        # Profiles state intent; these values record what providers actually reported
        # during this run, which is essential when aliases or server defaults change.
        manifest["observed_models"] = sorted({
            str(row.get("response", {}).get("model", {}).get("model"))
            for row in records if row.get("response", {}).get("model", {}).get("model")
        })
        manifest["prompt_versions"] = sorted({
            str(row.get("conversation", {}).get("prompt_version"))
            for row in records if row.get("conversation", {}).get("prompt_version")
        })
        manifest["completed_at"] = _now()
        manifest["records"] = len(records)
        manifest["episode_errors"] = len(all_rows) - len(records)
        report = _write_outputs(output, manifest, records, blocked)
        return {"manifest": manifest, "report": report, "output": str(output)}
    finally:
        client.close()


def compare_runs(paths: list[Path]) -> dict:
    loaded = []
    for path in paths:
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        report = json.loads((path / "report.json").read_text(encoding="utf-8"))
        loaded.append((path, manifest, report))
    fingerprints = {manifest["dataset_fingerprint"] for _, manifest, _ in loaded}
    if len(fingerprints) != 1:
        raise ValueError("As rodadas usam corpus diferente; compare apenas hashes idênticos")
    return {
        "schema_version": "evaluation-comparison.v1", "dataset_fingerprint": fingerprints.pop(),
        "runs": [{"path": str(path), "preset": manifest["preset"],
                  "by_review_status": report["by_review_status"]}
                 for path, manifest, report in loaded],
    }
