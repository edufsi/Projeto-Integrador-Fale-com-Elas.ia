from pydantic import BaseModel, Field
from typing import Optional

class AgenteManipulacaoIavp(BaseModel):
    q12_perdia_cabeca_culpava: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor alegava que 'perdia a cabeça' e culpava a vítima?"
    )
    q13_culpava_tudo_ruim: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor culpava a vítima por tudo de ruim que acontecia (desemprego, dívidas, etc.)?"
    )
    q14_usava_medos: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor usava os medos e inseguranças da vítima dizendo que ela não era capaz?"
    )
    q15_nao_era_boa_mae: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor afirmava que a vítima não era uma 'boa dona de casa', 'boa mãe' ou 'esposa' para justificar o abuso?"
    )
    q16_ameacava_suicidio_matar_filhos: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor ameaçava se matar ou matar os filhos quando a vítima tentava terminar a relação?"
    )
    q17_escondia_coisas_louca: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor escondia coisas, invertia fatos e dizia que a vítima estava louca?"
    )
    detalhes_manipulacao: Optional[str] = Field(
        default=None, 
        description="Extraia detalhes específicos ou outras situações de manipulação relatadas. Retorne uma string ou null se não houver."
    )