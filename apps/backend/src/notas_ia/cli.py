from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import time
from uuid import uuid4

import httpx
import uvicorn

from .app import create_app
from .classification import ClassifierRegistry
from .classification.context import ClassificationSnapshot
from .config import load_settings
from .evaluation.cli import add_parser as add_evaluation_parser, execute as execute_evaluation
from .providers import ModelRegistry
from .repositories import SQLiteConversationRepository


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


def _metric(value: int | float | None, unit: str = "") -> str:
    """Format a provider metric without treating an omitted value as zero."""
    return f"{value}{unit}" if value is not None else "não informado"


def _trace_turn(data: dict, round_trip_ms: int | None = None) -> None:
    """Prints an audit trace, deliberately excluding private chain-of-thought."""
    context = data.get("context", {})
    agent = data.get("agent", {})
    print("\n--- Traço de auditoria ---")
    print("Contexto:",
          f"memória={context.get('memory_profile')}, "
          f"resumo_usado={context.get('summary_used')}, "
          f"mensagens={context.get('messages_used')}, "
          f"tokens_estimados={context.get('estimated_input_tokens')}, "
          f"estado={context.get('status')}")
    print("Agente:",
          f"ferramentas_disponíveis={agent.get('tools_available', [])}, "
          f"usadas={agent.get('tools_used', [])}, "
          f"parada={agent.get('stop_reason')}")
    usage = data.get("usage", {})
    print("Desempenho:")
    print("  Turno completo (cliente → API → cliente):",
          _metric(round_trip_ms, " ms"))
    print("  LLM do agente (soma das chamadas no turno):",
          f"entrada={_metric(usage.get('input_tokens'))} tokens; "
          f"saída={_metric(usage.get('output_tokens'))} tokens; "
          f"tempo={_metric(usage.get('latency_ms'), ' ms')}")
    for execution in agent.get("tool_executions", []):
        print("  Ferramenta:", execution.get("tool_name"),
              f"status={execution.get('status')}",
              f"estratégia={execution.get('strategy')}",
              f"fontes={execution.get('source_ids', [])}")
        if execution.get("error_code"):
            print("    Erro de ferramenta:", execution["error_code"])
    if agent.get("degraded_services"):
        print("  Serviços degradados:", agent["degraded_services"])
    handoff = data.get("handoff")
    if handoff:
        print("Transbordo:",
              f"modo={handoff.get('mode')}, motivo={handoff.get('reason')}, "
              f"status={handoff.get('status')}")
    classifications = data.get("classifications")
    if classifications is None:
        print("Classificação: desativada no backend que respondeu a este turno.")
    else:
        for item in classifications:
            print("Classificação:",
                  f"perfil={item.get('profile')}, status={item.get('status')}, "
                  f"modelo={item.get('model')}")
            print("  Desempenho:",
                  f"entrada={_metric(item.get('input_tokens'))} tokens; "
                  f"saída={_metric(item.get('output_tokens'))} tokens; "
                  f"tempo={_metric(item.get('latency_ms'), ' ms')}")
            if item.get("status") != "completed":
                print("  Erro:", item.get("error_code"))
                if item.get("error_code") in {"ProviderUnavailableError", "provider_unavailable"}:
                    print("  Verificação: o Kev deve responder a GET /v1/models e o "
                          "container backend deve alcançar host.docker.internal:8080.")
                continue
            types = [
                (f"{entry.get('label')} ({float(entry['confidence']):.2f})"
                 if isinstance(entry.get("confidence"), (int, float))
                 else str(entry.get("label")))
                for entry in item.get("types", [])
            ]
            intent = item.get("intent") or {}
            urgency = item.get("urgency") or {}
            print("  Resultado:",
                  f"tipos={types or ['nenhum indício']}; "
                  f"intenção={intent.get('label')} ({intent.get('confidence')}); "
                  f"urgência={urgency.get('label')} ({urgency.get('confidence')})")
            if item.get("evidence"):
                print("  Evidências:")
                for evidence in item["evidence"]:
                    print("   -", evidence.get("label"), ":", repr(evidence.get("quote")))
            if item.get("audit_note"):
                print("  Nota:", item["audit_note"])
    print("--- fim do traço ---\n")


def _chat(base_url: str, model_profile: str | None, trace: bool = False) -> None:
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
                started = time.perf_counter()
                response = client.post(
                    f"/v1/conversations/{conversation_id}/messages",
                    json={"client_message_id": str(uuid4()), "content": content},
                )
                response.raise_for_status()
                round_trip_ms = round((time.perf_counter() - started) * 1000)
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
            if trace:
                _trace_turn(data, round_trip_ms)


async def _classify_replay(config_path: str, source_profile: str, target_profile: str,
                           conversation_id: str | None, limit: int) -> None:
    """Replays stored frozen snapshots one at a time; never runs two models in parallel."""
    settings = load_settings(config_path)
    repository = SQLiteConversationRepository(settings.server.database_path)
    repository.initialize()
    rows = repository.list_classification_snapshots(source_profile, conversation_id, limit)
    if not rows:
        print("Nenhum snapshot concluído encontrado para o perfil de origem.")
        return
    async with httpx.AsyncClient() as client:
        registry = ClassifierRegistry(settings.classifiers, ModelRegistry(settings.models, client), client)
        classifier = registry.classifier(target_profile)
        completed = failed = 0
        for row in rows:
            payload = json.loads(row["snapshot_json"])
            canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            snapshot = ClassificationSnapshot(
                payload=payload, canonical_json=canonical,
                sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            )
            try:
                result = await classifier.classify(snapshot)
                repository.save_classification_run(
                    row["conversation_id"], row["user_message_id"], result, "replay",
                    row["taxonomy_version"], snapshot, "completed", None,
                )
                completed += 1
            except Exception as exc:
                repository.save_classification_run(
                    row["conversation_id"], row["user_message_id"], None, "replay",
                    row["taxonomy_version"], snapshot, "failed", type(exc).__name__,
                    profile_name=target_profile,
                )
                failed += 1
    print(f"Replay concluído: {completed} sucesso(s), {failed} falha(s).")


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
    chat.add_argument("--trace", action="store_true",
                      help=("mostra classificação, ferramentas e métricas auditáveis; "
                            "não exibe raciocínio interno"))
    replay = commands.add_parser("classify-replay")
    replay.add_argument(
        "--config", default=os.getenv("CHAT_API_CONFIG", "apps/backend/config.example.ini")
    )
    replay.add_argument("--source-profile", required=True,
                        help="perfil que originalmente produziu os snapshots")
    replay.add_argument("--target-profile", required=True,
                        help="classificador a executar sobre os snapshots")
    replay.add_argument("--conversation-id")
    replay.add_argument("--limit", type=int, default=1000)
    add_evaluation_parser(commands)
    args = parser.parse_args()
    if args.command == "api":
        _serve(args.config)
    elif args.command == "chat":
        _chat(args.url, args.model_profile, args.trace)
    elif args.command == "classify-replay":
        if args.limit <= 0:
            parser.error("--limit deve ser positivo")
        asyncio.run(_classify_replay(
            args.config, args.source_profile, args.target_profile,
            args.conversation_id, args.limit,
        ))
    else:
        execute_evaluation(args)

