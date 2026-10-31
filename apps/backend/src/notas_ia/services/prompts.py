from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ..config import AssistantProfile
from ..errors import NotFoundError


@dataclass(frozen=True)
class LoadedPrompts:
    assistant: str
    summary: str
    version: str


class PromptRegistry:
    def __init__(self, profiles: dict[str, AssistantProfile]):
        self.profiles = profiles
        self._loaded: dict[str, LoadedPrompts] = {}

    def get(self, name: str) -> LoadedPrompts:
        if name not in self.profiles:
            raise NotFoundError(f"Perfil de assistente desconhecido: {name}")
        if name not in self._loaded:
            profile = self.profiles[name]
            assistant = profile.prompt_path.read_text(encoding="utf-8").strip()
            summary = profile.summary_prompt_path.read_text(encoding="utf-8").strip()
            digest = hashlib.sha256((assistant + "\n" + summary).encode("utf-8")).hexdigest()[:16]
            self._loaded[name] = LoadedPrompts(assistant, summary, digest)
        return self._loaded[name]

    def public_profiles(self) -> list[dict]:
        return [
            {"name": name, "prompt_version": self.get(name).version}
            for name in sorted(self.profiles)
        ]
