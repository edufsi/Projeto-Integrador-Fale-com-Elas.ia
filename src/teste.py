import asyncio
import json
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from agent_models import *

# =====================================================================
# 1. CLASSES PYDANTIC (NOSSOS 13 AGENTES ESPECIALISTAS)
# =====================================================================

# Dicionário mapeando os nomes para as classes para iterarmos facilmente
SCHEMAS_AGENTES = {
    "identificacao": AgenteIdentificacao,
    "historico_violencia": AgenteHistoricoDeViolenciaFonar,
    "perfil_agressor": AgenteSobreAgressorFonar,
    "isolamento": AgenteIsolamentoIavp,
    "ameacas_iavp": AgenteCondutasAmeacadores,
    "constrangimento": AgenteConstrangimentoIavp, 
    "contexto_vitima": AgenteContextoVitimaFonar,
    "dano_emocional1": AgenteDanoEmocional1,
    "dano_emocional2": AgenteDanoEmocional2,
    "manipulacao": AgenteManipulacaoIavp,
    "outras_informacoes": AgenteOutrasInformacoesFonar,
    "sobre_agressor": AgenteSobreAgressorFonar,
    "violencia_vicaria": AgenteViolenciaVicariaIavp
}

# =====================================================================
# 2. CONFIGURAÇÃO DOS MODELOS E PROMPTS
# =====================================================================

# LLM Extrator (Temperatura 0 para precisão matemática nos JSONs)
llm_extrator = ChatOllama(model="gemma3:12b", temperature=0)

# LLM Conversacional (Temperatura 0.6 para ser um pouco mais empático e natural)
llm_chat = ChatOllama(model="gemma3:12b", temperature=0.6)

# Prompt dos Agentes de Extração (O segredo da atualização contínua)
prompt_extracao = ChatPromptTemplate.from_messages([
    ("system", """Você é um extrator de dados frio e objetivo para um sistema jurídico.
    Resumo atual do caso: {resumo_atual}
    
    REGRAS DE OURO DA EXTRAÇÃO:
    1. Extraia dados APENAS da 'Nova mensagem' abaixo.
    2. SEJA ESTRITO COM OS ENUMS: Nunca invente valores que não estão na lista de opções. Se a resposta exata não estiver na lista, retorne null.
    3. Na dúvida, ou se a informação não estiver EXPLICITAMENTE na nova mensagem, retorne null obrigatoriamente."""),
    ("user", "Nova mensagem da vítima: {mensagem}")
])

# Construindo as "Chains" (Correntes) dinamicamente
chains_extracao = {
    nome: prompt_extracao | llm_extrator.with_structured_output(schema)
    for nome, schema in SCHEMAS_AGENTES.items()
}

# Chain separada para a Síntese (Ela precisa atualizar o resumo global)
chain_sintese = prompt_extracao | llm_extrator.with_structured_output(AgenteSinteseGeral)

# Prompt do Chatbot que fala com a usuária
prompt_chat = ChatPromptTemplate.from_messages([
    ("system", """Você é um assistente virtual de acolhimento à mulher do Ministério Público.
    Seja empático, breve e faça apenas UMA pergunta por vez para guiá-la.
    Resumo do que já sabemos para você ter contexto: {resumo_atual}
    Dados estruturados confirmados: {estado_json}"""),
    ("user", "{mensagem}")
])
chain_conversa = prompt_chat | llm_chat

# =====================================================================
# 3. LÓGICA DE DELTA (ATUALIZAÇÃO DO ESTADO E IMPRESSÃO DE NOVIDADES)
# =====================================================================

def atualizar_estado_e_pegar_mudancas(estado_global, novos_dados_agentes):
    mudancas_neste_turno = {}
    
    for nome_agente, dados_extraidos in novos_dados_agentes.items():
        if dados_extraidos is None: continue
        
        # Converte o objeto Pydantic para dicionário
        dict_dados = dados_extraidos.dict()
        
        for chave, novo_valor in dict_dados.items():
            # Ignoramos nulos, listas vazias ou strings vazias que a IA cuspiu
            if novo_valor is not None and novo_valor != [] and novo_valor != "":
                
                # Se o valor for novo ou diferente do que já tínhamos, é um Delta!
                if estado_global.get(chave) != novo_valor:
                    mudancas_neste_turno[chave] = novo_valor
                    estado_global[chave] = novo_valor # Salva no estado principal
                    
    return mudancas_neste_turno

# =====================================================================
# 4. LOOP PRINCIPAL DE EXECUÇÃO
# =====================================================================

async def iniciar_atendimento():
    estado_global_formulario = {}
    resumo_atual = "Nenhuma informação coletada ainda."
    
    print("\n" + "="*50)
    print("🤖 SISTEMA DE TRIAGEM ATIVADO (Pressione Ctrl+C para sair)")
    print("="*50 + "\n")
    
    print("Assistente: Olá. Sinto muito que esteja passando por isso. Estou aqui para te ouvir de forma segura. O que aconteceu?")
    
    while True:
        try:
            mensagem_vitima = input("\n👤 Vítima: ")
            
            # --- PASSO 1: Disparar todos os agentes ao mesmo tempo (Paralelismo) ---
            tarefas_extracao = [
                chain.ainvoke({"resumo_atual": resumo_atual, "mensagem": mensagem_vitima})
                for chain in chains_extracao.values()
            ]
            
            # Executa as extrações + a síntese na GPU simultaneamente
            resultados = await asyncio.gather(
                *tarefas_extracao, 
                chain_sintese.ainvoke({"resumo_atual": resumo_atual, "mensagem": mensagem_vitima})
            )
            
            # Desempacota resultados
            resultados_agentes = dict(zip(chains_extracao.keys(), resultados[:-1]))
            resultado_sintese = resultados[-1]
            
            # --- PASSO 2: Calcular o Delta e Atualizar ---
            mudancas = atualizar_estado_e_pegar_mudancas(estado_global_formulario, resultados_agentes)
            
            # Atualiza o resumo se a IA gerou um novo
            if resultado_sintese and resultado_sintese.resumo_geral_do_relato:
                resumo_atual = resultado_sintese.resumo_geral_do_relato
            
            # --- PASSO 3: Mostrar apenas o que mudou (Para o seu Debug/Demo) ---
            if mudancas:
                print("\n" + "-"*40)
                print("⚙️ [DEBUG] FORMULÁRIO ATUALIZADO NESTE TURNO:")
                print(json.dumps(mudancas, indent=2, ensure_ascii=False))
                print("-"*40)
            else:
                print("\n⚙️ [DEBUG] Nenhuma alteração estruturada no formulário neste turno.")
                
            # --- PASSO 4: Gerar resposta para a vítima ---
            resposta_ia = await chain_conversa.ainvoke({
                "resumo_atual": resumo_atual,
                "estado_json": json.dumps(estado_global_formulario, ensure_ascii=False),
                "mensagem": mensagem_vitima
            })
            
            print(f"\n👩‍⚖️ Assistente: {resposta_ia.content}")

        except KeyboardInterrupt:
            print("\n\n🛑 Encerrando atendimento.")
            print("\n📊 ESTADO FINAL DO FORMULÁRIO COMPLETO:")
            print(json.dumps(estado_global_formulario, indent=4, ensure_ascii=False))
            break

# Inicia o programa
if __name__ == "__main__":
    asyncio.run(iniciar_atendimento())