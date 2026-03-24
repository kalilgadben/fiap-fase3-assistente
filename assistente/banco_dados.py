import os
import sqlite3

CAMINHO_BANCO = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "dados", "hospital.db")
)

def criar_banco():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            idade INTEGER,
            sexo TEXT,
            condicao_principal TEXT,
            alergias TEXT,
            data_admissao TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exames (
            id INTEGER PRIMARY KEY,
            paciente_id INTEGER,
            tipo_exame TEXT,
            resultado TEXT,
            status TEXT,
            data_solicitacao TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tratamentos (
            id INTEGER PRIMARY KEY,
            paciente_id INTEGER,
            medicamento TEXT,
            dosagem TEXT,
            frequencia TEXT,
            data_inicio TEXT,
            observacoes TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)

    pacientes = [
        (1, "Paciente A", 45, "M", "Diabetes Tipo 2", "Penicilina", "2024-01-15"),
        (2, "Paciente B", 62, "F", "Hipertensão Arterial", "Nenhuma", "2024-02-03"),
        (3, "Paciente C", 38, "M", "Pneumonia", "Sulfa", "2024-03-10"),
        (4, "Paciente D", 55, "F", "Insuficiência Cardíaca", "Aspirina", "2024-01-20"),
        (5, "Paciente E", 71, "M", "DPOC", "Nenhuma", "2024-02-28"),
        (6, "Paciente F", 29, "F", "Asma", "Ibuprofeno", "2024-03-05"),
        (7, "Paciente G", 50, "M", "Arritmia Cardíaca", "Nenhuma", "2024-01-08"),
        (8, "Paciente H", 43, "F", "Hipotireoidismo", "Látex", "2024-03-15"),
        (9, "Paciente I", 67, "M", "Insuficiência Renal", "Contraste iodado", "2024-02-12"),
        (10, "Paciente J", 34, "F", "Anemia Falciforme", "Nenhuma", "2024-03-01"),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO pacientes VALUES (?, ?, ?, ?, ?, ?, ?)",
        pacientes
    )

    exames = [
        (1, 1, "Hemoglobina Glicada", "8.5%", "concluido", "2024-01-16"),
        (2, 1, "Glicemia em Jejum", "145 mg/dL", "concluido", "2024-01-16"),
        (3, 1, "Creatinina", None, "pendente", "2024-03-20"),
        (4, 2, "Ecocardiograma", "Fração de ejeção: 55%", "concluido", "2024-02-05"),
        (5, 2, "Pressão Arterial 24h (MAPA)", None, "pendente", "2024-03-18"),
        (6, 3, "Raio-X Tórax", "Infiltrado em base direita", "concluido", "2024-03-10"),
        (7, 3, "Cultura de Escarro", None, "pendente", "2024-03-11"),
        (8, 4, "BNP", "850 pg/mL", "concluido", "2024-01-22"),
        (9, 5, "Espirometria", "VEF1: 45% do previsto", "concluido", "2024-03-01"),
        (10, 6, "Peak Flow", "320 L/min", "concluido", "2024-03-06"),
        (11, 7, "Holter 24h", None, "pendente", "2024-03-19"),
        (12, 8, "TSH", "12.5 mUI/L", "concluido", "2024-03-16"),
        (13, 9, "Creatinina", "4.2 mg/dL", "concluido", "2024-02-13"),
        (14, 9, "Ureia", None, "pendente", "2024-03-20"),
        (15, 10, "Eletroforese de Hemoglobina", "HbS: 38%", "concluido", "2024-03-02"),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO exames VALUES (?, ?, ?, ?, ?, ?)",
        exames
    )

    tratamentos = [
        (1, 1, "Metformina", "850mg", "2x ao dia", "2024-01-17", "Tomar após refeições"),
        (2, 1, "Insulina NPH", "20UI", "1x ao dia (noite)", "2024-01-17", "Aplicar no abdômen"),
        (3, 2, "Losartana", "50mg", "1x ao dia", "2024-02-05", "Tomar pela manhã"),
        (4, 2, "Hidroclorotiazida", "25mg", "1x ao dia", "2024-02-05", "Monitorar potássio"),
        (5, 3, "Amoxicilina", "500mg", "3x ao dia", "2024-03-10", "Completar 7 dias"),
        (6, 4, "Furosemida", "40mg", "1x ao dia", "2024-01-22", "Monitorar peso diário"),
        (7, 4, "Carvedilol", "6.25mg", "2x ao dia", "2024-01-22", "Iniciar dose baixa"),
        (8, 5, "Brometo de Tiotrópio", "18mcg", "1x ao dia (inalação)", "2024-03-01", "Usar de manhã"),
        (9, 6, "Budesonida/Formoterol", "200/6mcg", "2x ao dia (inalação)", "2024-03-06", "Enxaguar boca após uso"),
        (10, 8, "Levotiroxina", "75mcg", "1x ao dia (jejum)", "2024-03-16", "30min antes do café"),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO tratamentos VALUES (?, ?, ?, ?, ?, ?, ?)",
        tratamentos
    )

    conexao.commit()
    conexao.close()
    print(f"Banco de dados criado em: {CAMINHO_BANCO}")
    print(f"  - {len(pacientes)} pacientes")
    print(f"  - {len(exames)} exames")
    print(f"  - {len(tratamentos)} tratamentos")


def buscar_paciente(paciente_id):
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))
    paciente = cursor.fetchone()

    conexao.close()

    if paciente:
        return dict(paciente)
    return None


def buscar_exames_paciente(paciente_id):
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM exames WHERE paciente_id = ?", (paciente_id,))
    exames = [dict(row) for row in cursor.fetchall()]

    conexao.close()
    return exames


def buscar_exames_pendentes(paciente_id):
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT * FROM exames WHERE paciente_id = ? AND status = 'pendente'",
        (paciente_id,)
    )
    exames = [dict(row) for row in cursor.fetchall()]

    conexao.close()
    return exames


def buscar_tratamentos_paciente(paciente_id):
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM tratamentos WHERE paciente_id = ?", (paciente_id,))
    tratamentos = [dict(row) for row in cursor.fetchall()]

    conexao.close()
    return tratamentos


def listar_pacientes():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("SELECT id, nome, idade, condicao_principal FROM pacientes")
    pacientes = [dict(row) for row in cursor.fetchall()]

    conexao.close()
    return pacientes


def montar_contexto_paciente(paciente_id):

    paciente = buscar_paciente(paciente_id)
    if not paciente:
        return f"Paciente ID {paciente_id} não encontrado no sistema."

    exames = buscar_exames_paciente(paciente_id)
    tratamentos = buscar_tratamentos_paciente(paciente_id)
    pendentes = buscar_exames_pendentes(paciente_id)

    contexto = f"""
--- DADOS DO PACIENTE ---
Nome: {paciente['nome']}
Idade: {paciente['idade']} anos
Sexo: {paciente['sexo']}
Condição Principal: {paciente['condicao_principal']}
Alergias: {paciente['alergias']}
Data de Admissão: {paciente['data_admissao']}

--- EXAMES REALIZADOS ---"""

    for exame in exames:
        if exame['status'] == 'concluido':
            contexto += f"\n  • {exame['tipo_exame']}: {exame['resultado']} ({exame['data_solicitacao']})"

    if pendentes:
        contexto += "\n\n--- EXAMES PENDENTES ---"
        for exame in pendentes:
            contexto += f"\n  ⚠ {exame['tipo_exame']} (solicitado em {exame['data_solicitacao']})"

    if tratamentos:
        contexto += "\n\n--- TRATAMENTOS EM ANDAMENTO ---"
        for trat in tratamentos:
            contexto += f"\n  • {trat['medicamento']} {trat['dosagem']} - {trat['frequencia']}"
            if trat['observacoes']:
                contexto += f" ({trat['observacoes']})"

    return contexto


if __name__ == "__main__":
    print("Criando banco de dados do hospital...")
    criar_banco()

    print("\n\nPacientes cadastrados:")
    for p in listar_pacientes():
        print(f"  ID {p['id']}: {p['nome']} - {p['idade']} anos - {p['condicao_principal']}")

    print("\n\nExemplo - Contexto do Paciente 1:")
    print(montar_contexto_paciente(1))
