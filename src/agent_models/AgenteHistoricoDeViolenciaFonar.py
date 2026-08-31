from pydantic import BaseModel, Field
from typing import Optional, List

class AgenteHistoricoDeViolenciaFonar(BaseModel):
    ameacou_vitima_ou_familiar: Optional[str] = Field(
        default=None, 
        description="ENUM: com_arma_de_fogo, com_faca, de_outra_forma, nao, null. O(A) agressor(a) já ameaçou a vítima ou algum familiar com a finalidade de atingi-la?"
    )
    agressoes_fisicas_graves: Optional[List[str]] = Field(
        default_factory=list, 
        description="ARRAY DE ENUM: queimadura, enforcamento, sufocamento, estrangulamento, tiro, afogamento, facada, paulada, outro, nenhuma_agressao_fisica. Houve agressões físicas graves?"
    )
    outras_agressoes_fisicas: Optional[List[str]] = Field(
        default_factory=list, 
        description="ARRAY DE ENUM: soco, chute, tapa, empurrao, puxao_de_cabelo, outro, nenhuma_agressao_fisica. Houve agressões físicas menores?"
    )
    necessitou_atendimento_medico_internacao: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, prefiro_nao_informar, null. A vítima precisou de atendimento médico após agressões?"
    )
    obrigou_relacao_sexual_contra_vontade: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_sei, null. O agressor a obrigou a ter relações ou atos sexuais contra a vontade dela?"
    )
    comportamentos_controle_ciume: Optional[List[str]] = Field(
        default_factory=list, 
        description="ARRAY DE ENUM: disse_se_nao_for_minha_nao_sera_de_mais_ninguem, perturbou_perseguiu_vigiou, proibiu_visitar_familiares_amigos, proibiu_trabalhar_estudar, telefonemas_mensagens_insistentes, impediu_acesso_dinheiro_bens, outros, nenhum. Identifique comportamentos de ciúme e controle."
    )
    registrou_ocorrencia_anterior: Optional[str] = Field(
        default=None, 
        description="ENUM: sim_ocorrencia_e_medida_protetiva, sim_apenas_ocorrencia, sim_apenas_medida_protetiva, nao_nunca_registrei, null. A vítima já buscou a polícia antes?"
    )
    descumpriu_medida_protetiva_anterior: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_sei, null. O agressor já descumpriu medida protetiva anteriormente?"
    )
    agressoes_ficaram_mais_frequentes_graves: Optional[str] = Field(
        default=None, 
        description="ENUM: sim_ficaram_mais_frequentes_ou_graves, nao_houve_aumento, nao_sei, null. A violência aumentou nos últimos 12 meses?"
    )