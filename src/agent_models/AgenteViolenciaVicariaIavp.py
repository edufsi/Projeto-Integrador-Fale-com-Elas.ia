from pydantic import BaseModel, Field
from typing import Optional

class AgenteViolenciaVicariaIavp(BaseModel):
    q36_ameacava_guarda_filhos: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor ameaçava pedir a guarda dos filhos?"
    )
    q37_ameacava_filhos_desistir_processo: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor ameaçava os filhos para que a vítima desistisse de algum processo?"
    )
    q38_agressividade_filhos_punicao: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor agia com agressividade com os filhos como forma de punir a mãe?"
    )
    q39_deixava_dar_remedios_filhos: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor deixava de dar remédios ou cuidados aos filhos doentes como forma de punir a mãe?"
    )
    q40_colocava_filhos_risco: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor colocava os filhos em situações de risco como forma de puni-la?"
    )
    q41_recusava_pagar_pensao: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor se recusava a pagar pensão para os filhos como chantagem ou punição?"
    )