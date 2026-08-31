from pydantic import BaseModel, Field
from typing import Optional

class AgenteIsolamentoIavp(BaseModel):
    q18_dificultava_contato_familiares: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor dificultava o contato da vítima com familiares?"
    )
    q19_obrigava_viva_voz: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. Quando os familiares ligavam, o agressor obrigava a vítima a colocar no viva-voz?"
    )
    q20_reclamava_saia_sozinha: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor reclamava quando a vítima saía sozinha?"
    )
    q21_reclamava_estudar_trabalhar: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor reclamava quando a vítima saía para estudar ou trabalhar?"
    )
    q22_bravo_conversava_homens: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor ficava bravo se a vítima conversava com homens que não eram da família?"
    )
    q23_escolhia_amizades: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor escolhia as amizades da vítima?"
    )
    q24_controlava_mensagens: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor controlava a vítima por mensagens, ligações ou de outro modo?"
    )
    q25_exigia_senhas: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor exigia as senhas da vítima em redes sociais?"
    )
    q26_ciumes_atencao: Optional[str] = Field(
        default=None, 
        description="ENUM: sim, nao, null. O agressor tinha ciúmes se alguma pessoa desse atenção ou se aproximasse da vítima?"
    )
    detalhes_isolamento: Optional[str] = Field(
        default=None, 
        description="Extraia detalhes específicos ou outra situação de isolamento relatada. Retorne uma string ou null se não houver."
    )