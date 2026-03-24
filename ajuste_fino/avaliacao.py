import os
import json
import math
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

def carregar_modelo_treinado():
    caminho = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "modelos", "gpt2_medico", "modelo_final")
    )
    print(f"Carregando modelo treinado de: {caminho}")

    try:
        tokenizador = GPT2Tokenizer.from_pretrained(caminho)
        modelo = GPT2LMHeadModel.from_pretrained(caminho)
        print("Modelo treinado carregado!")
        return modelo, tokenizador
    except Exception as e:
        print(f"Erro ao carregar modelo treinado: {e}")
        print("Você já rodou o treinamento? Execute primeiro: python ajuste_fino/treinamento.py")
        return None, None


def carregar_modelo_base():
    print("Carregando modelo GPT-2 base (sem fine-tuning)...")
    tokenizador = GPT2Tokenizer.from_pretrained('gpt2')
    modelo = GPT2LMHeadModel.from_pretrained('gpt2')
    tokenizador.pad_token = tokenizador.eos_token
    return modelo, tokenizador


def calcular_perplexidade(modelo, tokenizador, textos):

    modelo.eval()
    total_loss = 0
    total_tokens = 0

    with torch.no_grad():
        for texto in textos:
            tokens = tokenizador.encode(
                texto,
                return_tensors='pt',
                truncation=True,
                max_length=512
            )

            saidas = modelo(tokens, labels=tokens)
            loss = saidas.loss

            total_loss += loss.item() * tokens.size(1)
            total_tokens += tokens.size(1)

    perplexidade = math.exp(total_loss / total_tokens)
    return perplexidade


def gerar_resposta(modelo, tokenizador, pergunta, max_tokens=150):

    prompt = f"<|inicio|>Pergunta: {pergunta}\nResposta:"

    tokens_entrada = tokenizador.encode(prompt, return_tensors='pt')

    with torch.no_grad():
        tokens_saida = modelo.generate(
            tokens_entrada,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizador.eos_token_id,
            repetition_penalty=1.2
        )

    resposta_completa = tokenizador.decode(tokens_saida[0], skip_special_tokens=True)

    if "Resposta:" in resposta_completa:
        resposta = resposta_completa.split("Resposta:")[-1].strip()
    else:
        resposta = resposta_completa

    for marcador in ["Pergunta:", "<|inicio|>", "\n\n"]:
        if marcador in resposta:
            resposta = resposta.split(marcador)[0].strip()

    return resposta


def comparar_modelos():

    print("=" * 60)
    print("  AVALIAÇÃO DO MODELO - COMPARAÇÃO BASE vs FINE-TUNED")
    print("=" * 60)

    modelo_treinado, tok_treinado = carregar_modelo_treinado()
    if modelo_treinado is None:
        return

    modelo_base, tok_base = carregar_modelo_base()

    caminho_teste = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "dados", "processados", "teste.json")
    )
    with open(caminho_teste, 'r', encoding='utf-8') as f:
        dados_teste = json.load(f)

    textos_teste = [item['texto'] for item in dados_teste[:20]]  # usando 20 exemplos

    print("\n1. CÁLCULO DE PERPLEXIDADE")
    print("-" * 40)

    perp_base = calcular_perplexidade(modelo_base, tok_base, textos_teste)
    print(f"   GPT-2 Base:       {perp_base:.2f}")

    perp_treinado = calcular_perplexidade(modelo_treinado, tok_treinado, textos_teste)
    print(f"   GPT-2 Fine-tuned: {perp_treinado:.2f}")

    melhoria = ((perp_base - perp_treinado) / perp_base) * 100
    print(f"\n   Melhoria: {melhoria:.1f}%")
    if melhoria > 0:
        print("   -> O fine-tuning MELHOROU o modelo para textos médicos!")
    else:
        print("   -> O modelo base teve performance similar. Pode ser necessário mais dados/épocas.")

    print("\n\n2. COMPARAÇÃO DE RESPOSTAS")
    print("-" * 40)

    perguntas_teste = [
        "What are the common symptoms of diabetes?",
        "How is hypertension diagnosed?",
        "What treatment options exist for pneumonia?",
    ]

    for pergunta in perguntas_teste:
        print(f"\nPergunta: {pergunta}")
        print()

        resposta_base = gerar_resposta(modelo_base, tok_base, pergunta)
        print(f"  [GPT-2 Base]:       {resposta_base[:200]}")

        resposta_treinada = gerar_resposta(modelo_treinado, tok_treinado, pergunta)
        print(f"  [GPT-2 Fine-tuned]: {resposta_treinada[:200]}")

        print()

    resultados = {
        "perplexidade_base": perp_base,
        "perplexidade_finetuned": perp_treinado,
        "melhoria_percentual": melhoria,
        "exemplos_respostas": [
            {"pergunta": p, "resposta_finetuned": gerar_resposta(modelo_treinado, tok_treinado, p)}
            for p in perguntas_teste
        ]
    }

    caminho_resultado = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "dados", "processados", "resultados_avaliacao.json")
    )
    with open(caminho_resultado, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos em: {caminho_resultado}")


if __name__ == "__main__":
    comparar_modelos()
    print("\nAvaliação finalizada!")
