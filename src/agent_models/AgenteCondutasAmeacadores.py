from pydantic import BaseModel, Field
from typing import Optional

class AgenteCondutasAmeacadores(BaseModel):
    q27_gritava_explodia: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor gritava ou explodia por qualquer coisa?"
    )
    q28_explodia_ciumes_amantes: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor explodia por ciúmes ou acusava a vítima de ter amantes/estar paquerando?"
    )
    q29_destruia_escondia_coisas: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor destruía ou escondia as coisas pessoais da vítima?"
    )
    q30_destruia_moveis: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor destruía móveis ou utensílios da casa?"
    )
    q31_ameacava_animais: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor maltratava ou ameaçava os animais de estimação da vítima?"
    )
    q32_ameacava_contar_segredos_fotos: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor ameaçava contar segredos pessoais ou divulgar fotos da vítima para outras pessoas?"
    )
    q33_dizia_processos_sem_nada: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor dizia que, se ela o deixasse, entraria com processos e ela ficaria sem nada?"
    )
    q34_exibia_armas: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor exibia armas de fogo, facas ou outros objetos como forma de intimidação?"
    )
    detalhes_medo: Optional[str] = Field(
        default=None, 
        description="Extraia detalhes específicos ou outra situação relatada que causava medo à vítima. Retorne uma string ou null se não houver."
    )