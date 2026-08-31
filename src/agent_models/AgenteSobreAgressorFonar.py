from pydantic import BaseModel, Field
from typing import Optional, List

class AgenteSobreAgressorFonar(BaseModel):
    uso_abusivo_substancias: Optional[List[str]] = Field(
        default_factory=list, 
        description="ARRAY DE ENUM: alcool, drogas, medicamentos, nao_faz_uso, nao_sei. O(A) agressor(a) faz uso abusivo de alguma dessas substâncias?"
    )
    doenca_mental_comprovada: Optional[str] = Field(
        default=None, 
        description="ENUM: sim_e_faz_uso_de_medicacao, sim_e_nao_faz_uso_de_medicacao, nao, nao_sei, null. O(A) agressor(a) tem alguma doença mental comprovada por avaliação médica?"
    )
    tentou_ou_falou_em_suicidio: Optional[str] = Field(
        default=None, 
        description="ENUM: sim_ja_tentou_suicidio, sim_ja_falou_mas_nunca_tentou, nao_nunca_tentou_nem_falou, nao_sei, null. O(A) agressor(a) já tentou ou falou em suicidar-se?"
    )
    desempregado_ou_dificuldade_financeira: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_sei, null. O(A) agressor(a) está desempregado(a) ou tem dificuldades financeiras?"
    )
    facil_acesso_arma_de_fogo: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, nao_sei, prefiro_nao_informar, null. O(A) agressor(a) tem fácil acesso a arma de fogo (posse própria ou profissão)?"
    )
    agrediu_ou_ameacou_terceiros: Optional[List[str]] = Field(
        default_factory=list, 
        description="ARRAY DE ENUM: filhos, outros_familiares, animais_estimacao, outras_parceiras_intimas, outras_pessoas_amigos_colegas_desconhecidas, nao, nao_sei. O(A) agressor(a) já ameaçou ou agrediu terceiros ou animais?"
    )
    registro_ocorrencia_por_essas_violencias: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. Há conhecimento de registro de ocorrência policial ou medida protetiva contra o agressor por essas violências a terceiros?"
    )