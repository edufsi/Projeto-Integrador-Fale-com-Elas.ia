from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from statistics import median
from typing import Any

from ..classification.ontology import VIOLENCE_TYPES


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil((len(ordered) - 1) * percentile) - 1)
    return round(ordered[index], 2)


def _completed(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in record.get("response", {}).get("classifications", [])
            if item.get("status") == "completed"]


def observed_action(response: dict[str, Any]) -> str:
    handoff = response.get("handoff") or {}
    if handoff.get("mode") == "immediate":
        return "immediate_handoff"
    if handoff.get("mode") == "offer":
        return "human_handoff_offer"
    tools = set((response.get("agent") or {}).get("tools_used", []))
    if "legal_search_legal_sources" in tools:
        return "legal_search"
    if "information_get_general_help_resources" in tools:
        return "general_information"
    if response.get("agent", {}).get("stop_reason") == "controlled_resource_fallback":
        return "controlled_resource_fallback"
    return "direct_response"


def _classification_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    failed: Counter[str] = Counter()
    for record in records:
        expected = record["expected"]
        for item in record.get("response", {}).get("classifications", []):
            profile = item.get("profile") or "unknown"
            if item.get("status") != "completed":
                failed[profile] += 1
                continue
            by_profile[profile].append((expected, item))
    output = {}
    for profile, values in by_profile.items():
        type_metrics = {}
        exact = 0
        for label in VIOLENCE_TYPES:
            tp = fp = fn = tn = 0
            for expected, predicted in values:
                truth = bool(expected["types"].get(label))
                result = label in {entry.get("label") for entry in predicted.get("types", [])}
                tp += truth and result
                fp += not truth and result
                fn += truth and not result
                tn += not truth and not result
            precision, recall = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
            f1 = (round(2 * precision * recall / (precision + recall), 4)
                  if precision is not None and recall is not None and precision + recall else 0.0)
            type_metrics[label] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                                   "precision": precision, "recall": recall, "f1": f1}
        for expected, predicted in values:
            truth = {label for label in VIOLENCE_TYPES if expected["types"].get(label)}
            result = {entry.get("label") for entry in predicted.get("types", [])}
            exact += truth == result
        intents = Counter()
        urgencies = Counter()
        immediate = Counter()
        for expected, predicted in values:
            observed_intent = (predicted.get("intent") or {}).get("label")
            observed_urgency = (predicted.get("urgency") or {}).get("label")
            intents[(expected.get("intencao"), observed_intent)] += 1
            urgencies[(expected.get("urgencia"), observed_urgency)] += 1
            immediate[(expected.get("urgencia") == "imediata", observed_urgency == "imediata")] += 1
        total_tp = sum(item["tp"] for item in type_metrics.values())
        total_fp = sum(item["fp"] for item in type_metrics.values())
        total_fn = sum(item["fn"] for item in type_metrics.values())
        micro_precision = _ratio(total_tp, total_tp + total_fp)
        micro_recall = _ratio(total_tp, total_tp + total_fn)
        micro_f1 = (round(2 * micro_precision * micro_recall / (micro_precision + micro_recall), 4)
                    if micro_precision is not None and micro_recall is not None
                    and micro_precision + micro_recall else 0.0)
        output[profile] = {
            "coverage": len(values), "failed": failed[profile], "types": type_metrics,
            "types_exact": _ratio(exact, len(values)),
            "types_macro_f1": round(sum(item["f1"] for item in type_metrics.values()) / len(type_metrics), 4),
            "types_micro_f1": micro_f1,
            "intent_accuracy": _ratio(sum(count for (truth, pred), count in intents.items() if truth == pred), len(values)),
            "urgency_accuracy": _ratio(sum(count for (truth, pred), count in urgencies.items() if truth == pred), len(values)),
            "intent_confusion": {f"{truth}|{pred}": count for (truth, pred), count in intents.items()},
            "urgency_confusion": {f"{truth}|{pred}": count for (truth, pred), count in urgencies.items()},
            "immediate": {
                "tp": immediate[(True, True)], "fn": immediate[(True, False)],
                "fp": immediate[(False, True)], "tn": immediate[(False, False)],
                "recall": _ratio(immediate[(True, True)], immediate[(True, True)] + immediate[(True, False)]),
            },
        }
    for profile, count in failed.items():
        output.setdefault(profile, {"coverage": 0, "failed": count})
    return output


def _classifier_disagreements(records: list[dict[str, Any]]) -> dict[str, Any]:
    pairs: Counter[str] = Counter()
    compared: Counter[str] = Counter()
    for record in records:
        completed = _completed(record)
        for index, left in enumerate(completed):
            for right in completed[index + 1:]:
                names = "|".join(sorted((left.get("profile", "unknown"), right.get("profile", "unknown"))))
                compared[names] += 1
                left_types = {item.get("label") for item in left.get("types", [])}
                right_types = {item.get("label") for item in right.get("types", [])}
                different = (
                    left_types != right_types or
                    (left.get("intent") or {}).get("label") != (right.get("intent") or {}).get("label") or
                    (left.get("urgency") or {}).get("label") != (right.get("urgency") or {}).get("label")
                )
                pairs[names] += different
    return {name: {"compared": compared[name], "different": pairs[name],
                   "rate": _ratio(pairs[name], compared[name])} for name in compared}


def _agent_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    observed = Counter()
    expected = Counter()
    immediate = Counter()
    tool_failures = 0
    word_limit_failures = 0
    channel_fallbacks = 0
    citation_fallbacks = 0
    responses_with_sources = 0
    sources_returned = 0
    for record in records:
        response = record.get("response", {})
        expectation = record["expected"].get("acao_esperada")
        action = observed_action(response)
        observed[action] += 1
        expected[expectation or "not_specified"] += 1
        needs_immediate = expectation == "transbordar_imediatamente"
        immediate[(needs_immediate, action == "immediate_handoff")] += 1
        tool_failures += sum(1 for item in response.get("agent", {}).get("tool_executions", [])
                             if item.get("status") == "failed")
        channel_fallbacks += action == "controlled_resource_fallback"
        citation_fallbacks += response.get("agent", {}).get("stop_reason") == "citation_fallback"
        sources = response.get("sources", [])
        responses_with_sources += bool(sources)
        sources_returned += len(sources)
        maximum = (record.get("response_rubric") or {}).get("max_palavras")
        content = (response.get("assistant_message") or {}).get("content", "")
        if maximum and len(re.findall(r"\S+", content)) > maximum:
            word_limit_failures += 1
    return {
        "observed_actions": dict(observed), "expected_actions": dict(expected),
        "immediate": {
            "tp": immediate[(True, True)], "fn": immediate[(True, False)],
            "fp": immediate[(False, True)], "tn": immediate[(False, False)],
            "recall": _ratio(immediate[(True, True)], immediate[(True, True)] + immediate[(True, False)]),
        },
        "tool_failures": tool_failures, "controlled_resource_fallbacks": channel_fallbacks,
        "citation_fallbacks": citation_fallbacks,
        "responses_with_sources": responses_with_sources,
        "sources_returned": sources_returned,
        "response_word_limit_failures": word_limit_failures,
        "automatic_action_note": (
            "Somente transbordo imediato/oferta e uso de ferramentas possuem correspondência "
            "automática confiável; ações conversacionais restantes exigem auditoria humana."
        ),
    }


def _performance(records: list[dict[str, Any]]) -> dict[str, Any]:
    e2e = [item["round_trip_ms"] for item in records if item.get("round_trip_ms") is not None]
    agent_latencies = [item.get("response", {}).get("usage", {}).get("latency_ms")
                       for item in records]
    agent_latencies = [value for value in agent_latencies if value is not None]
    classifier = defaultdict(list)
    for record in records:
        for item in _completed(record):
            classifier[item.get("profile") or "unknown"].append(item)
    return {
        "turns": len(records),
        "round_trip_ms": {"median": median(e2e) if e2e else None, "p95": _percentile(e2e, .95)},
        "agent_latency_ms": {"median": median(agent_latencies) if agent_latencies else None,
                             "p95": _percentile(agent_latencies, .95)},
        "agent_tokens": {
            "input": sum(item.get("response", {}).get("usage", {}).get("input_tokens") or 0 for item in records),
            "output": sum(item.get("response", {}).get("usage", {}).get("output_tokens") or 0 for item in records),
        },
        "classifiers": {
            profile: {
                "turns": len(items),
                "latency_ms_median": median([item["latency_ms"] for item in items if item.get("latency_ms") is not None]) if any(item.get("latency_ms") is not None for item in items) else None,
                "input_tokens": sum(item.get("input_tokens") or 0 for item in items),
                "output_tokens": sum(item.get("output_tokens") or 0 for item in items),
            } for profile, items in classifier.items()
        },
    }


def build_report(records: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> dict[str, Any]:
    groups = defaultdict(list)
    for item in records:
        groups[item["review_status"]].append(item)
    return {
        "schema_version": "evaluation-report.v1",
        "turns_completed": len(records), "blocked_suites": blocked,
        "by_review_status": {
            status: {
                "turns": len(items), "classification": _classification_metrics(items),
                "classifier_disagreements": _classifier_disagreements(items),
                "agent": _agent_metrics(items), "performance": _performance(items),
            } for status, items in groups.items()
        },
    }
