from pydantic import BaseModel, Field
from typing import Optional

class AgenteDanoEmocional1(BaseModel):
    q42_evitar_pessoas_lugares: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. A vítima passou a evitar pessoas ou lugares que relembram os fatos?"
    )
    q43_medo_ficar_sozinha: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. A vítima tem medo de ficar sozinha em casa ou sair desacompanhada?"
    )
    q44_pesadelos_dormir: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. A vítima tem pesadelos ou dificuldade para dormir?"
    )
    q45_tristeza_crises_choro: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. A vítima relatou tristeza profunda ou crises de choro?"
    )
    q46_estado_alerta: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. A vítima está em constante estado de alerta (atenção e medo)?"
    )
    q47_dificuldade_atividades_dia_a_dia: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. A vítima tem dificuldade para realizar atividades do dia a dia?"
    )
    q48_afastamento_trabalho_estudos: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Houve afastamento do trabalho ou dos estudos?"
    )
    q49_afastamento_familiares_amigos: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Houve afastamento de familiares ou amigos?"
    )
    q50_deixou_relacionar_sexualmente_afetivamente: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Deixou de se relacionar sexualmente ou afetivamente com outras pessoas?"
    )
    q51_deixou_relacionar_pessoas_mesmo_sexo: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Deixou de se relacionar com pessoas do mesmo sexo do agressor?"
    )