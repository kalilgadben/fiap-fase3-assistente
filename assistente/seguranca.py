import os
import logging
from datetime import datetime

caminho_logs = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "logs")
)
os.makedirs(caminho_logs, exist_ok=True)

logger_auditoria = logging.getLogger("assistente_medico")
logger_auditoria.setLevel(logging.INFO)

arquivo_log = os.path.join(caminho_logs, "auditoria.log")
handler_arquivo = logging.FileHandler(arquivo_log, encoding='utf-8')
handler_arquivo.setLevel(logging.INFO)

formato = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler_arquivo.setFormatter(formato)
logger_auditoria.addHandler(handler_arquivo)

handler_console = logging.StreamHandler()
handler_console.setLevel(logging.WARNING) 
handler_console.setFormatter(formato)
logger_auditoria.addHandler(handler_console)

TERMOS_PRESCRICAO = [
    "prescrevo",
    "receito",
    "tome",
    "tomar imediatamente",
    "administre",
    "aplique",
    "inicie o tratamento com",
    "suspenda o uso de",
    "pare de tomar",
    "aumente a dose",
    "diminua a dose",
]

DISCLAIMER = (
    "\n\n⚠️  AVISO: Esta é uma sugestão baseada em dados e protocolos internos. "
    "NÃO substitui a avaliação e decisão do médico responsável. "
    "Toda conduta deve ser validada por um profissional antes de ser aplicada."
)


class ValidadorSeguranca:

    def __init__(self):
        self.total_consultas = 0
        self.respostas_bloqueadas = 0

    def verificar_prescricao_direta(self, resposta):
        resposta_lower = resposta.lower()

        termos_encontrados = []
        for termo in TERMOS_PRESCRICAO:
            if termo.lower() in resposta_lower:
                termos_encontrados.append(termo)

        if termos_encontrados:
            logger_auditoria.warning(
                f"PRESCRIÇÃO DETECTADA - Termos encontrados: {termos_encontrados}"
            )
            return True, termos_encontrados

        return False, []

    def adicionar_disclaimer(self, resposta):
        return resposta + DISCLAIMER

    def adicionar_fonte(self, resposta, fontes):
        texto_fontes = "\n\n📋 Fontes utilizadas:"
        for fonte in fontes:
            texto_fontes += f"\n  • {fonte}"

        return resposta + texto_fontes

    def validar_resposta(self, pergunta, resposta, fontes=None, paciente_id=None):
        self.total_consultas += 1

        logger_auditoria.info(f"CONSULTA #{self.total_consultas}")
        logger_auditoria.info(f"  Pergunta: {pergunta}")
        if paciente_id:
            logger_auditoria.info(f"  Paciente ID: {paciente_id}")

        tem_prescricao, termos = self.verificar_prescricao_direta(resposta)

        if tem_prescricao:
            self.respostas_bloqueadas += 1
            resposta_bloqueada = (
                "⛔ RESPOSTA BLOQUEADA POR SEGURANÇA\n\n"
                "A resposta original continha termos de prescrição direta, "
                "o que não é permitido. O assistente pode apenas SUGERIR "
                "condutas, nunca prescrever.\n\n"
                f"Termos detectados: {', '.join(termos)}\n\n"
                "Por favor, reformule sua pergunta pedindo sugestões ou "
                "informações sobre protocolos."
            )
            logger_auditoria.warning(f"  RESPOSTA BLOQUEADA - Termos: {termos}")
            return resposta_bloqueada

        if fontes:
            resposta = self.adicionar_fonte(resposta, fontes)

        resposta = self.adicionar_disclaimer(resposta)

        logger_auditoria.info(f"  Resposta: {resposta[:200]}...")
        logger_auditoria.info(f"  Fontes: {fontes}")
        logger_auditoria.info(f"  Status: APROVADA")

        return resposta

    def obter_estatisticas(self):
        return {
            "total_consultas": self.total_consultas,
            "respostas_bloqueadas": self.respostas_bloqueadas,
            "taxa_bloqueio": (
                f"{(self.respostas_bloqueadas / self.total_consultas * 100):.1f}%"
                if self.total_consultas > 0 else "0%"
            )
        }


validador = ValidadorSeguranca()


if __name__ == "__main__":
    print("Testando módulo de segurança...\n")

    resposta_ok = "Com base nos protocolos, o paciente pode se beneficiar de fisioterapia respiratória."
    resultado = validador.validar_resposta(
        pergunta="Qual conduta sugerida para o paciente com DPOC?",
        resposta=resposta_ok,
        fontes=["Protocolo interno - DPOC", "PubMedQA"],
        paciente_id=5
    )
    print("Teste 1 - Resposta normal:")
    print(resultado)

    print("\n" + "=" * 50)

    resposta_ruim = "Prescrevo Amoxicilina 500mg. Tome 3 vezes ao dia por 7 dias."
    resultado = validador.validar_resposta(
        pergunta="O que fazer com esse paciente com pneumonia?",
        resposta=resposta_ruim,
        fontes=["Protocolo interno - Pneumonia"],
        paciente_id=3
    )
    print("\nTeste 2 - Resposta com prescrição:")
    print(resultado)

    print("\n" + "=" * 50)
    print(f"\nEstatísticas: {validador.obter_estatisticas()}")
    print(f"Log salvo em: {arquivo_log}")
