# Tech Challenge - Fase 3: Assistente Médico Virtual

## Sobre o Projeto

Projeto desenvolvido para o Tech Challenge da Fase 3 da Pós-Graduação em IA da FIAP. O objetivo é criar um assistente virtual médico que utiliza **fine-tuning de LLM** com dados médicos e **LangChain/LangGraph** para auxiliar médicos em condutas clínicas.

### O que o sistema faz?
- Responde perguntas clínicas usando um modelo GPT-2 ajustado com dados do PubMedQA
- Contextualiza respostas com dados do paciente (exames, tratamentos, alergias)
- Coordena um fluxo automatizado de decisão usando LangGraph
- Garante segurança: nunca prescreve diretamente, sempre adiciona disclaimers
- Registra todas as interações em log de auditoria

## Tecnologias Utilizadas

- **Python 3.10+**
- **GPT-2 Small** (HuggingFace Transformers) - modelo base para fine-tuning
- **PubMedQA** - dataset de perguntas e respostas clínicas
- **LangChain** - orquestração do pipeline LLM
- **LangGraph** - fluxo de decisão automatizado
- **SQLite** - banco de dados simulado do hospital

## Estrutura do Projeto

```
├── dados/
│   ├── baixar_dados.py        # Download do PubMedQA
│   ├── brutos/                # Dados originais
│   └── processados/           # Dados após preprocessamento
├── ajuste_fino/
│   ├── preprocessamento.py    # Limpeza e formatação dos dados
│   ├── treinamento.py         # Fine-tuning do GPT-2
│   └── avaliacao.py           # Avaliação do modelo (perplexity)
├── assistente/
│   ├── banco_dados.py         # Banco SQLite com dados fictícios
│   ├── cadeia_llm.py          # Pipeline LangChain
│   ├── fluxo_grafo.py         # Fluxo LangGraph
│   └── seguranca.py           # Validação e logging
├── modelos/                   # Modelo treinado (gerado após treino)
├── logs/                      # Logs de auditoria
├── aplicacao.py               # Interface principal (terminal)
└── requirements.txt           # Dependências
```

## Como Instalar

1. Crie um ambiente virtual:
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

## Como Executar

### Passo 1: Baixar os dados
```
python dados/baixar_dados.py
```

### Passo 2: Preprocessar os dados
```
python ajuste_fino/preprocessamento.py
```

### Passo 3: Treinar o modelo (pode demorar em CPU)
```
python ajuste_fino/treinamento.py
```

### Passo 4: Avaliar o modelo (opcional)
```
python ajuste_fino/avaliacao.py
```

### Passo 5: Rodar o assistente
```
python aplicacao.py
```

### Comandos do Assistente
- `/pacientes` - Lista todos os pacientes
- `/selecionar <id>` - Seleciona um paciente
- `/info` - Mostra informações do paciente selecionado
- `/logs` - Mostra estatísticas de uso
- `/sair` - Encerra o assistente

## Exemplo de Uso

```
[Nenhum paciente] > /selecionar 1
  Paciente selecionado: Paciente A (ID 1)
  Condição: Diabetes Tipo 2

[Paciente A] > Quais exames estão pendentes?

  [Triagem] Classificando pergunta...
  [Consulta Dados] Buscando informações no banco...
  [Geração] Gerando resposta com o LLM...
  [Validação] Validando resposta...

  RESPOSTA DO ASSISTENTE:
  O paciente possui 1 exame pendente: Creatinina (solicitado em 2024-03-20).

  Fontes: Banco de dados do hospital, Modelo fine-tuned (PubMedQA)

  AVISO: Esta é uma sugestão. NÃO substitui a avaliação do médico responsável.
```

## Diagrama do Fluxo LangGraph

```
┌──────────┐    ┌────────────────┐    ┌──────────────────┐    ┌────────────┐   ┌───┐
│ TRIAGEM  │───>│ CONSULTA DADOS │───>│ GERAÇÃO RESPOSTA │───>│ VALIDAÇÃO  │──>|FIM|
│          │    │                │    │                  │    │            │   └───┘
│ Classif. │    │ Busca paciente │    │ LLM + contexto   │    │ Segurança  │
│ pergunta │    │ Exames pend.   │    │ gera resposta    │    │ Disclaimer │
│          │    │ Alertas        │    │                  │    │ Logging    │
└──────────┘    └────────────────┘    └──────────────────┘    └────────────┘
```

## Integrante do Grupo

- Kalil Gadben de Souza - Grupo 36

## Vídeo de Apresentação

- YouTube: https://youtu.be/z8eQnqCbfFg

## Referências

- [PubMedQA](https://pubmedqa.github.io/) - Dataset utilizado
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/) - Fine-tuning
- [LangChain](https://python.langchain.com/) - Orquestração LLM
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Fluxo de decisão
