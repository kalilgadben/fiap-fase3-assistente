import os
import json
from datasets import load_dataset

def baixar_pubmedqa():
    print("=" * 50)
    print("Baixando dataset PubMedQA...")
    print("=" * 50)

    try:
        dataset = load_dataset("qiaojin/PubMedQA", "pqa_labeled", trust_remote_code=True)
        print(f"Dataset baixado com sucesso!")
        print(f"Total de exemplos: {len(dataset['train'])}")
    except Exception as e:
        print(f"Erro ao baixar dataset: {e}")
        print("Verifique sua conexão com a internet e tente novamente.")
        return None

    print("\nExemplo de um dado do dataset:")
    exemplo = dataset['train'][0]
    print(f"  Pergunta: {exemplo['question'][:100]}...")
    print(f"  Resposta longa: {str(exemplo['long_answer'])[:100]}...")
    print(f"  Resposta final: {exemplo['final_decision']}")

    caminho_saida = os.path.join(os.path.dirname(__file__), "brutos", "pubmedqa_raw.json")

    dados_para_salvar = []
    for item in dataset['train']:
        dados_para_salvar.append({
            "pergunta": item['question'],
            "contexto": str(item['context']),
            "resposta_longa": str(item['long_answer']),
            "decisao_final": item['final_decision']
        })

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(dados_para_salvar, f, ensure_ascii=False, indent=2)

    print(f"\nDados salvos em: {caminho_saida}")
    print(f"Total de registros salvos: {len(dados_para_salvar)}")

    return dados_para_salvar


if __name__ == "__main__":
    dados = baixar_pubmedqa()
    if dados:
        print("\n✓ Download concluído com sucesso!")
    else:
        print("\n✗ Falha no download.")
