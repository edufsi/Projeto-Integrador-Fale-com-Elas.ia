from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationPreset:
    """Expected public backend state; never starts or reconfigures containers."""

    name: str
    model_profile: str
    classification_mode: str
    online_classifiers: tuple[str, ...] = ()
    agent_context_classifier: str | None = None
    compose_files: tuple[str, ...] = ()
    compose_profiles: tuple[str, ...] = ()


PRESETS = {
    "qwen-only": EvaluationPreset("qwen-only", "local-qwen", "disabled"),
    "qwen-qwen-shadow": EvaluationPreset(
        "qwen-qwen-shadow", "local-qwen", "shadow", ("local-qwen4",),
        compose_files=("compose.qwen-shadow.yaml",),
    ),
    "qwen-qwen-context": EvaluationPreset(
        "qwen-qwen-context", "local-qwen", "agent_context", ("local-qwen4",),
        "local-qwen4", ("compose.qwen-context.yaml",),
    ),
    "qwen-kev-shadow": EvaluationPreset(
        "qwen-kev-shadow", "local-qwen", "shadow", ("kev4b",),
        compose_files=("compose.kev.yaml",), compose_profiles=("kev",),
    ),
    "qwen-kev-context": EvaluationPreset(
        "qwen-kev-context", "local-qwen", "agent_context", ("kev4b",), "kev4b",
        ("compose.kev.yaml", "compose.kev-context.yaml"), ("kev",),
    ),
    "llama8-only": EvaluationPreset(
        "llama8-only", "local-llama8", "disabled", compose_profiles=("llama8",),
    ),
    "llama8-qwen-shadow": EvaluationPreset(
        "llama8-qwen-shadow", "local-llama8", "shadow", ("local-qwen4",),
        compose_files=("compose.llama8-qwen-shadow.yaml",), compose_profiles=("llama8",),
    ),
    "llama8-llama8-shadow": EvaluationPreset(
        "llama8-llama8-shadow", "local-llama8", "shadow", ("local-llama8",),
        compose_files=("compose.llama8-llama8-shadow.yaml",), compose_profiles=("llama8",),
    ),
    "llama8-kev-shadow": EvaluationPreset(
        "llama8-kev-shadow", "local-llama8", "shadow", ("kev4b",),
        compose_files=("compose.kev.yaml",), compose_profiles=("llama8", "kev"),
    ),
}
