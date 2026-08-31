from pydantic import BaseModel, Field
from typing import Optional

class AgenteConstrangimentoIavp(BaseModel):
    q1_criticava_aparencia: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor criticava a aparência da vítima (corpo, cabelo, roupas)?"
    )
    q2_proibia_roupas_maquiagem: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor proibia a vítima de usar algumas roupas ou maquiagem?"
    )
    q3_constrangia_frente_outras_pessoas: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor constrangia a vítima na frente de outras pessoas?"
    )
    q4_obrigava_pedir_desculpas: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor obrigava a vítima a pedir desculpas, mesmo quando não era culpa dela?"
    )
    q5_constrangia_fazer_coisas_nao_gostava: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor constrangia a vítima a fazer coisas que ela não gostava?"
    )
    detalhes_constrangimento: Optional[str] = Field(
        default=None, 
        description="Extraia detalhes específicos ou outras situações de constrangimento relatadas pela vítima. Retorne uma string ou null se não houver."
    )