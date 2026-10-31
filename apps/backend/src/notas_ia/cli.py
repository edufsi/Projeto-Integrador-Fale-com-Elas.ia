from __future__ import annotations

import argparse
import os
from uuid import uuid4

import httpx
import uvicorn

from .app import create_app
from .config import load_settings


def _terminal_text(value: str) -> str:
    """Recupera bytes UTF-8 preservados como surrogates por terminais Docker/WSL."""
    try:
        value.encode("utf-8")
        return value
    except UnicodeEncodeError:
        try:
            raw = value.encode("utf-8", errors="surrogateescape")
        except UnicodeEncodeError:
            return value.encode("utf-8", errors="replace").decode("utf-8")
        return raw.decode("utf-8", errors="replace")


def _http_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(body.get("detail"), str):
            return body["detail"]
    return f"HTTP {response.status_code}: {response.text[:300].strip()}"


def _serve(config_path: str) -> None:
    settings = load_settings(config_path)
    uvicorn.run(
        create_app(settings=settings), host=settings.server.host,
        port=settings.server.port, workers=1, log_level="info",
    )


def _chat(base_url: str, model_profile: str | None) -> None:
    with httpx.Client(base_url=base_url, timeout=180) as client:
        try:
            created = client.post("/v1/conversations", json={
                "model_profile": model_profile,
                "assistant_profile": None,
                "memory_profile": "recent-window-v1",
            })
            created.raise_for_status()
        except httpx.HTTPStatusError as exc:
            print(f"Não foi possível criar a conversa: {_http_error_message(exc.response)}")
            return
        except httpx.RequestError as exc:
            print(f"Não foi possível acessar {base_url}: {exc}")
            return
        conversation_id = created.json()["id"]
        print(f"Conversa {conversation_id}. Digite /sair para encerrar.")
        while True:
            try:
                content = _terminal_text(input("Você: ")).strip()
            except (EOFError, KeyboardInterrupt):
                break
            if content.lower() == "/sair":
                break
            if not content:
                continue
            try:
                response = client.post(
                    f"/v1/conversations/{conversation_id}/messages",
                    json={"client_message_id": str(uuid4()), "content": content},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                print(f"Falha no turno: {_http_error_message(exc.response)}")
                continue
            except httpx.RequestError as exc:
                print(f"Conexão com o backend interrompida: {exc}")
                continue
            data = response.json()
            print("Assistente:", data["assistant_message"]["content"])
            for source in data.get("sources", []):
                print(f"  [{source['reference']}] {source['document']}, "
                      f"{source['section']} — {source['url']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Notas.IA")
    commands = parser.add_subparsers(dest="command", required=True)
    api = commands.add_parser("api")
    api.add_argument(
        "--config", default=os.getenv("CHAT_API_CONFIG", "apps/backend/config.example.ini")
    )
    chat = commands.add_parser("chat")
    chat.add_argument("--url", default="http://127.0.0.1:8000")
    chat.add_argument("--model-profile")
    args = parser.parse_args()
    if args.command == "api":
        _serve(args.config)
    else:
        _chat(args.url, args.model_profile)

