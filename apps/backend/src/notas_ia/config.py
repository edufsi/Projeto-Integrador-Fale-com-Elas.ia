from __future__ import annotations

import os
from configparser import ConfigParser, ExtendedInterpolation
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServerSettings:
    database_path: Path
    host: str
    port: int
    allowed_origins: tuple[str, ...]
    default_model_profile: str
    default_assistant_profile: str
    default_memory_profile: str
    recent_messages: int
    summary_trigger_messages: int
    summary_trigger_tokens: int
    max_message_chars: int
    lock_timeout_seconds: float
    max_tool_rounds: int
    max_tool_calls: int
    tool_context_budget_tokens: int


@dataclass(frozen=True)
class MCPSettings:
    legal_url: str
    timeout: float


@dataclass(frozen=True)
class ModelProfile:
    name: str
    provider: str
    api_url: str
    model: str
    api_key: str
    context_budget_tokens: int
    max_output_tokens: int
    timeout: float
    temperature: float
    supports_tools: bool

    def public_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "model": self.model,
            "context_budget_tokens": self.context_budget_tokens,
            "max_output_tokens": self.max_output_tokens,
            "supports_tools": self.supports_tools,
        }


@dataclass(frozen=True)
class AssistantProfile:
    name: str
    prompt_path: Path
    summary_prompt_path: Path

    def public_dict(self) -> dict:
        return {"name": self.name}


@dataclass(frozen=True)
class ChatSettings:
    server: ServerSettings
    models: dict[str, ModelProfile]
    assistants: dict[str, AssistantProfile]
    mcp: MCPSettings
    config_path: Path


def _int(section, key: str, default: int) -> int:
    value = int(section.get(key, default))
    if value <= 0:
        raise ValueError(f"{key} deve ser positivo")
    return value


def load_settings(config_path: str | Path = "apps/backend/config.example.ini") -> ChatSettings:
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Configuração ausente: {path}")
    parser = ConfigParser(interpolation=ExtendedInterpolation())
    parser.read(path, encoding="utf-8")
    if not parser.has_section("CHAT_API"):
        raise ValueError("Seção [CHAT_API] ausente")
    root = parser["CHAT_API"]
    base = path.parent
    origins = tuple(item.strip() for item in root.get("ALLOWED_ORIGINS", "").split(",")
                    if item.strip())
    database = Path(root.get("DATABASE_PATH", "../../data/private/chat.sqlite3"))
    if not database.is_absolute():
        database = (base / database).resolve()
    server = ServerSettings(
        database_path=database,
        host=root.get("HOST", "127.0.0.1"),
        port=_int(root, "PORT", 8000),
        allowed_origins=origins,
        default_model_profile=root.get("DEFAULT_MODEL_PROFILE", "local-qwen"),
        default_assistant_profile=root.get(
            "DEFAULT_ASSISTANT_PROFILE", "acolhimento-juridico-v1"
        ),
        default_memory_profile=root.get("DEFAULT_MEMORY_PROFILE", "recent-window-v1"),
        recent_messages=_int(root, "RECENT_MESSAGES", 6),
        summary_trigger_messages=_int(root, "SUMMARY_TRIGGER_MESSAGES", 12),
        summary_trigger_tokens=_int(root, "SUMMARY_TRIGGER_TOKENS", 1800),
        max_message_chars=_int(root, "MAX_MESSAGE_CHARS", 12000),
        lock_timeout_seconds=float(root.get("LOCK_TIMEOUT_SECONDS", "30")),
        max_tool_rounds=_int(root, "MAX_TOOL_ROUNDS", 2),
        max_tool_calls=_int(root, "MAX_TOOL_CALLS", 3),
        tool_context_budget_tokens=_int(root, "TOOL_CONTEXT_BUDGET_TOKENS", 1600),
    )
    if server.lock_timeout_seconds <= 0:
        raise ValueError("LOCK_TIMEOUT_SECONDS deve ser positivo")

    models: dict[str, ModelProfile] = {}
    assistants: dict[str, AssistantProfile] = {}
    for section_name in parser.sections():
        if section_name.startswith("MODEL."):
            name = section_name.removeprefix("MODEL.")
            section = parser[section_name]
            provider = section.get("PROVIDER", "").lower()
            if provider not in {"ollama", "openai_compatible"}:
                raise ValueError(f"PROVIDER inválido em [{section_name}]")
            key_env = section.get("API_KEY_ENV", "").strip()
            models[name] = ModelProfile(
                name=name,
                provider=provider,
                api_url=section.get("API_URL", "").strip(),
                model=section.get("MODEL", "").strip(),
                api_key=os.getenv(key_env, "") if key_env else "",
                context_budget_tokens=_int(section, "CONTEXT_BUDGET_TOKENS", 4096),
                max_output_tokens=_int(section, "MAX_OUTPUT_TOKENS", 512),
                timeout=float(section.get("TIMEOUT", "120")),
                temperature=float(section.get("TEMPERATURE", "0.3")),
                supports_tools=section.getboolean("SUPPORTS_TOOLS", fallback=True),
            )
            if not models[name].api_url or not models[name].model:
                raise ValueError(f"API_URL e MODEL são obrigatórios em [{section_name}]")
        elif section_name.startswith("ASSISTANT."):
            name = section_name.removeprefix("ASSISTANT.")
            section = parser[section_name]
            prompt = Path(section.get("PROMPT_PATH", ""))
            summary = Path(section.get("SUMMARY_PROMPT_PATH", ""))
            if not prompt.is_absolute():
                prompt = (base / prompt).resolve()
            if not summary.is_absolute():
                summary = (base / summary).resolve()
            assistants[name] = AssistantProfile(name, prompt, summary)

    if server.default_model_profile not in models:
        raise ValueError("DEFAULT_MODEL_PROFILE não corresponde a uma seção [MODEL.*]")
    if server.default_assistant_profile not in assistants:
        raise ValueError("DEFAULT_ASSISTANT_PROFILE não corresponde a [ASSISTANT.*]")
    for assistant in assistants.values():
        if not assistant.prompt_path.is_file() or not assistant.summary_prompt_path.is_file():
            raise FileNotFoundError(f"Prompts ausentes no perfil {assistant.name}")
    mcp_section = parser["MCP"] if parser.has_section("MCP") else {}
    mcp = MCPSettings(
        legal_url=mcp_section.get("LEGAL_URL", "http://127.0.0.1:8001/mcp"),
        timeout=float(mcp_section.get("TIMEOUT", "30")),
    )
    if mcp.timeout <= 0:
        raise ValueError("MCP TIMEOUT deve ser positivo")
    return ChatSettings(server, models, assistants, mcp, path)
