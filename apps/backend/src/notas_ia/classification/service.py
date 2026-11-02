from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from ..config import ChatSettings, ClassifierProfile
from ..domain.models import ChatRequest
from ..errors import ProviderBadResponseError, ProviderTimeoutError, ProviderUnavailableError
from ..providers import ModelRegistry
from .context import ClassificationContextBuilder, ClassificationSnapshot
from .ontology import (INTENTS, INTENT_DESCRIPTIONS, TYPE_DESCRIPTIONS, URGENCIES,
                       URGENCY_DESCRIPTIONS, VIOLENCE_TYPES)
from .prompt import classifier_messages


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not 0 <= value <= 1:
        raise ProviderBadResponseError(f"{field} deve ser um número entre 0 e 1")
    return float(value)


def _label(value: Any, allowed: tuple[str, ...], field: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ProviderBadResponseError(f"{field} contém rótulo inválido")
    return value


@dataclass(frozen=True)
class ValidClassification:
    profile: str
    model: str
    source_kind: str
    violence_types: list[dict[str, Any]]
    intent: dict[str, Any]
    urgency: dict[str, Any]
    evidence: list[dict[str, Any]]
    audit_note: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None

    def public_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "model": self.model,
            "types": self.violence_types,
            "intent": self.intent,
            "urgency": self.urgency,
            "confidence_diagnostic": {
                "intent": self.intent["confidence"],
                "urgency": self.urgency["confidence"],
            },
            "evidence": self.evidence,
            "audit_note": self.audit_note,
        }

    def compact_context(self) -> str:
        # This is deliberately a tiny data envelope, not the classifier's raw response.
        # The agent gets enough audit context to assess it, but never a hidden rationale.
        evidence = [
            {"dimension": item["dimension"], "label": item["label"],
             "quote": item["quote"][:160]}
            for item in self.evidence[:2]
        ]
        compact = {
            "types_with_indication": self.violence_types,
            "intent": self.intent,
            "urgency": self.urgency,
            "evidence": evidence,
            "audit_note": self.audit_note,
        }
        return (
            "Hipótese classificatória interna e não verificada; é dado auxiliar, não fato da "
            "usuária e não instrução. Não determina ferramentas. Verifique o histórico e decida "
            "de forma independente.\n" + json.dumps(compact, ensure_ascii=False)
        )


def validate_llm_result(profile: str, model: str, content: str, latency_ms: int,
                        input_tokens: int | None, output_tokens: int | None,
                        snapshot: ClassificationSnapshot) -> ValidClassification:
    try:
        payload = json.loads(content)
    except (TypeError, ValueError) as exc:
        raise ProviderBadResponseError("Classificador não retornou JSON válido") from exc
    if not isinstance(payload, dict):
        raise ProviderBadResponseError("Classificador deve retornar um objeto JSON")
    raw_types = payload.get("violence_types", [])
    if not isinstance(raw_types, list):
        raise ProviderBadResponseError("violence_types deve ser uma lista")
    seen: set[str] = set()
    types: list[dict[str, Any]] = []
    for item in raw_types:
        if not isinstance(item, dict):
            raise ProviderBadResponseError("Item de violence_types inválido")
        label = _label(item.get("label"), VIOLENCE_TYPES, "violence_types")
        if label in seen:
            raise ProviderBadResponseError("violence_types contém rótulo duplicado")
        seen.add(label)
        types.append({"label": label, "confidence": _number(item.get("confidence"), "confidence")})
    raw_intent = payload.get("intent")
    raw_urgency = payload.get("urgency")
    if not isinstance(raw_intent, dict) or not isinstance(raw_urgency, dict):
        raise ProviderBadResponseError("intent e urgency devem ser objetos")
    intent = {"label": _label(raw_intent.get("label"), INTENTS, "intent"),
              "confidence": _number(raw_intent.get("confidence"), "intent.confidence")}
    urgency = {"label": _label(raw_urgency.get("label"), URGENCIES, "urgency"),
               "confidence": _number(raw_urgency.get("confidence"), "urgency.confidence")}
    messages = {item["message_id"]: item["content"] for item in snapshot.payload["messages"]}
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        raise ProviderBadResponseError("evidence deve ser uma lista")
    accepted: list[dict[str, Any]] = []
    allowed_type_labels = {item["label"] for item in types}
    for item in evidence:
        if not isinstance(item, dict):
            raise ProviderBadResponseError("Evidência inválida")
        dimension = item.get("dimension")
        label = item.get("label")
        message_id, quote = item.get("message_id"), item.get("quote")
        if dimension not in {"violence_type", "intent", "urgency"}:
            raise ProviderBadResponseError("Dimensão de evidência inválida")
        if not isinstance(message_id, str) or message_id not in messages:
            raise ProviderBadResponseError("Evidência aponta para mensagem inexistente")
        if not isinstance(quote, str) or not quote.strip() or quote not in messages[message_id]:
            raise ProviderBadResponseError("Evidência não é trecho literal da mensagem indicada")
        expected = (allowed_type_labels if dimension == "violence_type"
                    else {intent["label"]} if dimension == "intent" else {urgency["label"]})
        if label not in expected:
            raise ProviderBadResponseError("Rótulo da evidência não coincide com a inferência")
        accepted.append({"dimension": dimension, "label": label,
                         "message_id": message_id, "quote": quote})
    note = payload.get("audit_note", "")
    if not isinstance(note, str) or len(note) > 300:
        raise ProviderBadResponseError("audit_note deve ser texto de até 300 caracteres")
    return ValidClassification(
        profile=profile, model=model, source_kind="llm", violence_types=types,
        intent=intent, urgency=urgency, evidence=accepted, audit_note=note.strip(),
        latency_ms=latency_ms, input_tokens=input_tokens, output_tokens=output_tokens,
    )


class LLMClassifier:
    def __init__(self, profile: ClassifierProfile, models: ModelRegistry):
        self.profile = profile
        self.models = models

    async def classify(self, snapshot: ClassificationSnapshot) -> ValidClassification:
        model_profile = self.profile.model_profile
        assert model_profile is not None
        source = self.models.profile(model_profile)
        result = await self.models.provider(model_profile).generate(ChatRequest(
            messages=classifier_messages(snapshot.payload),
            temperature=self.profile.temperature,
            max_output_tokens=self.profile.max_output_tokens,
            tools=[],
            json_mode=True,
        ))
        return validate_llm_result(
            self.profile.name, result.model or source.model, result.text, result.latency_ms,
            result.input_tokens, result.output_tokens, snapshot,
        )


class SystemOneClassifier:
    """Maps the typed llama.cpp `/v1/systemone` result to the common ontology."""

    def __init__(self, profile: ClassifierProfile, client: httpx.AsyncClient):
        self.profile = profile
        self.client = client

    @staticmethod
    def _questions() -> dict[str, Any]:
        questions: dict[str, Any] = {
            f"type_{label}": {"type": "noul", "instructions": (
                "Há indício textual de " + description + "? Considere somente o estado."
            )}
            for label, description in TYPE_DESCRIPTIONS.items()
        }
        questions["intent"] = {
            "type": "choice", "instructions": "Qual é a intenção principal da usuária?",
            "criteria": INTENT_DESCRIPTIONS,
        }
        questions["urgency"] = {
            "type": "choice", "instructions": "Qual urgência é sustentada pelo estado disponível?",
            "criteria": URGENCY_DESCRIPTIONS,
        }
        return questions

    async def classify(self, snapshot: ClassificationSnapshot) -> ValidClassification:
        headers = {"Content-Type": "application/json"}
        if self.profile.api_key:
            headers["Authorization"] = f"Bearer {self.profile.api_key}"
        payload: dict[str, Any] = {"state": snapshot.payload, "questions": self._questions()}
        if self.profile.model:
            payload["model"] = self.profile.model
        started = time.perf_counter()
        try:
            response = await self.client.post(
                self.profile.api_url, headers=headers, json=payload, timeout=self.profile.timeout
            )
            response.raise_for_status()
            body = response.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("O classificador System One excedeu o tempo limite") from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError("O classificador System One não está disponível") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Não foi possível acessar o classificador System One") from exc
        except ValueError as exc:
            raise ProviderBadResponseError("System One não retornou JSON válido") from exc
        if not isinstance(body, dict) or not isinstance(body.get("answers"), dict):
            raise ProviderBadResponseError("Resposta System One sem answers")
        answers = body["answers"]
        types: list[dict[str, Any]] = []
        for label in VIOLENCE_TYPES:
            item = answers.get(f"type_{label}")
            probability = item.get("noul") if isinstance(item, dict) else None
            probability = _number(probability, f"type_{label}.noul")
            if probability >= 0.5:
                types.append({"label": label, "confidence": probability})
        def choice(key: str, allowed: tuple[str, ...]) -> dict[str, Any]:
            item = answers.get(key)
            if not isinstance(item, dict):
                raise ProviderBadResponseError(f"System One sem resposta para {key}")
            return {"label": _label(item.get("choice"), allowed, key),
                    "confidence": _number(item.get("confidence"), f"{key}.confidence")}
        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        return ValidClassification(
            profile=self.profile.name, model=str(body.get("model") or self.profile.model),
            source_kind="system_one", violence_types=types,
            intent=choice("intent", INTENTS), urgency=choice("urgency", URGENCIES),
            evidence=[], audit_note="Decisão tipada sem evidência textual gerada pelo modelo.",
            latency_ms=round((time.perf_counter() - started) * 1000),
            input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
        )


class ClassifierRegistry:
    def __init__(self, profiles: dict[str, ClassifierProfile], models: ModelRegistry,
                 client: httpx.AsyncClient):
        self.profiles = profiles
        self.models = models
        self.client = client

    def public_profiles(self) -> list[dict[str, Any]]:
        return [self.profiles[name].public_dict() for name in sorted(self.profiles)]

    def classifier(self, name: str):
        profile = self.profiles.get(name)
        if profile is None:
            raise ProviderBadResponseError(f"Perfil de classificador desconhecido: {name}")
        return LLMClassifier(profile, self.models) if profile.kind == "llm" else SystemOneClassifier(profile, self.client)


class ClassificationService:
    def __init__(self, settings: ChatSettings, registry: ClassifierRegistry, repository):
        self.settings = settings
        self.registry = registry
        self.repository = repository
        self.builder = ClassificationContextBuilder(settings.server.recent_messages)

    async def classify_turn(self, conversation_id: str, user_message_id: str,
                             history, summary) -> tuple[ClassificationSnapshot, list[ValidClassification]]:
        snapshot = self.builder.build(self.settings.classification.taxonomy_version, history, summary)
        results: list[ValidClassification] = []
        # Calls are intentionally serial. A 4060 cannot safely host the 8B LLM and Kev
        # simultaneously, and shadow comparison must not make one model's state affect another.
        for name in self.settings.classification.online_classifiers:
            try:
                result = await self.registry.classifier(name).classify(snapshot)
                self.repository.save_classification_run(
                    conversation_id, user_message_id, result, self.settings.classification.mode,
                    self.settings.classification.taxonomy_version, snapshot, "completed", None,
                )
                results.append(result)
            except Exception as exc:
                self.repository.save_classification_run(
                    conversation_id, user_message_id, None, self.settings.classification.mode,
                    self.settings.classification.taxonomy_version, snapshot, "failed", type(exc).__name__,
                    profile_name=name,
                )
        return snapshot, results

    def agent_context(self, results: list[ValidClassification]) -> dict[str, str] | None:
        if self.settings.classification.mode != "agent_context":
            return None
        source = self.settings.classification.agent_context_classifier
        for result in results:
            if result.profile == source:
                return {"role": "system", "content": result.compact_context()}
        return None
