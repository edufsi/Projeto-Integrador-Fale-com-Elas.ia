from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .agent import AgentRuntime, FastMCPToolCatalog
from .config import ChatSettings, load_settings
from .classification import ClassificationService, ClassifierRegistry
from .errors import ChatAPIError
from .providers import ModelRegistry
from .operations import HandoffTemplateRegistry
from .repositories import SQLiteConversationRepository
from .services.prompts import PromptRegistry
from .services.turns import TurnService


logger = logging.getLogger("notas_ia")


def create_app(config_path: str | Path = "apps/backend/config.example.ini",
               settings: ChatSettings | None = None,
               http_transport: httpx.AsyncBaseTransport | None = None,
               tool_catalog=None) -> FastAPI:
    resolved = settings or load_settings(config_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # This is intentionally emitted once at startup: it lets an experimenter
        # verify which Compose overlay reached the running backend without logging
        # URLs, prompts, messages or provider credentials.
        logger.info(
            "runtime_configuration classification_mode=%s online_classifiers=%s "
            "agent_context_classifier=%s default_model=%s",
            resolved.classification.mode,
            list(resolved.classification.online_classifiers),
            resolved.classification.agent_context_classifier,
            resolved.server.default_model_profile,
        )
        repository = SQLiteConversationRepository(resolved.server.database_path)
        repository.initialize()
        client = httpx.AsyncClient(transport=http_transport)
        models = ModelRegistry(resolved.models, client)
        prompts = PromptRegistry(resolved.assistants)
        catalog = tool_catalog or FastMCPToolCatalog(
            resolved.mcp.legal_url, resolved.mcp.timeout
        )
        templates = HandoffTemplateRegistry(Path(__file__).parent / "prompts")
        agent = AgentRuntime(
            catalog, templates,
            max_rounds=resolved.server.max_tool_rounds,
            max_calls=resolved.server.max_tool_calls,
            tool_context_budget_tokens=resolved.server.tool_context_budget_tokens,
        )
        # Disabled means no classifier registry is created at all: no client calls,
        # snapshots or classification tables are touched during a turn.
        classifier_registry = None
        classification_service = None
        if resolved.classification.mode != "disabled":
            classifier_registry = ClassifierRegistry(resolved.classifiers, models, client)
            classification_service = ClassificationService(
                resolved, classifier_registry, repository
            )
        app.state.repository = repository
        app.state.models = models
        app.state.prompts = prompts
        app.state.tool_catalog = catalog
        app.state.agent = agent
        app.state.classifier_registry = classifier_registry
        app.state.classification_service = classification_service
        app.state.turn_service = TurnService(
            resolved, repository, models, prompts, agent,
            classification_service=classification_service,
        )
        try:
            yield
        finally:
            await client.aclose()

    app = FastAPI(
        title="Notas.IA — API agentiva experimental",
        version="0.3.0",
        description=(
            "Protótipo acadêmico. Não validado para atendimento real; "
            "usa pesquisa jurídica e simula transbordo, sem substituir atendimento real."
        ),
        lifespan=lifespan,
    )
    if resolved.server.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved.server.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", "X-Request-ID"],
        )

    @app.exception_handler(ChatAPIError)
    async def known_error(_: Request, exc: ChatAPIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.middleware("http")
    async def request_metadata(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_complete method=%s path=%s status=%s duration_ms=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            round((time.perf_counter() - started) * 1000),
            request_id,
        )
        return response

    app.include_router(router)
    return app
