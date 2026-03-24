import os
import re
import json


def carregar_dados_brutos():
    caminho = os.path.join(os.path.dirname(__file__), "..", "dados", "brutos", "pubmedqa_raw.json")
    caminho = os.path.normpath(caminho)

    print(f"Carregando dados de: {caminho}")

    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    print(f"Dados carregados: {len(dados)} registros")
    return dados


def anonimizar_texto(texto):

    texto = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL_REMOVIDO]', texto)
    texto = re.sub(r'\b\d{2,3}[-.\s]?\d{4,5}[-.\s]?\d{4}\b', '[TELEFONE_REMOVIDO]', texto)
    texto = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATA_REMOVIDA]', texto)
    texto = re.sub(r'\b(Patient|Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+\b', '[NOME_REMOVIDO]', texto)

    return texto


def formatar_para_treinamento(dados_brutos):

    dados_formatados = []

    for item in dados_brutos:
        pergunta = anonimizar_texto(item['pergunta'])
        contexto = anonimizar_texto(item['contexto'])
        resposta = anonimizar_texto(item['resposta_longa'])

        texto_treinamento = (
            f"<|inicio|>"
            f"Pergunta: {pergunta}\n"
            f"Contexto: {contexto[:500]}\n" 
            f"Resposta: {resposta}"
            f"<|fim|>"
        )

        dados_formatados.append({
            "texto": texto_treinamento,
            "decisao": item['decisao_final']
        })

    return dados_formatados


def dividir_treino_teste(dados, proporcao_treino=0.8):

    import random
    random.seed(42)

    dados_embaralhados = dados.copy()
    random.shuffle(dados_embaralhados)

    ponto_corte = int(len(dados_embaralhados) * proporcao_treino)
    treino = dados_embaralhados[:ponto_corte]
    teste = dados_embaralhados[ponto_corte:]

    return treino, teste


def salvar_dados_processados(treino, teste):

    caminho_base = os.path.join(os.path.dirname(__file__), "..", "dados", "processados")
    caminho_base = os.path.normpath(caminho_base)

    os.makedirs(caminho_base, exist_ok=True)

    caminho_treino = os.path.join(caminho_base, "treino.json")
    with open(caminho_treino, 'w', encoding='utf-8') as f:
        json.dump(treino, f, ensure_ascii=False, indent=2)

    caminho_teste = os.path.join(caminho_base, "teste.json")
    with open(caminho_teste, 'w', encoding='utf-8') as f:
        json.dump(teste, f, ensure_ascii=False, indent=2)

    print(f"Dados de treino salvos: {len(treino)} registros -> {caminho_treino}")
    print(f"Dados de teste salvos: {len(teste)} registros -> {caminho_teste}")


def executar_preprocessamento():
    print("=" * 50)
    print("Iniciando preprocessamento dos dados...")
    print("=" * 50)

    dados_brutos = carregar_dados_brutos()

    print("\nFormatando dados para treinamento...")
    dados_formatados = formatar_para_treinamento(dados_brutos)
    print(f"Dados formatados: {len(dados_formatados)} registros")

    print("\nExemplo de dado formatado:")
    print("-" * 40)
    print(dados_formatados[0]['texto'][:300] + "...")
    print("-" * 40)

    print("\nDividindo em treino (80%) e teste (20%)...")
    treino, teste = dividir_treino_teste(dados_formatados)

    salvar_dados_processados(treino, teste)

    print("\nPreprocessamento concluído!")
    return treino, teste


if __name__ == "__main__":
    treino, teste = executar_preprocessamento()
