from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..classification.ontology import VIOLENCE_TYPES


@dataclass(frozen=True)
class EvaluationTurn:
    id: str
    message: str
    expected: dict[str, Any]
    response_rubric: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationEpisode:
    id: str
    suite: str
    review_status: str
    seed_history: tuple[str, ...]
    turns: tuple[EvaluationTurn, ...]


@dataclass(frozen=True)
class DatasetBundle:
    suite: str
    review_status: str
    episodes: tuple[EvaluationEpisode, ...]
    source_path: Path | None
    sha256: str
    runnable: bool = True
    block_reason: str | None = None


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    return json.loads(raw), _sha(raw)


def archive_root(value: str | Path | None = None) -> Path:
    if value:
        return Path(value).resolve()
    mounted = Path("/data/archive/evaluation-corpus")
    if mounted.exists():
        return mounted
    return Path(__file__).resolve().parents[5] / "data" / "archive" / "evaluation-corpus"


def _types(value: dict[str, Any] | list[str] | None) -> dict[str, bool]:
    if isinstance(value, list):
        return {label: label in value for label in VIOLENCE_TYPES}
    return {label: bool((value or {}).get(label, False)) for label in VIOLENCE_TYPES}


def _expected(item: dict[str, Any], labels: dict[str, Any] | None = None) -> dict[str, Any]:
    source = labels or item
    types = source.get("tipos_com_indicio", source.get("tipos", item.get("types")))
    return {
        "types": _types(types),
        "intencao": source.get("intencao"),
        "urgencia": source.get("urgencia"),
        "acao_esperada": item.get("acao_esperada"),
        "evidencias": item.get("evidencias_revisao_humana", item.get("evidencias", [])),
    }


def load_exploratory(root: Path) -> DatasetBundle:
    path = root / "benchmark_exploratorio.json"
    data, digest = _read_json(path)
    episodes = []
    for item in data["itens"]:
        turn = EvaluationTurn(item["id"], item["mensagem_usuario"], _expected(item))
        episodes.append(EvaluationEpisode(
            item["id"], "exploratory", "single_reviewed",
            tuple(item.get("historico_visivel", [])), (turn,),
        ))
    return DatasetBundle("exploratory", "single_reviewed", tuple(episodes), path, digest)


def load_gold_draft(root: Path) -> DatasetBundle:
    path = root / "gold_conversations.draft.json"
    data, digest = _read_json(path)
    episodes = []
    for conversation in data["conversas"]:
        turns = []
        for item in conversation["turnos"]:
            expected = _expected(item, item.get("rotulos"))
            turns.append(EvaluationTurn(
                f"{conversation['id']}:T{item['turno']}", item["mensagem_usuario"], expected,
                item.get("rubrica_resposta", {}),
            ))
        episodes.append(EvaluationEpisode(
            conversation["id"], "gold_draft", "draft_pending_calibration", (), tuple(turns)
        ))
    return DatasetBundle("gold_draft", "draft_pending_calibration", tuple(episodes), path, digest)


def load_safety() -> DatasetBundle:
    path = Path(__file__).parent / "fixtures" / "safety-regressions.v1.json"
    data, digest = _read_json(path)
    episodes = []
    for item in data["episodes"]:
        messages = item["messages"]
        turns = []
        for index, message in enumerate(messages, 1):
            expected = item["expected"] if index == len(messages) else {
                "types": {label: False for label in VIOLENCE_TYPES},
                "intencao": "ajuda_urgente" if message.casefold() == "socorro" else "outro",
                "urgencia": "indeterminada", "acao_esperada": None, "evidencias": [],
            }
            if isinstance(expected.get("types"), list):
                expected = {**expected, "types": _types(expected["types"])}
            turns.append(EvaluationTurn(f"{item['id']}:T{index}", message, expected))
        episodes.append(EvaluationEpisode(
            item["id"], "safety", "code_regression", (), tuple(turns)
        ))
    return DatasetBundle("safety", "code_regression", tuple(episodes), path, digest)


def load_emergency_inventory(root: Path) -> DatasetBundle:
    """Load every currently executable emergency scenario from its source file.

    The source is intentionally allowed to grow. A scenario is blocked only when it
    has no usable turns, rather than because it does not match a historical target
    count such as 40 pairs or 80 messages.
    """
    path = root / "emergency.draft.json"
    data, digest = _read_json(path)
    episodes = []
    for pair in data.get("pares", []):
        for scenario in pair.get("cenarios", []):
            raw_turns = [item for item in scenario.get("turnos", []) if isinstance(item, dict)]
            if not raw_turns:
                continue
            turns = tuple(
                EvaluationTurn(
                    f"{scenario['id']}:T{item.get('turno', index)}",
                    item["mensagem_usuario"],
                    _expected(item, item.get("rotulos")),
                    item.get("rubrica_resposta", {}),
                )
                for index, item in enumerate(raw_turns, 1)
            )
            seed = tuple(raw_turns[0].get("historico_visivel", []))
            episodes.append(EvaluationEpisode(
                scenario["id"], "emergency", "draft_pending_specialist_review", seed, turns
            ))
    if episodes:
        return DatasetBundle(
            "emergency", "draft_pending_specialist_review", tuple(episodes), path, digest
        )
    return DatasetBundle(
        "emergency", "blocked_incomplete", (), path, digest, runnable=False,
        block_reason="Nenhum cenário de emergência possui turno executável.",
    )


def load_suites(names: list[str], root: str | Path | None = None) -> list[DatasetBundle]:
    base = archive_root(root)
    loaders = {
        "exploratory": lambda: load_exploratory(base),
        "gold_draft": lambda: load_gold_draft(base),
        "safety": load_safety,
        "emergency": lambda: load_emergency_inventory(base),
    }
    selected = list(loaders) if "all" in names else names
    unknown = sorted(set(selected) - set(loaders))
    if unknown:
        raise ValueError(f"Suite desconhecida: {', '.join(unknown)}")
    return [loaders[name]() for name in selected]


def validate_bundles(bundles: list[DatasetBundle]) -> None:
    """Validate shape, not corpus size or semantic quality.

    Files are the source of truth: users may add cases without touching Python.
    Review status remains a reporting property, not an admission criterion.
    """
    episode_ids: set[str] = set()
    turn_ids: set[str] = set()
    for bundle in bundles:
        if not bundle.runnable:
            continue
        for episode in bundle.episodes:
            if not episode.id or episode.id in episode_ids:
                raise ValueError(f"ID de cenário ausente ou duplicado: {episode.id!r}")
            episode_ids.add(episode.id)
            if not episode.turns:
                raise ValueError(f"Cenário executável sem turnos: {episode.id}")
            for turn in episode.turns:
                if not turn.id or turn.id in turn_ids:
                    raise ValueError(f"ID de turno ausente ou duplicado: {turn.id!r}")
                turn_ids.add(turn.id)
                if not turn.message.strip():
                    raise ValueError(f"Mensagem vazia no turno {turn.id}")
                if set(turn.expected.get("types", {})) != set(VIOLENCE_TYPES):
                    raise ValueError(f"Tipos incompletos no turno {turn.id}")
