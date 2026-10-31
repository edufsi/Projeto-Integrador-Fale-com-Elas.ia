from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class Conversation:
    id: str
    model_profile: str
    assistant_profile: str
    prompt_version: str
    created_at: str
    updated_at: str
    next_sequence: int
    memory_profile: str = "recent-window-v1"


@dataclass(frozen=True)
class Message:
    id: str
    conversation_id: str
    sequence: int
    role: Role
    content: str
    status: str
    created_at: str


@dataclass(frozen=True)
class Summary:
    id: str
    conversation_id: str
    version: int
    content: str
    through_sequence: int
    model_profile: str
    model: str
    created_at: str


@dataclass(frozen=True)
class ChatRequest:
    messages: list[dict[str, Any]]
    temperature: float
    max_output_tokens: int
    tools: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    finish_reason: str | None
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class TurnArtifacts:
    """Espaço separado para futuras classificações, RAG e ferramentas."""

    values: dict[str, Any] = field(default_factory=dict)
