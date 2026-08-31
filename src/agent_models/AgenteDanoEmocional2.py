from pydantic import BaseModel, Field
from typing import Optional

class AgenteDanoEmocional2(BaseModel):
    q52_fobia_medo_especifico: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Desenvolveu fobia ou medo específico (altura, animais, pessoas, sangue)?"
    )
    q53_alteracoes_apetite_peso: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Teve alterações no apetite com aumento ou perda de peso?"
    )
    q54_doente_frequencia: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Passou a ficar doente com frequência (dores, lesões, queda de cabelo, pressão alta)?"
    )
    q55_tremores_relembrar: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Apresenta tremores ao relembrar dos fatos?"
    )
    q56_coracao_acelerado_falta_ar: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Sente coração acelerado ou falta de ar quando alguém do sexo oposto se aproxima?"
    )
    q57_desanimo_apatia: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Sente desânimo, apatia ou indiferença em ambientes de lazer?"
    )
    q58_incapaz_fracassada: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Passou a se sentir incapaz, fracassada ou sem valor?"
    )
    q59_mundo_perigoso_nao_confia: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Passou a ver o mundo como perigoso e não confia nas pessoas?"
    )
    q60_irritabilidade_constante: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Passou a ter irritabilidade constante?"
    )
    q61_ideacao_suicida: Optional[str] = Field(
        default=None, description="ENUM: sim, nao, null. Perdeu a vontade de viver ou teve ideação suicida?"
    )