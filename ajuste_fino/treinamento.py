import os
import json
import torch
from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    TextDataset,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments
)
from torch.utils.data import Dataset


class DatasetMedico(Dataset):

    def __init__(self, caminho_dados, tokenizador, tamanho_maximo=512):
        self.tokenizador = tokenizador
        self.tamanho_maximo = tamanho_maximo
        self.exemplos = []

        print(f"Carregando dados de: {caminho_dados}")
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        print(f"Tokenizando {len(dados)} exemplos...")
        for item in dados:
            texto = item['texto']
            
            tokens = tokenizador.encode(
                texto,
                truncation=True,
                max_length=self.tamanho_maximo,
                padding='max_length'
            )
            self.exemplos.append(torch.tensor(tokens))

        print(f"Dataset criado com {len(self.exemplos)} exemplos tokenizados")

    def __len__(self):
        return len(self.exemplos)

    def __getitem__(self, indice):
        return {
            'input_ids': self.exemplos[indice],
            'labels': self.exemplos[indice]
        }


def carregar_modelo_base():

    print("Carregando modelo GPT-2 Small...")

    tokenizador = GPT2Tokenizer.from_pretrained('gpt2')
    modelo = GPT2LMHeadModel.from_pretrained('gpt2')

    tokens_especiais = {
        'pad_token': '<|pad|>',
        'additional_special_tokens': ['<|inicio|>', '<|fim|>']
    }
    tokenizador.add_special_tokens(tokens_especiais)

    modelo.resize_token_embeddings(len(tokenizador))

    print(f"Modelo carregado! Parâmetros: {modelo.num_parameters():,}")
    print(f"Vocabulário: {len(tokenizador)} tokens")

    return modelo, tokenizador


def configurar_treinamento(caminho_saida):

    argumentos = TrainingArguments(
        output_dir=caminho_saida,
        overwrite_output_dir=True,
        num_train_epochs=2,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        learning_rate=5e-5,
        weight_decay=0.01,
        warmup_steps=50,
        save_steps=100,
        save_total_limit=2,
        logging_steps=10,
        logging_dir=os.path.join(caminho_saida, "logs_treino"),
        evaluation_strategy="steps",
        eval_steps=50,
        no_cuda=True,
    )

    return argumentos


def executar_treinamento():

    print("=" * 60)
    print("  FINE-TUNING DO GPT-2 COM DADOS MÉDICOS (PubMedQA)")
    print("=" * 60)

    caminho_base = os.path.join(os.path.dirname(__file__), "..")
    caminho_treino = os.path.normpath(os.path.join(caminho_base, "dados", "processados", "treino.json"))
    caminho_teste = os.path.normpath(os.path.join(caminho_base, "dados", "processados", "teste.json"))
    caminho_saida = os.path.normpath(os.path.join(caminho_base, "modelos", "gpt2_medico"))

    modelo, tokenizador = carregar_modelo_base()

    print("\nPreparando datasets...")
    dataset_treino = DatasetMedico(caminho_treino, tokenizador)
    dataset_teste = DatasetMedico(caminho_teste, tokenizador)

    print("\nConfigurando parâmetros de treinamento...")
    argumentos = configurar_treinamento(caminho_saida)

    treinador = Trainer(
        model=modelo,
        args=argumentos,
        train_dataset=dataset_treino,
        eval_dataset=dataset_teste,
    )

    print("\nIniciando treinamento...")
    print("(isso pode demorar um pouco em CPU, tenha paciência)")
    print("-" * 60)

    resultado = treinador.train()

    print("\nSalvando modelo treinado...")
    caminho_modelo_final = os.path.join(caminho_saida, "modelo_final")
    modelo.save_pretrained(caminho_modelo_final)
    tokenizador.save_pretrained(caminho_modelo_final)

    print(f"\nModelo salvo em: {caminho_modelo_final}")

    print("\n" + "=" * 60)
    print("RESULTADOS DO TREINAMENTO:")
    print(f"  Loss final: {resultado.training_loss:.4f}")
    print(f"  Steps totais: {resultado.global_step}")
    print("=" * 60)

    return modelo, tokenizador


if __name__ == "__main__":
    modelo, tokenizador = executar_treinamento()
    print("\nTreinamento finalizado com sucesso!")
