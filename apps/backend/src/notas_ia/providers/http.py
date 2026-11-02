from __future__ import annotations

import time
import json
from uuid import uuid4
from typing import Any

import httpx

from ..config import ModelProfile
from ..domain.models import ChatRequest, GenerationResult, ToolCall
from ..errors import (NotFoundError, ProviderBadResponseError, ProviderTimeoutError,
                      ProviderUnavailableError)


def _required_text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderBadResponseError("O provedor retornou uma resposta sem texto")
    return value


def _tool_calls(value: Any) -> list[ToolCall]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ProviderBadResponseError("tool_calls deve ser uma lista")
    calls: list[ToolCall] = []
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("function"), dict):
            raise ProviderBadResponseError("Tool call inválido")
        function = item["function"]
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError as exc:
                raise ProviderBadResponseError("Argumentos de ferramenta não são JSON") from exc
        if not isinstance(arguments, dict) or not function.get("name"):
            raise ProviderBadResponseError("Nome ou argumentos de ferramenta inválidos")
        calls.append(ToolCall(
            id=str(item.get("id") or f"call_{uuid4().hex}"),
            name=str(function["name"]),
            arguments=arguments,
        ))
    return calls


def _ollama_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted = []
    for message in messages:
        role = message["role"]
        if role == "assistant" and message.get("tool_calls"):
            converted.append({
                "role": "assistant",
                "content": message.get("content", ""),
                "tool_calls": [{
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": call["arguments"],
                    },
                } for call in message["tool_calls"]],
            })
        elif role == "tool":
            converted.append({
                "role": "tool",
                "tool_name": message["name"],
                "content": message["content"],
            })
        else:
            converted.append({"role": role, "content": message.get("content", "")})
    return converted


def _openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted = []
    for message in messages:
        role = message["role"]
        if role == "assistant" and message.get("tool_calls"):
            converted.append({
                "role": "assistant",
                "content": message.get("content") or None,
                "tool_calls": [{
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call["arguments"], ensure_ascii=False),
                    },
                } for call in message["tool_calls"]],
            })
        elif role == "tool":
            converted.append({
                "role": "tool",
                "tool_call_id": message["tool_call_id"],
                "content": message["content"],
            })
        else:
            converted.append({"role": role, "content": message.get("content", "")})
    return converted


class _HTTPProvider:
    def __init__(self, profile: ModelProfile, client: httpx.AsyncClient):
        self.profile = profile
        self.client = client

    async def _post(self, payload: dict) -> tuple[dict, int]:
        headers = {"Content-Type": "application/json"}
        if self.profile.api_key:
            headers["Authorization"] = f"Bearer {self.profile.api_key}"
        started = time.perf_counter()
        try:
            response = await self.client.post(
                self.profile.api_url,
                headers=headers,
                json=payload,
                timeout=self.profile.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("O provedor excedeu o tempo limite") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500 or exc.response.status_code == 429:
                raise ProviderUnavailableError(
                    f"O provedor respondeu HTTP {exc.response.status_code}"
                ) from exc
            raise ProviderBadResponseError(
                f"O provedor recusou a requisição com HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Não foi possível acessar o provedor") from exc
        except ValueError as exc:
            raise ProviderBadResponseError("O provedor não retornou JSON válido") from exc
        if not isinstance(data, dict):
            raise ProviderBadResponseError("A resposta do provedor deve ser um objeto JSON")
        return data, round((time.perf_counter() - started) * 1000)


class OllamaProvider(_HTTPProvider):
    async def generate(self, request: ChatRequest) -> GenerationResult:
        payload = {
            "model": self.profile.model,
            "messages": _ollama_messages(request.messages),
            "stream": False,
            "think": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_output_tokens,
            },
        }
        if request.tools:
            payload["tools"] = request.tools
        if request.json_mode:
            # Ollama accepts a JSON format constraint independently of tool calling.
            payload["format"] = "json"
        data, latency = await self._post(payload)
        message = data.get("message")
        if not isinstance(message, dict):
            raise ProviderBadResponseError("Resposta Ollama sem message")
        calls = _tool_calls(message.get("tool_calls"))
        content = message.get("content") or ""
        if not content.strip() and not calls:
            _required_text(content)
        return GenerationResult(
            text=content,
            model=str(data.get("model") or self.profile.model),
            finish_reason=data.get("done_reason"),
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            latency_ms=latency,
            metadata={"done": data.get("done")},
            tool_calls=calls,
        )


class OpenAICompatibleProvider(_HTTPProvider):
    async def generate(self, request: ChatRequest) -> GenerationResult:
        payload = {
            "model": self.profile.model,
            "messages": _openai_messages(request.messages),
            "stream": False,
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
        }
        if request.tools:
            payload["tools"] = request.tools
            payload["tool_choice"] = "auto"
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}
        data, latency = await self._post(payload)
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ProviderBadResponseError("Resposta compatível sem choices[0]")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ProviderBadResponseError("Resposta compatível sem message")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        calls = _tool_calls(message.get("tool_calls"))
        content = message.get("content") or ""
        if not content.strip() and not calls:
            _required_text(content)
        return GenerationResult(
            text=content,
            model=str(data.get("model") or self.profile.model),
            finish_reason=choice.get("finish_reason"),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_ms=latency,
            metadata={"response_id": data.get("id")},
            tool_calls=calls,
        )


class ModelRegistry:
    def __init__(self, profiles: dict[str, ModelProfile], client: httpx.AsyncClient):
        self.profiles = profiles
        self.client = client

    def profile(self, name: str) -> ModelProfile:
        try:
            return self.profiles[name]
        except KeyError as exc:
            raise NotFoundError(f"Perfil de modelo desconhecido: {name}") from exc

    def provider(self, name: str):
        profile = self.profile(name)
        if profile.provider == "ollama":
            return OllamaProvider(profile, self.client)
        return OpenAICompatibleProvider(profile, self.client)

    def public_profiles(self) -> list[dict]:
        return [self.profiles[name].public_dict() for name in sorted(self.profiles)]
