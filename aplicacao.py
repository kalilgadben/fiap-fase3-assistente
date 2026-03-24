import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assistente.banco_dados import criar_banco, listar_pacientes, buscar_paciente
from assistente.fluxo_grafo import executar_fluxo
from assistente.seguranca import validador

def mostrar_banner():
    print()
    print("=" * 60)
    print("  ASSISTENTE MÉDICO VIRTUAL - Hospital Tech Challenge")
    print("  Fine-tuned com PubMedQA + LangChain + LangGraph")
    print("=" * 60)
    print()
    print("  Comandos disponíveis:")
    print("    /pacientes  - Lista todos os pacientes")
    print("    /selecionar - Seleciona um paciente pelo ID")
    print("    /info       - Mostra info do paciente selecionado")
    print("    /logs       - Mostra estatísticas de uso")
    print("    /sair       - Encerra o assistente")
    print()


def listar_todos_pacientes():
    pacientes = listar_pacientes()
    print("\n  Pacientes cadastrados:")
    print("  " + "-" * 50)
    for p in pacientes:
        print(f"  ID {p['id']:>2} | {p['nome']:<15} | {p['idade']} anos | {p['condicao_principal']}")
    print("  " + "-" * 50)
    print()


def mostrar_info_paciente(paciente_id):
    from assistente.banco_dados import montar_contexto_paciente

    paciente = buscar_paciente(paciente_id)
    if not paciente:
        print(f"  Paciente ID {paciente_id} não encontrado.")
        return

    print(montar_contexto_paciente(paciente_id))


def mostrar_estatisticas():
    stats = validador.obter_estatisticas()
    print("\n  Estatísticas de uso:")
    print(f"    Total de consultas: {stats['total_consultas']}")
    print(f"    Respostas bloqueadas: {stats['respostas_bloqueadas']}")
    print(f"    Taxa de bloqueio: {stats['taxa_bloqueio']}")
    print(f"    Log salvo em: logs/auditoria.log")
    print()


def executar():
    mostrar_banner()

    print("Inicializando banco de dados...")
    criar_banco()

    paciente_selecionado = None
    print("\nAssistente pronto! Digite sua pergunta ou um comando.\n")

    while True:
        if paciente_selecionado:
            paciente = buscar_paciente(paciente_selecionado)
            nome = paciente['nome'] if paciente else "?"
            prompt = f"[{nome}] > "
        else:
            prompt = "[Nenhum paciente] > "

        try:
            entrada = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nEncerrando assistente...")
            break

        if not entrada:
            continue

        if entrada.lower() == "/sair":
            print("\nEncerrando assistente. Até logo!")
            break

        elif entrada.lower() == "/pacientes":
            listar_todos_pacientes()
            continue

        elif entrada.lower().startswith("/selecionar"):
            partes = entrada.split()
            if len(partes) > 1:
                try:
                    paciente_selecionado = int(partes[1])
                    paciente = buscar_paciente(paciente_selecionado)
                    if paciente:
                        print(f"\n  Paciente selecionado: {paciente['nome']} (ID {paciente_selecionado})")
                        print(f"  Condição: {paciente['condicao_principal']}")
                        print()
                    else:
                        print(f"  Paciente ID {paciente_selecionado} não encontrado.")
                        paciente_selecionado = None
                except ValueError:
                    print("  Use: /selecionar <id>  (exemplo: /selecionar 1)")
            else:
                print("  Use: /selecionar <id>  (exemplo: /selecionar 1)")
            continue

        elif entrada.lower() == "/info":
            if paciente_selecionado:
                mostrar_info_paciente(paciente_selecionado)
            else:
                print("  Nenhum paciente selecionado. Use /selecionar <id>")
            continue

        elif entrada.lower() == "/logs":
            mostrar_estatisticas()
            continue

        elif entrada.startswith("/"):
            print(f"  Comando desconhecido: {entrada}")
            print("  Comandos: /pacientes, /selecionar, /info, /logs, /sair")
            continue

        print("\nProcessando sua consulta...")

        try:
            resultado = executar_fluxo(entrada, paciente_selecionado)
            print("\n" + "=" * 60)
            print("RESPOSTA DO ASSISTENTE:")
            print("=" * 60)
            print(resultado["resposta_final"])
            print("=" * 60)
            print()

        except Exception as e:
            print(f"\nErro ao processar: {e}")
            print("Tente novamente ou reformule sua pergunta.\n")


if __name__ == "__main__":
    executar()
