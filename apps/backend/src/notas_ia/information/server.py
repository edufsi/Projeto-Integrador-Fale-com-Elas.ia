from __future__ import annotations

from fastmcp import FastMCP

from .catalog import CuratedInformation, CuratedInformationRegistry


def create_information_server(registry: CuratedInformationRegistry | None = None) -> FastMCP:
    registry = registry or CuratedInformationRegistry()
    server = FastMCP("Notas.IA Curated Information")

    @server.tool(name="get_general_help_resources")
    def get_general_help_resources() -> CuratedInformation:
        """Retorna canais gerais oficiais e revisados de acolhimento e orientação.

        Use para informações gerais sobre ajuda e rede de atendimento. Não use para
        localizar uma instituição específica: esta versão não recebe localização.
        """
        return registry.get("general-help-resources")

    @server.tool(name="get_violence_type_overview")
    def get_violence_type_overview() -> CuratedInformation:
        """Retorna explicação educativa revisada dos tipos usados neste protótipo.

        Não conclui que um tipo de violência ocorreu em um caso individual e não
        substitui busca jurídica para dúvidas específicas.
        """
        return registry.get("violence-type-overview")

    return server
