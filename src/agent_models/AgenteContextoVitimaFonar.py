from pydantic import BaseModel, Field
from typing import Optional, List

class AgenteContextoVitimaFonar(BaseModel):
    tentou_terminou_ou_manifestou_intencao_terminar: Optional[str] = Field(
        default=None, 
        description="ENUM: sim_terminei_recentemente, sim_tentei_mas_ainda_estou_na_relacao, sim_manifestei_intencao, nao, null. A vítima terminou ou tentou terminar o relacionamento recentemente?"
    )
    possui_filhos: Optional[str] = Field(
        default=None, 
        description="ENUM: sim_outro_relacionamento, sim_com_agressor, nao_possuo, null. A vítima tem filhos?"
    )
    possui_filhos_quantidade: Optional[int] = Field(
        default=None, 
        description="Quantidade total de filhos da vítima. Retorne um número inteiro ou null se não mencionado."
    )
    faixa_etaria_filhos: Optional[List[str]] = Field(
        default_factory=list, 
        description="ARRAY DE ENUM: 0_a_11_anos, 12_a_17_anos, a_partir_de_18_anos. Qual a faixa etária dos filhos?"
    )
    filho_pessoa_com_deficiencia: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. Algum dos filhos é pessoa com deficiência?"
    )
    filho_pessoa_com_deficiencia_quantidade: Optional[int] = Field(
        default=None, 
        description="Quantidade de filhos com deficiência. Retorne um número inteiro ou null."
    )
    conflito_guarda_visitas_pensao: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_sei, null. Estão vivendo conflitos de guarda, visitas ou pensão?"
    )
    filhos_presenciaram_violencia: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_sei, null. Os filhos já presenciaram atos de violência do agressor?"
    )
    violencia_durante_gravidez_ou_puerperio: Optional[str] = Field(
        default=None, 
        description="ENUM: sim_gravida_e_sofro_violencia, sim_tive_filho_e_sofro_violencia, sim_sofri_gravidez_ou_pos_parto_mas_nao_atualmente, nao_sofri, null. Houve violência na gravidez ou até 18 meses após o parto?"
    )
    novo_relacionamento_gerou_aumento_ameacas: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_se_aplica, null. Um novo relacionamento da vítima gerou aumento das ameaças?"
    )
    isolada_amigos_familiares: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_sei, null. A vítima se sente isolada de amigos ou familiares?"
    )
    possui_deficiencia_ou_doenca_degenerativa: Optional[List[str]] = Field(
        default_factory=list, 
        description="ARRAY DE ENUM: deficiencia_fisica, deficiencia_visual, deficiencia_auditiva, deficiencia_intelectual, doenca_degenerativa, outra, nao, prefiro_nao_informar. A vítima possui alguma dessas condições?"
    )