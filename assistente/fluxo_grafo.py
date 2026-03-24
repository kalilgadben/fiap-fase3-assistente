import os
import sys
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from assistente.banco_dados import (
    montar_contexto_paciente,
    buscar_exames_pendentes,
    buscar_paciente,
    listar_pacientes
)
from assistente.seguranca import validador


class EstadoAssistente(TypedDict):
    pergunta: str
    paciente_id: Optional[int]
    tipo_consulta: str
    contexto_paciente: str
    exames_pendentes: list
    resposta_llm: str
    resposta_final: str
    fontes: list
    alertas: list
    bloqueado: bool



def no_triagem(estado: EstadoAssistente) -> EstadoAssistente:

    print("  [Triagem] Classificando pergunta...")

    pergunta = estado["pergunta"].lower()

    palavras_exame = ["exame", "resultado", "laborat", "raio", "tomografia", "ressonância", "pendente"]
    palavras_tratamento = ["tratamento", "medicamento", "medicação", "dose", "prescrição", "procedimento"]

    tipo = "clinica"

    for palavra in palavras_exame:
        if palavra in pergunta:
            tipo = "exame"
            break

    for palavra in palavras_tratamento:
        if palavra in pergunta:
            tipo = "tratamento"
            break

    print(f"  [Triagem] Tipo identificado: {tipo}")

    estado["tipo_consulta"] = tipo
    estado["alertas"] = []
    estado["fontes"] = []
    estado["bloqueado"] = False

    return estado

def no_consulta_dados(estado: EstadoAssistente) -> EstadoAssistente:

    print("  [Consulta Dados] Buscando informações no banco...")

    paciente_id = estado.get("paciente_id")
    fontes = []
    alertas = []

    if paciente_id:
        contexto = montar_contexto_paciente(paciente_id)
        estado["contexto_paciente"] = contexto
        fontes.append("Banco de dados do hospital")

        tipo = estado.get("tipo_consulta", "clinica")

        pendentes = buscar_exames_pendentes(paciente_id)
        estado["exames_pendentes"] = pendentes

        if pendentes and tipo == "exame":
            nomes_exames = [e['tipo_exame'] for e in pendentes]
            alertas.append(f"ALERTA: Paciente tem {len(pendentes)} exame(s) pendente(s): {', '.join(nomes_exames)}")

        paciente = buscar_paciente(paciente_id)
        pergunta_lower = estado.get("pergunta", "").lower()
        pergunta_sobre_alergia = any(p in pergunta_lower for p in ["alergia", "alérg", "reação", "sensibilidade"])

        if paciente and paciente['alergias'] != 'Nenhuma' and (tipo == "tratamento" or pergunta_sobre_alergia):
            alertas.append(f"ALERTA: Paciente tem alergia a: {paciente['alergias']}")

    else:
        estado["contexto_paciente"] = "Consulta geral - sem paciente selecionado."
        estado["exames_pendentes"] = []

    fontes.append("Modelo fine-tuned (PubMedQA)")
    estado["fontes"] = fontes
    estado["alertas"] = alertas

    print(f"  [Consulta Dados] Fontes: {fontes}")
    if alertas:
        for alerta in alertas:
            print(f"  [Consulta Dados] {alerta}")

    return estado

def no_geracao_resposta(estado: EstadoAssistente) -> EstadoAssistente:

    print("  [Geração] Gerando resposta com o LLM...")

    from assistente.cadeia_llm import criar_cadeia, consultar_assistente

    try:
        cadeia = criar_cadeia()
        resposta, fontes_llm = consultar_assistente(
            cadeia,
            estado["pergunta"],
            estado.get("paciente_id")
        )
        estado["resposta_llm"] = resposta
        estado["fontes"] = list(set(estado["fontes"] + fontes_llm))

    except Exception as e:
        print(f"  [Geração] Erro: {e}")
        estado["resposta_llm"] = (
            "Não foi possível gerar uma resposta no momento. "
            "Por favor, consulte os protocolos diretamente ou tente novamente."
        )

    print(f"  [Geração] Resposta gerada ({len(estado['resposta_llm'])} caracteres)")
    return estado


def no_validacao(estado: EstadoAssistente) -> EstadoAssistente:

    print("  [Validação] Validando resposta...")

    resposta_validada = validador.validar_resposta(
        pergunta=estado["pergunta"],
        resposta=estado["resposta_llm"],
        fontes=estado["fontes"],
        paciente_id=estado.get("paciente_id")
    )

    if estado["alertas"]:
        texto_alertas = "\n\n🚨 ALERTAS:\n"
        for alerta in estado["alertas"]:
            texto_alertas += f"  {alerta}\n"
        resposta_validada = texto_alertas + "\n" + resposta_validada

    if "BLOQUEADA" in resposta_validada:
        estado["bloqueado"] = True

    estado["resposta_final"] = resposta_validada

    print(f"  [Validação] Status: {'BLOQUEADA' if estado['bloqueado'] else 'APROVADA'}")
    return estado


def criar_grafo():

    print("Montando grafo de decisão...")

    grafo = StateGraph(EstadoAssistente)

    grafo.add_node("triagem", no_triagem)
    grafo.add_node("consulta_dados", no_consulta_dados)
    grafo.add_node("geracao_resposta", no_geracao_resposta)
    grafo.add_node("validacao", no_validacao)

    grafo.set_entry_point("triagem")
    grafo.add_edge("triagem", "consulta_dados")
    grafo.add_edge("consulta_dados", "geracao_resposta")
    grafo.add_edge("geracao_resposta", "validacao")
    grafo.add_edge("validacao", END)

    fluxo = grafo.compile()

    print("Grafo montado com sucesso!")
    print("  Fluxo: triagem -> consulta_dados -> geracao_resposta -> validacao -> FIM")

    return fluxo


def executar_fluxo(pergunta, paciente_id=None):

    print("\n" + "=" * 50)
    print("Executando fluxo do assistente...")
    print("=" * 50)

    fluxo = criar_grafo()

    estado_inicial = {
        "pergunta": pergunta,
        "paciente_id": paciente_id,
        "tipo_consulta": "",
        "contexto_paciente": "",
        "exames_pendentes": [],
        "resposta_llm": "",
        "resposta_final": "",
        "fontes": [],
        "alertas": [],
        "bloqueado": False,
    }

    resultado = fluxo.invoke(estado_inicial)

    print("=" * 50)
    print("Fluxo concluído!")

    return resultado


if __name__ == "__main__":
    from assistente.banco_dados import criar_banco
    criar_banco()

    print("\n\nTeste 1 - Pergunta sobre exames do paciente 1:")
    resultado = executar_fluxo(
        "Quais exames estão pendentes para este paciente?",
        paciente_id=1
    )
    print("\nRESPOSTA FINAL:")
    print(resultado["resposta_final"])
