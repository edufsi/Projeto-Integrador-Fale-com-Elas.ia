from pydantic import BaseModel, Field
from typing import Optional

class AgenteIdentificacao(BaseModel):
    # --- Dados Demográficos ---
    identificacao_vitima_idade: Optional[int] = Field(
        default=None, 
        description="Idade da vítima. Retorne um número inteiro ou null."
    )
    identificacao_vitima_identidade_genero: Optional[str] = Field(
        default=None, 
        description="ENUM: mulher_cis, mulher_trans, travesti, pessoa_nao_binaria, prefiro_nao_informar, outra, null."
    )
    identificacao_vitima_orientacao_sexual: Optional[str] = Field(
        default=None, 
        description="ENUM: heterossexual, lesbica, bissexual, assexual, pansexual, prefiro_nao_informar, outra, null."
    )
    identificacao_vitima_escolaridade: Optional[str] = Field(
        default=None, 
        description="Nível de escolaridade da vítima. Retorne null se não mencionado."
    )
    identificacao_vitima_raca: Optional[str] = Field(
        default=None, 
        description="Cor ou raça da vítima (ex: preta, parda, branca, indígena, amarela). Retorne null se não mencionado."
    )
    identificacao_vitima_nacionalidade: Optional[str] = Field(
        default=None, 
        description="Nacionalidade da vítima. Retorne null se não mencionado."
    )
    
    # --- Vínculos com o Agressor ---
    vinculo_entre_as_partes_afetivo: Optional[str] = Field(
        default=None, 
        description="ENUM: marido_ou_esposo, ex_marido_ou_ex_esposo, companheiro, ex_companheiro, namorado, ex_namorado, outro, null. Preencha apenas se houver relação afetiva."
    )
    vinculo_entre_as_partes_familiar: Optional[str] = Field(
        default=None, 
        description="ENUM: pai, irmao, primo, genro_ou_nora, mae, filho, cunhado, padrasto, avo, sobrinho, madrasta, tio, enteado, outro, null. Preencha apenas se houver grau de parentesco."
    )
    vinculo_entre_as_partes_domestico: Optional[str] = Field(
        default=None, 
        description="ENUM: pessoa_que_reside_mesmo_lar, empregado_domestico, ex_residente_do_lar, cuidador, outro, null. Preencha apenas se houver relação doméstica/coabitação."
    )
    outros_vinculos_entre_as_partes: Optional[str] = Field(
        default=None,
        description="Extraia qualquer vínculo entre a vítima e o agressor que não se enquadre nas categorias acima. Retorne uma string ou null se não houver."
    )
    