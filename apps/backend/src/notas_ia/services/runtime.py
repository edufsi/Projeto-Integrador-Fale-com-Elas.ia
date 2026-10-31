from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from ..domain.models import TurnArtifacts
from ..errors import ConflictError


class AllowLocalAccess:
    async def authorize(self, conversation_id: str) -> None:
        return None


class NoopPipelineHooks:
    async def before_context(self, artifacts: TurnArtifacts) -> None:
        return None

    async def before_generation(self, artifacts: TurnArtifacts) -> None:
        return None

    async def after_generation(self, artifacts: TurnArtifacts) -> None:
        return None

    async def before_persist_response(self, artifacts: TurnArtifacts) -> None:
        return None


class ConversationLocks:
    def __init__(self, timeout: float):
        self.timeout = timeout
        self._locks: dict[str, asyncio.Lock] = {}
        self._guard = asyncio.Lock()

    @asynccontextmanager
    async def hold(self, conversation_id: str):
        async with self._guard:
            lock = self._locks.setdefault(conversation_id, asyncio.Lock())
        try:
            await asyncio.wait_for(lock.acquire(), timeout=self.timeout)
        except TimeoutError as exc:
            raise ConflictError("A conversa está processando outra mensagem") from exc
        try:
            yield
        finally:
            lock.release()
