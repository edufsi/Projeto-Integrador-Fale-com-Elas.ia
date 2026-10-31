from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateConversationRequest(BaseModel):
    model_profile: str | None = None
    assistant_profile: str | None = None
    memory_profile: str | None = None


class SendMessageRequest(BaseModel):
    client_message_id: UUID
    content: Annotated[str, Field(min_length=1)]

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content não pode conter apenas espaços")
        return value


class ErrorBody(BaseModel):
    error: dict
