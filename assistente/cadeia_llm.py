import os
import re
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from assistente.banco_dados import (
    montar_contexto_paciente,
    buscar_paciente,
    buscar_exames_paciente,
    buscar_exames_pendentes,
    buscar_tratamentos_paciente,
)

CAMINHO_MODELO = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "modelos", "gpt2_medico", "modelo_final")
)


def carregar_llm():

    print("Carregando modelo fine-tuned para o LangChain...")

    try:
        tokenizador = GPT2Tokenizer.from_pretrained(CAMINHO_MODELO)
        modelo = GPT2LMHeadModel.from_pretrained(CAMINHO_MODELO)
    except Exception as e:
        print(f"Erro ao carregar modelo: {e}")
        print("Usando GPT-2 base como fallback...")
        tokenizador = GPT2Tokenizer.from_pretrained('gpt2')
        modelo = GPT2LMHeadModel.from_pretrained('gpt2')
        tokenizador.pad_token = tokenizador.eos_token

    pipe_geracao = pipeline(
        "text-generation",
        model=modelo,
        tokenizer=tokenizador,
        max_new_tokens=150,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.3,
        do_sample=True,
    )

    llm = HuggingFacePipeline(pipeline=pipe_geracao)

    print("Modelo carregado e integrado ao LangChain!")
    return llm


def criar_template_prompt():

    template = """Você é um assistente médico do hospital. Sua função é auxiliar médicos
com informações baseadas em protocolos internos e dados do paciente.

REGRAS IMPORTANTES:
- NUNCA prescreva medicamentos diretamente
- Sempre sugira, nunca ordene
- Indique quando uma informação precisa de validação humana
- Baseie suas respostas nos dados disponíveis

{contexto_paciente}

Pergunta do médico: {pergunta}

Resposta do assistente:"""

    prompt = PromptTemplate(
        input_variables=["contexto_paciente", "pergunta"],
        template=template
    )

    return prompt


def criar_cadeia(llm=None):

    if llm is None:
        llm = carregar_llm()

    prompt = criar_template_prompt()

    cadeia = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=False
    )

    return cadeia


def _detectar_idioma_portugues(texto):

    palavras_pt = {
        "que", "não", "para", "com", "uma", "são", "dos", "das", "por",
        "como", "mais", "foi", "tem", "ser", "está", "pode", "este",
        "esta", "esse", "essa", "pelo", "pela", "sobre", "após", "entre",
        "deve", "cada", "quando", "também", "ainda", "muito", "outros",
        "onde", "mesmo", "suas", "seus", "nas", "nos", "aos", "ela",
        "ele", "isso", "isto", "aqui", "ter", "seu", "sua", "há",
        "já", "até", "bem", "assim", "então", "mas", "porém", "porque",
        "paciente", "exame", "médico", "tratamento", "doença", "clínico",
        "saúde", "resultado", "diagnóstico", "sintomas", "medicamento",
    }

    palavras_texto = set(re.findall(r'\b\w+\b', texto.lower()))

    encontradas = palavras_texto.intersection(palavras_pt)

    if len(palavras_texto) == 0:
        return False

    proporcao = len(encontradas) / len(palavras_texto)
    return proporcao > 0.05


def limpar_resposta_llm(texto_bruto):

    if not texto_bruto or not texto_bruto.strip():
        return ""

    texto = texto_bruto.strip()

    marcadores_fim = [
        "Pergunta do médico:", "REGRAS IMPORTANTES:", "Você é um assistente",
        "<|endoftext|>", "<|inicio|>", "<|fim|>", "<|pad|>",
        "---", "===", "***",
    ]
    for marcador in marcadores_fim:
        if marcador in texto:
            texto = texto.split(marcador)[0].strip()

    if not _detectar_idioma_portugues(texto):
        return ""

    frases = re.split(r'(?<=[.!?;])\s+', texto)
    frases_limpas = []

    for frase in frases:
        frase = frase.strip()
        if not frase:
            continue

        palavras = frase.split()
        if len(palavras) < 3:
            continue

        if not _detectar_idioma_portugues(frase):
            continue

        caracteres_alfa = sum(1 for c in frase if c.isalpha() or c.isspace())
        if len(frase) > 0 and caracteres_alfa / len(frase) < 0.6:
            continue

        tem_palavra_gigante = any(len(p) > 25 for p in palavras)
        if tem_palavra_gigante:
            continue

        palavras_unicas = set(p.lower() for p in palavras)
        if len(palavras) > 5 and len(palavras_unicas) / len(palavras) < 0.4:
            continue

        if len(palavras) > 60:
            continue

        frases_limpas.append(frase)

    resultado = " ".join(frases_limpas)

    if len(resultado) < 20:
        return ""

    return resultado


def gerar_resposta_banco(pergunta, paciente_id):

    if not paciente_id:
        return "Para uma resposta mais precisa, selecione um paciente com /selecionar <id>."

    paciente = buscar_paciente(paciente_id)
    if not paciente:
        return f"Paciente ID {paciente_id} não encontrado no sistema."

    pergunta_lower = pergunta.lower()
    resposta_partes = []

    quer_exames = any(p in pergunta_lower for p in [
        "exame", "resultado", "laborat", "pendente", "raio", "tomografia"
    ])
    quer_tratamento = any(p in pergunta_lower for p in [
        "tratamento", "medicamento", "medicação", "remédio", "dose", "medica"
    ])
    quer_resumo = any(p in pergunta_lower for p in [
        "resumo", "quadro", "condição", "situação", "como está", "status", "geral"
    ])
    quer_alergia = any(p in pergunta_lower for p in [
        "alergia", "alérg", "reação", "sensibilidade"
    ])

    if not any([quer_exames, quer_tratamento, quer_resumo, quer_alergia]):
        quer_resumo = True

    if quer_resumo:
        resposta_partes.append(
            f"O paciente {paciente['nome']} tem {paciente['idade']} anos, "
            f"sexo {paciente['sexo']}, com condição principal: {paciente['condicao_principal']}."
        )
        if paciente['alergias'] != 'Nenhuma':
            resposta_partes.append(f"Possui alergia registrada a: {paciente['alergias']}.")
        resposta_partes.append(f"Data de admissão: {paciente['data_admissao']}.")

    if quer_exames or quer_resumo:
        exames = buscar_exames_paciente(paciente_id)
        pendentes = [e for e in exames if e['status'] == 'pendente']
        concluidos = [e for e in exames if e['status'] == 'concluido']

        if concluidos:
            resposta_partes.append("\nExames concluídos:")
            for e in concluidos:
                resposta_partes.append(f"  - {e['tipo_exame']}: {e['resultado']} ({e['data_solicitacao']})")

        if pendentes:
            resposta_partes.append("\nExames pendentes:")
            for e in pendentes:
                resposta_partes.append(f"  - {e['tipo_exame']} (solicitado em {e['data_solicitacao']})")
            resposta_partes.append(
                "\nSugestão: acompanhar a liberação dos exames pendentes antes de ajustar a conduta."
            )
        elif quer_exames:
            resposta_partes.append("Não há exames pendentes para este paciente no momento.")

    if quer_tratamento or quer_resumo:
        tratamentos = buscar_tratamentos_paciente(paciente_id)
        if tratamentos:
            resposta_partes.append("\nTratamentos em andamento:")
            for t in tratamentos:
                obs = f" - Obs: {t['observacoes']}" if t['observacoes'] else ""
                resposta_partes.append(
                    f"  - {t['medicamento']} {t['dosagem']}, {t['frequencia']}{obs}"
                )
        else:
            resposta_partes.append("Não há tratamentos registrados para este paciente.")

    if quer_alergia:
        if paciente['alergias'] != 'Nenhuma':
            resposta_partes.append(
                f"O paciente possui alergia registrada a: {paciente['alergias']}. "
                f"Considere essa informação ao avaliar condutas."
            )
        else:
            resposta_partes.append("Não há alergias registradas para este paciente.")

    return "\n".join(resposta_partes)


def consultar_assistente(cadeia, pergunta, paciente_id=None):

    if paciente_id:
        contexto = montar_contexto_paciente(paciente_id)
    else:
        contexto = "Nenhum paciente selecionado. Respondendo de forma geral."

    fontes = []
    resposta_llm_limpa = ""

    try:
        resultado = cadeia.invoke({
            "contexto_paciente": contexto,
            "pergunta": pergunta
        })

        texto_bruto = resultado.get('text', str(resultado))

        if "Resposta do assistente:" in texto_bruto:
            texto_bruto = texto_bruto.split("Resposta do assistente:")[-1].strip()

        resposta_llm_limpa = limpar_resposta_llm(texto_bruto)

        if resposta_llm_limpa:
            fontes.append("Modelo fine-tuned (PubMedQA)")

    except Exception as e:
        print(f"  [LLM] Erro na geração: {e}")
        resposta_llm_limpa = ""

    resposta_banco = ""
    if paciente_id:
        resposta_banco = gerar_resposta_banco(pergunta, paciente_id)
        fontes.append("Banco de dados do hospital")

    if resposta_llm_limpa and resposta_banco:
        resposta_final = resposta_banco + "\n\nAnálise complementar do modelo:\n" + resposta_llm_limpa
    elif resposta_banco:
        resposta_final = resposta_banco
    elif resposta_llm_limpa:
        resposta_final = resposta_llm_limpa
    else:
        resposta_final = (
            "Não foi possível gerar uma resposta precisa para esta pergunta. "
            "Sugestão: selecione um paciente com /selecionar <id> para obter "
            "informações contextualizadas, ou consulte os protocolos diretamente."
        )
        if not fontes:
            fontes.append("Nenhuma fonte disponível")

    return resposta_final, fontes


if __name__ == "__main__":
    print("Testando pipeline LangChain...\n")

    llm = carregar_llm()
    cadeia = criar_cadeia(llm)

    print("Teste 1 - Pergunta geral:")
    resposta, fontes = consultar_assistente(
        cadeia,
        "Quais são os sintomas comuns da diabetes tipo 2?"
    )
    print(f"Resposta: {resposta[:300]}")
    print(f"Fontes: {fontes}")

    print("\n\nTeste 2 - Pergunta sobre paciente:")
    resposta, fontes = consultar_assistente(
        cadeia,
        "Quais exames estão pendentes para este paciente?",
        paciente_id=1
    )
    print(f"Resposta: {resposta[:300]}")
    print(f"Fontes: {fontes}")
