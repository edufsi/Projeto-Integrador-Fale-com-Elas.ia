from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class CuratedSource(BaseModel):
    title: str
    url: str


class CuratedInformation(BaseModel):
    """Editorial content kept outside prompts so it can be reviewed independently."""

    resource_id: str
    version: str
    reviewed_at: str
    scope: str
    content: str
    sources: list[CuratedSource] = Field(default_factory=list)


class CuratedInformationRegistry:
    def __init__(self, resource_directory: Path | None = None):
        self.resource_directory = resource_directory or Path(__file__).parent / "resources"

    def get(self, resource_id: str) -> CuratedInformation:
        path = self.resource_directory / f"{resource_id}.pt-BR.json"
        if not path.is_file():
            raise ValueError(f"Recurso curado desconhecido: {resource_id}")
        return CuratedInformation.model_validate_json(path.read_text(encoding="utf-8"))
