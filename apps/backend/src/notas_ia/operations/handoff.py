from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from pydantic import BaseModel


class HandoffResult(BaseModel):
    action: Literal["human_handoff"] = "human_handoff"
    mode: Literal["offer", "immediate"]
    reason: Literal[
        "explicit_human_request", "possible_current_danger", "insufficient_confidence"
    ]
    status: Literal["simulated"] = "simulated"
    human_available: bool = False
    template_id: str
    stop_agent: bool = True


def create_operations_server() -> FastMCP:
    server = FastMCP("Notas.IA Operations")

    @server.tool(name="offer_human_handoff")
    def offer_human_handoff(
        reason: Literal["explicit_human_request", "insufficient_confidence"],
    ) -> HandoffResult:
        """Oferece encaminhamento humano simulado em uma resposta controlada.

        Use quando a pessoa pedir explicitamente uma atendente ou quando a limitação
        do protótipo impedir resposta segura. Não use para possível perigo atual:
        nesse caso use `escalate_immediate`. Este protótipo não possui atendente
        conectado.
        """
        return HandoffResult(
            mode="offer", reason=reason, template_id="handoff-offer-v1",
        )

    @server.tool(name="escalate_immediate")
    def escalate_immediate() -> HandoffResult:
        """Interrompe a resposta automática por possível perigo atual ou iminente.

        Use somente quando a mensagem atual indicar possível perigo presente ou
        iminente. Não requer argumentos: a própria chamada seleciona o template
        controlado. Este protótipo não conecta uma atendente real.
        """
        return HandoffResult(
            mode="immediate", reason="possible_current_danger",
            template_id="handoff-immediate-v1",
        )

    return server


class HandoffTemplateRegistry:
    def __init__(self, prompt_directory: Path):
        self.prompt_directory = prompt_directory

    def render(self, template_id: str) -> str:
        allowed = {
            "handoff-offer-v1": "handoff-offer-v1.pt-BR.md",
            "handoff-immediate-v1": "handoff-immediate-v1.pt-BR.md",
        }
        if template_id not in allowed:
            raise ValueError(f"Template de transbordo desconhecido: {template_id}")
        return (self.prompt_directory / allowed[template_id]).read_text(
            encoding="utf-8"
        ).strip()

