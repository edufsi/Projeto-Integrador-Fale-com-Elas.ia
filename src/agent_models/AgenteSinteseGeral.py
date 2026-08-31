from pydantic import BaseModel, Field
from typing import Optional

class AgenteSinteseGeral(BaseModel):
    q35_inteligencia_artificial: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. Foi utilizada IA ou tecnologia para alterar imagem ou voz da vítima nas condutas anteriores?"
    )
    frequencia_condutas: Optional[str] = Field(
        default=None, 
        description="ENUM: poucas_vezes, muitas_vezes, sempre, null. Com que frequência as condutas de violência aconteciam? Retorne null se não houver."
    )
    outras_situacoes: Optional[str] = Field(
        default=None, 
        description="Especifique  condutas abusivas relatadas pela vítima. Retorne null se não houver."
    )
    sintomas: Optional[str] = Field(
        default=None, 
        description="A vítima apresenta ou apresentou sintomas de dano emocional ou físico? Descreva, apontando se há necessidade de atendimento ou encaminhamento da vítima"
    )
    resumo_geral_do_relato: Optional[str] = Field(
        default=None, 
        description="Elabore um resumo conciso (1 a 2 parágrafos) do relato da vítima, destacando a dinâmica principal de controle, os medos relatados e o nível de vulnerabilidade aparente."
    )