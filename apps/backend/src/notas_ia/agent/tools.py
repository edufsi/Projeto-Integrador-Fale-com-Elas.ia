from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastmcp import Client, ClientGroup

from ..errors import ToolError
from ..operations import create_operations_server


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    input_schema: dict[str, Any]

    def as_llm_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


@dataclass
class ToolSession:
    group: ClientGroup
    descriptors: list[ToolDescriptor]
    degraded_services: list[str]

    async def call(self, name: str, arguments: dict[str, Any]) -> Any:
        allowed = {item.name for item in self.descriptors}
        if name not in allowed:
            raise ToolError(f"Ferramenta não autorizada neste turno: {name}")
        try:
            result = await self.group.call_tool(name, arguments, raise_on_error=True)
        except Exception as exc:
            raise ToolError(f"Falha ao executar {name}: {type(exc).__name__}") from exc
        data = result.structured_content or result.data
        if hasattr(data, "root"):
            data = data.root
        elif hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        return data


class FastMCPToolCatalog:
    """Catálogo com operações locais e RAG remoto, degradável por turno."""

    def __init__(self, legal_url: str, timeout: float = 30):
        self.legal_url = legal_url
        self.timeout = timeout
        self.operations_server = create_operations_server()

    def _group(self, include_legal: bool) -> ClientGroup:
        clients = {
            "operations": Client(self.operations_server, timeout=self.timeout),
        }
        if include_legal:
            clients["legal"] = Client(self.legal_url, timeout=self.timeout)
        return ClientGroup(clients)

    @staticmethod
    async def _descriptors(group: ClientGroup) -> list[ToolDescriptor]:
        return [
            ToolDescriptor(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.input_schema,
            )
            for tool in await group.list_tools()
        ]

    @asynccontextmanager
    async def session(self):
        group = self._group(include_legal=True)
        degraded: list[str] = []
        entered = False
        try:
            try:
                await group.__aenter__()
                entered = True
                descriptors = await self._descriptors(group)
            except Exception:
                if entered:
                    await group.__aexit__(None, None, None)
                group = self._group(include_legal=False)
                await group.__aenter__()
                entered = True
                descriptors = await self._descriptors(group)
                degraded = ["legal"]
            yield ToolSession(group, descriptors, degraded)
        finally:
            if entered:
                await group.__aexit__(None, None, None)

    async def status(self) -> dict[str, Any]:
        async with self.session() as session:
            return {
                "status": "degraded" if session.degraded_services else "ok",
                "degraded_services": session.degraded_services,
                "tools": [item.name for item in session.descriptors],
            }

