from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from pydantic import BaseModel, model_validator


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


class HandoffRequest(BaseModel):
    mode: Literal["offer", "immediate"]
    reason: Literal[
        "explicit_human_request", "possible_current_danger", "insufficient_confidence"
    ]

    @model_validator(mode="after")
    def compatible_mode_and_reason(self):
        if self.mode == "immediate" and self.reason != "possible_current_danger":
            raise ValueError("immediate exige possible_current_danger")
        if self.mode == "offer" and self.reason == "possible_current_danger":
            raise ValueError("possible_current_danger exige immediate")
        return self


def create_operations_server() -> FastMCP:
    server = FastMCP("Notas.IA Operations")

    @server.tool(name="request_human_handoff")
    def request_human_handoff(
        mode: Literal["offer", "immediate"],
        reason: Literal[
            "explicit_human_request", "possible_current_danger", "insufficient_confidence"
        ],
    ) -> HandoffResult:
        """Interrompe a resposta automática e seleciona um encaminhamento humano controlado.

        Use `offer` quando a pessoa pedir atendimento humano ou quando a incerteza
        impedir uma resposta segura. Use `immediate` somente diante de possível
        perigo atual. Este protótipo não possui atendente conectado.
        """
        request = HandoffRequest(mode=mode, reason=reason)
        return HandoffResult(
            mode=request.mode,
            reason=request.reason,
            template_id=(
                "handoff-immediate-v1" if request.mode == "immediate"
                else "handoff-offer-v1"
            ),
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

