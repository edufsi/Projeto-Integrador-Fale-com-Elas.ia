from __future__ import annotations

from fastapi import APIRouter, Query, Request, Response, status

from .schemas import CreateConversationRequest, SendMessageRequest


router = APIRouter()


@router.post("/v1/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(body: CreateConversationRequest, request: Request):
    item = request.app.state.turn_service.create_conversation(
        body.model_profile, body.assistant_profile, body.memory_profile
    )
    return {
        "id": item.id,
        "model_profile": item.model_profile,
        "assistant_profile": item.assistant_profile,
        "memory_profile": item.memory_profile,
        "prompt_version": item.prompt_version,
        "created_at": item.created_at,
    }


@router.post("/v1/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, body: SendMessageRequest, request: Request):
    return await request.app.state.turn_service.send_message(
        conversation_id, str(body.client_message_id), body.content
    )


@router.get("/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    request: Request,
    after_sequence: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    return await request.app.state.turn_service.get_conversation(
        conversation_id, after_sequence, limit
    )


@router.delete("/v1/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, request: Request):
    await request.app.state.turn_service.delete_conversation(conversation_id)
    return Response(status_code=204)


@router.get("/v1/model-profiles")
async def model_profiles(request: Request):
    return {"items": request.app.state.models.public_profiles()}


@router.get("/v1/assistant-profiles")
async def assistant_profiles(request: Request):
    return {"items": request.app.state.prompts.public_profiles()}


@router.get("/health/live")
async def live():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(request: Request):
    database = request.app.state.repository.check()
    tools = await request.app.state.tool_catalog.status()
    return {
        "status": "ok" if database and tools["status"] == "ok" else "degraded",
        "database": "ok" if database else "unavailable",
        "tools": tools,
    }


@router.get("/version")
async def version():
    from .. import __version__
    return {"name": "chat-api", "version": __version__}
