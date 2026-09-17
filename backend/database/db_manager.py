import sqlite3
import os
import sys
import shutil
from datetime import datetime


def _base_dir():
    """Retorna a pasta base do projeto, tanto rodando como script .py
    quanto rodando como executável gerado pelo PyInstaller."""
    if getattr(sys, "frozen", False):
        # Executando como .exe: usa a pasta onde o .exe está, para que
        # o banco de dados fique salvo ao lado dele (e não em uma pasta
        # temporária que é apagada ao fechar o programa).
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _bundle_dir():
    """Pasta onde os arquivos de dados foram empacotados dentro do .exe
    (usada apenas para copiar o banco de dados inicial na primeira execução)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# Caminho para o banco de dados SQLite (raiz do projeto, ou pasta do .exe)
db_PATH = os.path.join(_base_dir(), "escala.db")

# Na primeira execução do .exe, o banco ainda não existe ao lado dele:
# copiamos a cópia inicial que foi empacotada junto do executável.
if not os.path.exists(db_PATH):
    _db_inicial = os.path.join(_bundle_dir(), "escala.db")
    if os.path.exists(_db_inicial) and _db_inicial != db_PATH:
        shutil.copyfile(_db_inicial, db_PATH)


def get_connection():
    """Abre e retorna a conexão com o banco SQLite com chave estrangeira ativada e linhas no formato Row."""
    conn = sqlite3.connect(db_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _schema_compatível(conn):
    """Retorna se o banco existente usa exclusivamente o schema definitivo."""
    tabelas = {
        row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    obrigatorias = {
        "colaboradores", "frota", "rotas", "escalas", "afastamentos",
        "historico_alteracoes", "lotes_importacao"
    }
    if not obrigatorias.issubset(tabelas) or any("_old" in tabela for tabela in tabelas):
        return False

    sql_colaboradores = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'colaboradores'"
    ).fetchone()["sql"]
    return "'reserva'" in sql_colaboradores and "INTEGER NOT NULL" not in sql_colaboradores


def _remover_banco():
    """Remove o banco e arquivos WAL para permitir uma criação limpa."""
    for caminho in (db_PATH, f"{db_PATH}-wal", f"{db_PATH}-shm"):
        if os.path.exists(caminho):
            os.remove(caminho)


def _ensure_db():
    """Cria o schema final; banco legado de teste é recriado integralmente."""
    conn = get_connection()
    precisa_recriar = not _schema_compatível(conn)
    conn.close()

    if precisa_recriar:
        _remover_banco()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            funcao TEXT NOT NULL CHECK (funcao IN ('motorista', 'ajudante')),
            status TEXT NOT NULL DEFAULT 'disponivel'
                CHECK (status IN ('disponivel', 'em_rota', 'afastado', 'reserva')),
            data_cadastro TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS frota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_frota TEXT NOT NULL UNIQUE,
            placa TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS rotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_rota TEXT NOT NULL UNIQUE,
            duracao_media_dias INTEGER
        );
        CREATE TABLE IF NOT EXISTS escalas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motorista_id INTEGER NOT NULL,
            ajudante_id INTEGER,
            frota_id INTEGER NOT NULL,
            rota_id INTEGER NOT NULL,
            data_saida TEXT NOT NULL,
            data_chegada TEXT,
            status TEXT NOT NULL DEFAULT 'em_rota'
                CHECK (status IN ('em_rota', 'chegou', 'substituido')),
            FOREIGN KEY (motorista_id) REFERENCES colaboradores(id) ON DELETE RESTRICT,
            FOREIGN KEY (ajudante_id) REFERENCES colaboradores(id) ON DELETE RESTRICT,
            FOREIGN KEY (frota_id) REFERENCES frota(id) ON DELETE RESTRICT,
            FOREIGN KEY (rota_id) REFERENCES rotas(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS afastamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            data_inicio TEXT NOT NULL,
            data_fim_prevista TEXT,
            data_retorno TEXT,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS historico_alteracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_alteracao TEXT NOT NULL,
            escala_id INTEGER,
            descricao TEXT NOT NULL,
            data_alteracao TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (escala_id) REFERENCES escalas(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS lotes_importacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_nome TEXT,
            data_importacao TEXT NOT NULL DEFAULT (datetime('now')),
            observacao TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_escalas_status ON escalas(status);
        CREATE INDEX IF NOT EXISTS idx_escalas_motorista ON escalas(motorista_id);
        CREATE INDEX IF NOT EXISTS idx_escalas_frota ON escalas(frota_id);
        CREATE INDEX IF NOT EXISTS idx_afastamentos_colaborador ON afastamentos(colaborador_id);
        CREATE INDEX IF NOT EXISTS idx_historico_escala ON historico_alteracoes(escala_id);
    """)
    conn.commit()
    conn.close()


def _migrar_status_reserva():
    """Compatibilidade histórica: o schema atual não usa migrações em runtime."""
    _ensure_db()


# ============================================================
# FUNÇÕES INTERNAS (aceitam cursor para compartilhar conexão)
# ============================================================

def _adicionar_colaborador(nome, funcao, status="disponivel", cursor=None):
    """Cadastra um novo colaborador. Se cursor for fornecido, usa a conexão existente."""
    close_conn = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_conn = True

    try:
        cursor.execute("""
            INSERT INTO colaboradores (nome, funcao, status)
            VALUES (?, ?, ?)
        """, (nome, funcao, status))
        novo_id = cursor.lastrowid
        if close_conn:
            conn.commit()
        return novo_id
    except Exception as e:
        if close_conn:
            conn.rollback()
        raise e
    finally:
        if close_conn:
            conn.close()


def _adicionar_frota(numero_frota, placa, cursor=None):
    """Cadastra um novo veículo. Se cursor for fornecido, usa a conexão existente."""
    close_conn = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_conn = True

    try:
        cursor.execute("""
            INSERT INTO frota (numero_frota, placa)
            VALUES (?, ?)
        """, (numero_frota, placa.upper()))
        novo_id = cursor.lastrowid
        if close_conn:
            conn.commit()
        return novo_id
    except Exception as e:
        if close_conn:
            conn.rollback()
        raise e
    finally:
        if close_conn:
            conn.close()


def _adicionar_rota(nome_rota, duracao_media_dias=None, cursor=None):
    """Cadastra uma nova rota. Se cursor for fornecido, usa a conexão existente."""
    close_conn = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_conn = True

    try:
        cursor.execute("""
            INSERT INTO rotas (nome_rota, duracao_media_dias)
            VALUES (?, ?)
        """, (nome_rota, duracao_media_dias))
        novo_id = cursor.lastrowid
        if close_conn:
            conn.commit()
        return novo_id
    except Exception as e:
        if close_conn:
            conn.rollback()
        raise e
    finally:
        if close_conn:
            conn.close()


def _obter_ou_criar_colaborador(nome, funcao, cursor):
    """Busca colaborador por nome e função. Se não encontrar, cadastra. Usa cursor compartilhado."""
    if not nome:
        return None

    nome_limpo = str(nome).strip()

    cursor.execute("""
        SELECT id FROM colaboradores
        WHERE LOWER(nome) = LOWER(?) AND funcao = ?
    """, (nome_limpo, funcao))

    colab = cursor.fetchone()

    if colab:
        return colab["id"]

    return _adicionar_colaborador(nome=nome_limpo, funcao=funcao, status="disponivel", cursor=cursor)


def _obter_ou_criar_frota(identificador, cursor):
    """Busca frota por número ou placa. Se não encontrar, insere. Usa cursor compartilhado."""
    if not identificador:
        return None

    numero_frota, placa = _parse_veiculo(identificador)

    cursor.execute("""
        SELECT id FROM frota
        WHERE UPPER(numero_frota) = ? OR UPPER(placa) = ?
    """, (numero_frota.upper(), placa.upper()))

    veiculo = cursor.fetchone()

    if veiculo:
        return veiculo["id"]

    return _adicionar_frota(numero_frota=numero_frota, placa=placa, cursor=cursor)


def _obter_ou_criar_rota(nome_rota, duracao_media_dias=None, cursor=None):
    """Busca rota por nome. Se não existir, cadastra. Usa cursor compartilhado."""
    if not nome_rota:
        return None

    nome_limpo = str(nome_rota).strip()

    cursor.execute("""
        SELECT id FROM rotas
        WHERE LOWER(nome_rota) = LOWER(?)
    """, (nome_limpo,))

    rota = cursor.fetchone()

    if rota:
        return rota["id"]

    return _adicionar_rota(nome_rota=nome_limpo, duracao_media_dias=duracao_media_dias, cursor=cursor)


def _registrar_afastamento(colaborador_id, motivo, data_inicio, data_fim_prevista, cursor):
    """Registra afastamento usando cursor compartilhado."""
    cursor.execute("""
        INSERT INTO afastamentos (colaborador_id, motivo, data_inicio, data_fim_prevista)
        VALUES (?, ?, ?, ?)
    """, (colaborador_id, motivo, data_inicio, data_fim_prevista))

    cursor.execute("UPDATE colaboradores SET status = 'afastado' WHERE id = ?", (colaborador_id,))

    return cursor.lastrowid


def _registrar_historico(tipo_alteracao, descricao, escala_id, cursor):
    """Grava registro de auditoria usando cursor compartilhado."""
    cursor.execute("""
        INSERT INTO historico_alteracoes (tipo_alteracao, escala_id, descricao)
        VALUES (?, ?, ?)
    """, (tipo_alteracao, escala_id, descricao))


def _criar_escala(motorista_id, frota_id, rota_id, data_saida, ajudante_id, cursor):
    """Cria escala usando cursor compartilhado. Retorna o id da nova escala."""

    # Validação de foreign keys
    cursor.execute("SELECT id FROM colaboradores WHERE id = ?", (motorista_id,))
    if not cursor.fetchone():
        raise ValueError(f"FOREIGN KEY inválida: motorista_id={motorista_id} não existe")

    cursor.execute("SELECT id FROM frota WHERE id = ?", (frota_id,))
    if not cursor.fetchone():
        raise ValueError(f"FOREIGN KEY inválida: frota_id={frota_id} não existe")

    cursor.execute("SELECT id FROM rotas WHERE id = ?", (rota_id,))
    if not cursor.fetchone():
        raise ValueError(f"FOREIGN KEY inválida: rota_id={rota_id} não existe")

    if ajudante_id is not None:
        cursor.execute("SELECT id FROM colaboradores WHERE id = ?", (ajudante_id,))
        if not cursor.fetchone():
            raise ValueError(f"FOREIGN KEY inválida: ajudante_id={ajudante_id} não existe")

    cursor.execute("""
        INSERT INTO escalas (motorista_id, ajudante_id, frota_id, rota_id, data_saida, status)
        VALUES (?, ?, ?, ?, ?, 'em_rota')
    """, (motorista_id, ajudante_id, frota_id, rota_id, data_saida))

    novo_id = cursor.lastrowid

    cursor.execute("UPDATE colaboradores SET status = 'em_rota' WHERE id = ?", (motorista_id,))

    if ajudante_id:
        cursor.execute("UPDATE colaboradores SET status = 'em_rota' WHERE id = ?", (ajudante_id,))

    _registrar_historico(
        tipo_alteracao="criacao_escala",
        descricao=f"Nova escala #{novo_id} iniciada para rota {rota_id}.",
        escala_id=novo_id,
        cursor=cursor
    )

    return novo_id


# ============================================================
# FUNÇÕES PÚBLICAS (mantêm compatibilidade com o app.py)
# ============================================================

def adicionar_colaborador(nome, funcao, status="disponivel"):
    """Cadastra um novo colaborador no sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO colaboradores (nome, funcao, status)
            VALUES (?, ?, ?)
        """, (nome, funcao, status))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def atualizar_colaborador(colaborador_id, nome, funcao, status=None):
    """Atualiza um colaborador existente e retorna se ele foi encontrado."""
    conn = get_connection()
    try:
        campos = ["nome = ?", "funcao = ?"]
        valores = [nome, funcao]
        if status is not None:
            campos.append("status = ?")
            valores.append(status)
        valores.append(colaborador_id)
        cursor = conn.execute(
            f"UPDATE colaboradores SET {', '.join(campos)} WHERE id = ?", valores
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def excluir_colaborador(colaborador_id):
    """Exclui colaborador; SQLite rejeita a operação se houver referências."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM colaboradores WHERE id = ?", (colaborador_id,))
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def listar_colaboradores():
    """Retorna todos os colaboradores cadastrados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM colaboradores ORDER BY nome ASC")
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def adicionar_frota(numero_frota, placa):
    """Cadastra um novo veículo na frota."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO frota (numero_frota, placa)
            VALUES (?, ?)
        """, (numero_frota, placa.upper()))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def atualizar_frota(frota_id, numero_frota, placa):
    """Atualiza um veículo existente."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE frota SET numero_frota = ?, placa = ? WHERE id = ?",
            (numero_frota, placa.upper(), frota_id),
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def excluir_frota(frota_id):
    """Exclui veículo; escalas referenciadas impedem a exclusão."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM frota WHERE id = ?", (frota_id,))
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def listar_frota():
    """Retorna todos os veículos cadastrados na frota."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM frota ORDER BY numero_frota ASC")
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def adicionar_rota(nome_rota, duracao_media_dias=None):
    """Cadastra uma nova rota com a duração média estimada em dias."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO rotas (nome_rota, duracao_media_dias)
            VALUES (?, ?)
        """, (nome_rota, duracao_media_dias))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def atualizar_rota(rota_id, nome_rota, duracao_media_dias=None):
    """Atualiza uma rota existente."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE rotas SET nome_rota = ?, duracao_media_dias = ? WHERE id = ?",
            (nome_rota, duracao_media_dias, rota_id),
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def excluir_rota(rota_id):
    """Exclui rota; escalas referenciadas impedem a exclusão."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM rotas WHERE id = ?", (rota_id,))
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def listar_rotas():
    """Retorna todas as rotas operacionais cadastradas."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rotas ORDER BY nome_rota ASC")
    resultados = cursor.fetchall()
    conn.close()
    return resultados


# --- GESTÃO DE ESCALAS ---

def criar_escala(motorista_id, frota_id, rota_id, data_saida, ajudante_id=None):
    """Cria uma nova escala de viagem e atualiza o status dos colaboradores."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validação de foreign keys
        cursor.execute("SELECT id FROM colaboradores WHERE id = ?", (motorista_id,))
        if not cursor.fetchone():
            raise ValueError(f"FOREIGN KEY inválida: motorista_id={motorista_id} não existe")

        cursor.execute("SELECT id FROM frota WHERE id = ?", (frota_id,))
        if not cursor.fetchone():
            raise ValueError(f"FOREIGN KEY inválida: frota_id={frota_id} não existe")

        cursor.execute("SELECT id FROM rotas WHERE id = ?", (rota_id,))
        if not cursor.fetchone():
            raise ValueError(f"FOREIGN KEY inválida: rota_id={rota_id} não existe")

        if ajudante_id is not None:
            cursor.execute("SELECT id FROM colaboradores WHERE id = ?", (ajudante_id,))
            if not cursor.fetchone():
                raise ValueError(f"FOREIGN KEY inválida: ajudante_id={ajudante_id} não existe")

        cursor.execute("""
            INSERT INTO escalas (motorista_id, ajudante_id, frota_id, rota_id, data_saida, status)
            VALUES (?, ?, ?, ?, ?, 'em_rota')
        """, (motorista_id, ajudante_id, frota_id, rota_id, data_saida))

        novo_id = cursor.lastrowid

        cursor.execute("UPDATE colaboradores SET status = 'em_rota' WHERE id = ?", (motorista_id,))

        if ajudante_id:
            cursor.execute("UPDATE colaboradores SET status = 'em_rota' WHERE id = ?", (ajudante_id,))

        conn.commit()

        registrar_historico(
            tipo_alteracao="criacao_escala",
            descricao=f"Nova escala #{novo_id} iniciada para rota {rota_id}.",
            escala_id=novo_id
        )

        return novo_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def listar_escalas():
    """Retorna as escalas cadastradas trazendo nomes via JOIN."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            escalas.id,
            escalas.motorista_id,
            escalas.ajudante_id,
            escalas.frota_id,
            escalas.rota_id,
            colaboradores_motorista.nome AS motorista,
            colaboradores_ajudante.nome AS ajudante,
            frota.numero_frota,
            frota.placa,
            rotas.nome_rota,
            rotas.duracao_media_dias,
            escalas.data_saida,
            escalas.data_chegada,
            escalas.status
        FROM escalas
        JOIN colaboradores AS colaboradores_motorista ON escalas.motorista_id = colaboradores_motorista.id
        LEFT JOIN colaboradores AS colaboradores_ajudante ON escalas.ajudante_id = colaboradores_ajudante.id
        JOIN frota ON escalas.frota_id = frota.id
        JOIN rotas ON escalas.rota_id = rotas.id
        ORDER BY escalas.id DESC
    """)

    resultados = cursor.fetchall()
    conn.close()
    return resultados


def registrar_chegada(escala_id, data_chegada):
    """Registra a conclusão de uma viagem e libera os colaboradores."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT motorista_id, ajudante_id FROM escalas WHERE id = ?", (escala_id,))
        escala = cursor.fetchone()

        if not escala:
            raise ValueError("Escala não encontrada.")

        cursor.execute("""
            UPDATE escalas
            SET data_chegada = ?, status = 'chegou'
            WHERE id = ?
        """, (data_chegada, escala_id))

        cursor.execute("""
            UPDATE colaboradores SET status = 'disponivel'
            WHERE id = ? AND status != 'afastado'
        """, (escala["motorista_id"],))

        if escala["ajudante_id"]:
            cursor.execute("""
                UPDATE colaboradores SET status = 'disponivel'
                WHERE id = ? AND status != 'afastado'
            """, (escala["ajudante_id"],))

        conn.commit()

        registrar_historico(
            tipo_alteracao="chegada_escala",
            descricao=f"Chegada registrada para a escala #{escala_id} em {data_chegada}.",
            escala_id=escala_id
        )
    finally:
        conn.close()


# --- SUBSTITUIÇÕES EM ESCALA ---

def trocar_motorista(escala_id, novo_motorista_id, data_troca):
    """Encerra a escala atual e abre nova escala com o novo motorista."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM escalas WHERE id = ?", (escala_id,))
        escala_atual = cursor.fetchone()

        if escala_atual is None:
            raise ValueError("Escala não encontrada")

        cursor.execute("""
            UPDATE escalas SET status = 'substituido', data_chegada = ? WHERE id = ?
        """, (data_troca, escala_id))

        cursor.execute(
            "UPDATE colaboradores SET status = 'disponivel' WHERE id = ? AND status != 'afastado'",
            (escala_atual["motorista_id"],)
        )

        cursor.execute("UPDATE colaboradores SET status = 'em_rota' WHERE id = ?", (novo_motorista_id,))

        cursor.execute("""
            INSERT INTO escalas (motorista_id, ajudante_id, frota_id, rota_id, data_saida, status)
            VALUES (?, ?, ?, ?, ?, 'em_rota')
        """, (novo_motorista_id, escala_atual["ajudante_id"], escala_atual["frota_id"],
              escala_atual["rota_id"], data_troca))

        nova_escala_id = cursor.lastrowid
        conn.commit()

        registrar_historico(
            tipo_alteracao="troca_motorista",
            descricao=f"Motorista alterado na escala #{escala_id} para motorista #{novo_motorista_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )

        return nova_escala_id
    finally:
        conn.close()


def trocar_ajudante(escala_id, novo_ajudante_id, data_troca):
    """Encerra a escala atual e abre nova escala com o novo ajudante."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM escalas WHERE id = ?", (escala_id,))
        escala_atual = cursor.fetchone()

        if escala_atual is None:
            raise ValueError("Escala não encontrada")

        cursor.execute("""
            UPDATE escalas SET status = 'substituido', data_chegada = ? WHERE id = ?
        """, (data_troca, escala_id))

        if escala_atual["ajudante_id"]:
            cursor.execute(
                "UPDATE colaboradores SET status = 'disponivel' WHERE id = ? AND status != 'afastado'",
                (escala_atual["ajudante_id"],)
            )

        if novo_ajudante_id:
            cursor.execute("UPDATE colaboradores SET status = 'em_rota' WHERE id = ?", (novo_ajudante_id,))

        cursor.execute("""
            INSERT INTO escalas (motorista_id, ajudante_id, frota_id, rota_id, data_saida, status)
            VALUES (?, ?, ?, ?, ?, 'em_rota')
        """, (escala_atual["motorista_id"], novo_ajudante_id, escala_atual["frota_id"],
              escala_atual["rota_id"], data_troca))

        nova_escala_id = cursor.lastrowid
        conn.commit()

        registrar_historico(
            tipo_alteracao="troca_ajudante",
            descricao=f"Ajudante alterado na escala #{escala_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )

        return nova_escala_id
    finally:
        conn.close()


def trocar_frota(escala_id, nova_frota_id, data_troca):
    """Encerra a escala atual e abre nova escala com o novo veículo."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM escalas WHERE id = ?", (escala_id,))
        escala_atual = cursor.fetchone()

        if escala_atual is None:
            raise ValueError("Escala não encontrada")

        cursor.execute("""
            UPDATE escalas SET status = 'substituido', data_chegada = ? WHERE id = ?
        """, (data_troca, escala_id))

        cursor.execute("""
            INSERT INTO escalas (motorista_id, ajudante_id, frota_id, rota_id, data_saida, status)
            VALUES (?, ?, ?, ?, ?, 'em_rota')
        """, (escala_atual["motorista_id"], escala_atual["ajudante_id"],
              nova_frota_id, escala_atual["rota_id"], data_troca))

        nova_escala_id = cursor.lastrowid
        conn.commit()

        registrar_historico(
            tipo_alteracao="troca_frota",
            descricao=f"Frota alterada na escala #{escala_id} para frota #{nova_frota_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )

        return nova_escala_id
    finally:
        conn.close()


def trocar_rota(escala_id, nova_rota_id, data_troca):
    """Encerra a escala atual e abre nova escala com a nova rota."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM escalas WHERE id = ?", (escala_id,))
        escala_atual = cursor.fetchone()

        if escala_atual is None:
            raise ValueError("Escala não encontrada")

        cursor.execute("""
            UPDATE escalas SET status = 'substituido', data_chegada = ? WHERE id = ?
        """, (data_troca, escala_id))

        cursor.execute("""
            INSERT INTO escalas (motorista_id, ajudante_id, frota_id, rota_id, data_saida, status)
            VALUES (?, ?, ?, ?, ?, 'em_rota')
        """, (escala_atual["motorista_id"], escala_atual["ajudante_id"],
              escala_atual["frota_id"], nova_rota_id, data_troca))

        nova_escala_id = cursor.lastrowid
        conn.commit()

        registrar_historico(
            tipo_alteracao="troca_rota",
            descricao=f"Rota alterada na escala #{escala_id} para rota #{nova_rota_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )

        return nova_escala_id
    finally:
        conn.close()


# --- GESTÃO DE AFASTAMENTOS E RETORNOS ---

def registrar_afastamento(colaborador_id, motivo, data_inicio, data_fim_prevista=None):
    """Registra um afastamento de colaborador e define seu status como 'afastado'."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO afastamentos (colaborador_id, motivo, data_inicio, data_fim_prevista)
            VALUES (?, ?, ?, ?)
        """, (colaborador_id, motivo, data_inicio, data_fim_prevista))

        cursor.execute("UPDATE colaboradores SET status = 'afastado' WHERE id = ?", (colaborador_id,))

        novo_id = cursor.lastrowid
        conn.commit()

        registrar_historico(
            tipo_alteracao="afastamento",
            descricao=f"Colaborador #{colaborador_id} afastado. Motivo: {motivo}"
        )

        return novo_id
    finally:
        conn.close()


def registrar_retorno(afastamento_id, colaborador_id, data_retorno):
    """Registra a data de retorno de um afastamento e libera o colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE afastamentos SET data_retorno = ? WHERE id = ?
        """, (data_retorno, afastamento_id))

        cursor.execute("""
            UPDATE colaboradores SET status = 'disponivel' WHERE id = ?
        """, (colaborador_id,))

        conn.commit()

        registrar_historico(
            tipo_alteracao="retorno_afastamento",
            descricao=f"Colaborador #{colaborador_id} retornou do afastamento #{afastamento_id} em {data_retorno}"
        )
    finally:
        conn.close()


def listar_afastamentos_ativos():
    """Retorna os afastamentos em aberto (sem data de retorno registrada)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            afastamentos.id,
            afastamentos.colaborador_id,
            colaboradores.nome,
            colaboradores.funcao,
            afastamentos.motivo,
            afastamentos.data_inicio,
            afastamentos.data_fim_prevista
        FROM afastamentos
        JOIN colaboradores ON afastamentos.colaborador_id = colaboradores.id
        WHERE afastamentos.data_retorno IS NULL
        ORDER BY afastamentos.id DESC
    """)
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def listar_disponiveis(funcao):
    """Lista apenas os colaboradores disponíveis para uma determinada função."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM colaboradores
        WHERE status = 'disponivel' AND funcao = ?
        ORDER BY nome ASC
    """, (funcao,))

    resultados = cursor.fetchall()
    conn.close()
    return resultados


# --- AUDITORIA E HISTÓRICO ---

def registrar_historico(tipo_alteracao, descricao, escala_id=None):
    """Grava um registro de auditoria na tabela historico_alteracoes."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO historico_alteracoes (tipo_alteracao, escala_id, descricao)
            VALUES (?, ?, ?)
        """, (tipo_alteracao, escala_id, descricao))
        conn.commit()
    finally:
        conn.close()


def listar_historico():
    """Retorna o histórico de alterações ordenado da mais recente para a mais antiga."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM historico_alteracoes ORDER BY id DESC")
    resultados = cursor.fetchall()

    conn.close()
    return resultados


def obter_historico_colaborador(colaborador_id):
    """Retorna a ficha completa do colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colaboradores WHERE id = ?", (colaborador_id,))
    colab = cursor.fetchone()

    if not colab:
        conn.close()
        raise ValueError("Colaborador não encontrado")

    cursor.execute("""
        SELECT
            escalas.id,
            escalas.data_saida,
            escalas.data_chegada,
            escalas.status,
            rotas.nome_rota,
            frota.numero_frota,
            frota.placa,
            CASE
                WHEN escalas.motorista_id = ? THEN 'Motorista'
                ELSE 'Ajudante'
            END AS papel_exercido
        FROM escalas
        JOIN rotas ON escalas.rota_id = rotas.id
        JOIN frota ON escalas.frota_id = frota.id
        WHERE escalas.motorista_id = ? OR escalas.ajudante_id = ?
        ORDER BY escalas.id DESC
    """, (colaborador_id, colaborador_id, colaborador_id))

    escalas = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT * FROM afastamentos
        WHERE colaborador_id = ?
        ORDER BY id DESC
    """, (colaborador_id,))

    afastamentos = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "colaborador": dict(colab),
        "total_viagens": len(escalas),
        "total_afastamentos": len(afastamentos),
        "escalas": escalas,
        "afastamentos": afastamentos
    }


# --- IMPORTAÇÃO EM MASSA VIA EXCEL ---

def obter_ou_criar_colaborador(nome, funcao):
    """Busca colaborador por nome e função. Se não encontrar, cadastra automaticamente."""
    if not nome:
        return None

    nome_limpo = str(nome).strip()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id FROM colaboradores
            WHERE LOWER(nome) = LOWER(?) AND funcao = ?
        """, (nome_limpo, funcao))

        colab = cursor.fetchone()

        if colab:
            return colab["id"]

        return adicionar_colaborador(nome=nome_limpo, funcao=funcao, status="disponivel")
    finally:
        conn.close()


def _parse_veiculo(identificador):
    """Separa uma string como 'F03 - MSN7805' em (numero_frota, placa)."""
    val = str(identificador).strip()
    if not val:
        return None, None
    if "-" in val:
        partes = val.split("-", 1)
        numero, placa = partes[0].strip(), partes[1].strip()
        if numero and placa:
            return numero, placa
    return val, val


def obter_ou_criar_frota(identificador):
    """Busca frota por número ou placa. Se não encontrar, insere automaticamente."""
    if not identificador:
        return None

    numero_frota, placa = _parse_veiculo(identificador)
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id FROM frota
            WHERE UPPER(numero_frota) = ? OR UPPER(placa) = ?
        """, (numero_frota.upper(), placa.upper()))

        veiculo = cursor.fetchone()

        if veiculo:
            return veiculo["id"]

        return adicionar_frota(numero_frota=numero_frota, placa=placa)
    finally:
        conn.close()


def obter_ou_criar_rota(nome_rota, duracao_media_dias=None):
    """Busca rota por nome. Se não existir, cadastra automaticamente."""
    if not nome_rota:
        return None

    nome_limpo = str(nome_rota).strip()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id FROM rotas
            WHERE LOWER(nome_rota) = LOWER(?)
        """, (nome_limpo,))

        rota = cursor.fetchone()

        if rota:
            return rota["id"]

        return adicionar_rota(nome_rota=nome_limpo, duracao_media_dias=duracao_media_dias)
    finally:
        conn.close()


def listar_colaboradores_reserva():
    """Retorna todos os colaboradores com status 'reserva'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM colaboradores
        WHERE status = 'reserva'
        ORDER BY nome ASC
    """)
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def remover_reserva(colaborador_id):
    """Remove um colaborador da reserva, definindo status como 'disponivel'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE colaboradores SET status = 'disponivel'
        WHERE id = ? AND status = 'reserva'
    """, (colaborador_id,))
    afetados = cursor.rowcount
    conn.commit()
    conn.close()
    if afetados == 0:
        raise ValueError("Colaborador não encontrado ou não está em reserva")
    return afetados


def listar_frotas_com_status():
    """Retorna todas as frotas com informação se estão em uso ou livres."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            f.id,
            f.numero_frota,
            f.placa,
            CASE
                WHEN e.id IS NOT NULL THEN 'em_uso'
                ELSE 'livre'
            END AS status_frota,
            e.id AS escala_ativa_id,
            motorista.nome AS motorista_atual,
            rotas.nome_rota AS rota_atual,
            e.data_saida
        FROM frota f
        LEFT JOIN escalas e ON e.frota_id = f.id AND e.status = 'em_rota'
        LEFT JOIN colaboradores AS motorista ON e.motorista_id = motorista.id
        LEFT JOIN rotas ON e.rota_id = rotas.id
        ORDER BY f.numero_frota ASC
    """)
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def obter_historico_frota(frota_id, data_inicio=None, data_fim=None, limite=3):
    """Retorna o histórico de motoristas e rotas de uma frota."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM frota WHERE id = ?", (frota_id,))
    frota = cursor.fetchone()
    if not frota:
        conn.close()
        return None

    params = [frota_id]
    filtro_data = ""

    if data_inicio and data_fim:
        filtro_data = "AND escalas.data_saida BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    elif data_inicio:
        filtro_data = "AND escalas.data_saida >= ?"
        params.append(data_inicio)
    elif data_fim:
        filtro_data = "AND escalas.data_saida <= ?"
        params.append(data_fim)

    limit_clause = "" if (data_inicio or data_fim) else f"LIMIT {limite}"

    cursor.execute(f"""
        SELECT
            escalas.id,
            escalas.data_saida,
            escalas.data_chegada,
            escalas.status,
            motorista.nome AS motorista_nome,
            motorista.id AS motorista_id,
            ajudante.nome AS ajudante_nome,
            ajudante.id AS ajudante_id,
            rotas.nome_rota,
            rotas.id AS rota_id
        FROM escalas
        JOIN colaboradores AS motorista ON escalas.motorista_id = motorista.id
        LEFT JOIN colaboradores AS ajudante ON escalas.ajudante_id = ajudante.id
        JOIN rotas ON escalas.rota_id = rotas.id
        WHERE escalas.frota_id = ?
        {filtro_data}
        ORDER BY escalas.data_saida DESC
        {limit_clause}
    """, params)

    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "frota": dict(frota),
        "historico": historico,
        "total": len(historico)
    }


def processar_linha_importacao(dados, data_padrao=None, motivo_afastamento_padrao="Retirado da escala via importação de planilha"):
    """
    Processa uma linha importada da planilha Excel.
    USA UMA ÚNICA CONEXÃO para toda a operação, evitando 'database is locked'.
    """
    motorista_nome = dados.get("motorista")
    frota_identificador = dados.get("frota") or dados.get("veiculo") or dados.get("placa")
    rota_nome = dados.get("rota")
    ajudante_nome = dados.get("ajudante")
    data_saida = dados.get("data_saida") or data_padrao or datetime.now().strftime("%Y-%m-%d")

    if not motorista_nome or not frota_identificador or not rota_nome:
        print(f"[DB] ERRO: Linha sem dados obrigatórios - motorista='{motorista_nome}', frota='{frota_identificador}', rota='{rota_nome}'")
        return {"status": "erro", "motivo": "Linha sem motorista, frota ou rota preenchidos"}

    # ===== UMA ÚNICA CONEXÃO PARA TUDO =====
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Resolução / Criação automática de Motorista, Frota e Rota
        motorista_id = _obter_ou_criar_colaborador(motorista_nome, "motorista", cursor)
        frota_id = _obter_ou_criar_frota(frota_identificador, cursor)
        rota_id = _obter_ou_criar_rota(rota_nome, cursor=cursor)

        # ===== DEBUG =====
        print(f"[DB] motorista='{motorista_nome}' -> id={motorista_id}, "
              f"ajudante='{ajudante_nome}', "
              f"frota='{frota_identificador}' -> id={frota_id}, "
              f"rota='{rota_nome}' -> id={rota_id}, "
              f"data_saida='{data_saida}'")

        # Validação
        erros = []
        if not motorista_id:
            erros.append(f"Motorista '{motorista_nome}' não pôde ser encontrado/criado")
        if not frota_id:
            erros.append(f"Frota '{frota_identificador}' não pôde ser encontrada/criada")
        if not rota_id:
            erros.append(f"Rota '{rota_nome}' não pôde ser encontrada/criada")
        if erros:
            conn.rollback()
            print(f"[DB] ERRO VALIDAÇÃO: {' | '.join(erros)}")
            return {"status": "erro", "motivo": " | ".join(erros)}

        # Tratamento do Ajudante (Opcional)
        ajudante_id = None
        if ajudante_nome is not None:
            ajudante_str = str(ajudante_nome).strip()
            if ajudante_str and ajudante_str.upper() not in ("VAZIO", "NAN", "-", "--"):
                ajudante_id = _obter_ou_criar_colaborador(ajudante_str, "ajudante", cursor)
                if not ajudante_id:
                    conn.rollback()
                    print(f"[DB] ERRO: Ajudante '{ajudante_str}' não pôde ser encontrado/criado")
                    return {"status": "erro", "motivo": f"Ajudante '{ajudante_str}' não pôde ser encontrado/criado"}

        # Verifica escala ativa
        cursor.execute("""
            SELECT * FROM escalas
            WHERE status = 'em_rota' AND (frota_id = ? OR motorista_id = ?)
        """, (frota_id, motorista_id))
        escala_ativa = cursor.fetchone()

        afastamento_gerado = None

        if escala_ativa:
            print(f"[DB] ESCALA ATIVA ENCONTRADA: id={escala_ativa['id']}, motorista_id={escala_ativa['motorista_id']}, frota_id={escala_ativa['frota_id']}")

            ajudante_anterior_id = escala_ativa["ajudante_id"]

            if ajudante_anterior_id is not None and ajudante_id is None:
                afastamento_id = _registrar_afastamento(
                    colaborador_id=ajudante_anterior_id,
                    motivo=motivo_afastamento_padrao,
                    data_inicio=data_saida,
                    data_fim_prevista=None,
                    cursor=cursor
                )
                afastamento_gerado = {
                    "colaborador_id": ajudante_anterior_id,
                    "afastamento_id": afastamento_id
                }

            cursor.execute("""
                UPDATE escalas
                SET status = 'substituido', data_chegada = ?
                WHERE id = ?
            """, (data_saida, escala_ativa["id"]))

            if escala_ativa["motorista_id"] != motorista_id:
                cursor.execute(
                    "UPDATE colaboradores SET status = 'disponivel' WHERE id = ? AND status != 'afastado'",
                    (escala_ativa["motorista_id"],)
                )

        # Cria a nova escala usando o mesmo cursor
        nova_escala_id = _criar_escala(
            motorista_id=motorista_id,
            frota_id=frota_id,
            rota_id=rota_id,
            data_saida=data_saida,
            ajudante_id=ajudante_id,
            cursor=cursor
        )

        # COMMIT ÚNICO no final de tudo
        conn.commit()

        print(f"[DB] SUCESSO: escala #{nova_escala_id} criada")

        return {
            "status": "sucesso",
            "escala_id": nova_escala_id,
            "motorista_id": motorista_id,
            "frota_id": frota_id,
            "rota_id": rota_id,
            "ajudante_id": ajudante_id,
            "afastamento_gerado": afastamento_gerado
        }

    except ValueError as e:
        conn.rollback()
        print(f"[DB] ERRO ValueError: {e}")
        return {"status": "erro", "motivo": str(e)}
    except Exception as e:
        conn.rollback()
        print(f"[DB] ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "erro", "motivo": f"Erro inesperado: {e}"}
    finally:
        conn.close()


# --- INDICADORES E DASHBOARD ---

def obter_indicadores():
    """Calcula estatísticas operacionais para exibição no dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM escalas WHERE status = 'em_rota'")
    escalas_em_rota = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'disponivel' AND funcao = 'motorista'")
    motoristas_disponiveis = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'disponivel' AND funcao = 'ajudante'")
    ajudantes_disponiveis = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'afastado'")
    colaboradores_afastados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM frota")
    total_frota = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rotas")
    total_rotas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            escalas.data_saida,
            escalas.data_chegada,
            rotas.duracao_media_dias
        FROM escalas
        JOIN rotas ON escalas.rota_id = rotas.id
        WHERE escalas.status = 'chegou' AND escalas.data_chegada IS NOT NULL AND rotas.duracao_media_dias IS NOT NULL
    """)
    viagens_concluidas = cursor.fetchall()

    no_prazo = 0
    total_concluidas = len(viagens_concluidas)

    for v in viagens_concluidas:
        try:
            saida = datetime.strptime(v["data_saida"][:10], "%Y-%m-%d")
            chegada = datetime.strptime(v["data_chegada"][:10], "%Y-%m-%d")
            duracao_real = (chegada - saida).days
            if duracao_real <= v["duracao_media_dias"]:
                no_prazo += 1
        except Exception:
            pass

    taxa_pontualidade = round((no_prazo / total_concluidas * 100), 1) if total_concluidas > 0 else 100.0

    cursor.execute("""
        SELECT colaboradores.nome, COUNT(escalas.id) as total_viagens
        FROM escalas
        JOIN colaboradores ON escalas.motorista_id = colaboradores.id
        GROUP BY colaboradores.id
        ORDER BY total_viagens DESC
        LIMIT 5
    """)
    top_motoristas = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT rotas.nome_rota, COUNT(escalas.id) as total_escalas
        FROM escalas
        JOIN rotas ON escalas.rota_id = rotas.id
        GROUP BY rotas.id
        ORDER BY total_escalas DESC
        LIMIT 5
    """)
    top_rotas = [dict(row) for row in cursor.fetchall()]

    # Frotas disponíveis (não em uso)
    cursor.execute("""
        SELECT COUNT(*) FROM frota f
        WHERE NOT EXISTS (
            SELECT 1 FROM escalas e WHERE e.frota_id = f.id AND e.status = 'em_rota'
        )
    """)
    frotas_disponiveis = cursor.fetchone()[0]

    # Colaboradores reserva
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'reserva'")
    total_reservas = cursor.fetchone()[0]

    # Transbordos ativos
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT motorista_id, frota_id
            FROM escalas
            WHERE status = 'em_rota'
            GROUP BY motorista_id, frota_id
            HAVING COUNT(*) > 1
        )
    """)
    total_transbordos = cursor.fetchone()[0]

    conn.close()

    return {
        "escalas_em_rota": escalas_em_rota,
        "motoristas_disponiveis": motoristas_disponiveis,
        "ajudantes_disponiveis": ajudantes_disponiveis,
        "colaboradores_afastados": colaboradores_afastados,
        "total_frota": total_frota,
        "total_rotas": total_rotas,
        "total_viagens_concluidas": total_concluidas,
        "taxa_pontualidade": taxa_pontualidade,
        "top_motoristas": top_motoristas,
        "top_rotas": top_rotas,
        "frotas_disponiveis": frotas_disponiveis,
        "total_reservas": total_reservas,
        "total_transbordos": total_transbordos,
    }


# --- LOTES DE IMPORTAÇÃO E RODAPÉ DA PLANILHA ---

def criar_lote_importacao(arquivo_nome):
    """Cria um registro de lote de importação e retorna seu id."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO lotes_importacao (arquivo_nome) VALUES (?)
        """, (arquivo_nome,))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def atualizar_observacao_lote(lote_id, texto):
    """Anexa um texto à observação do lote."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT observacao FROM lotes_importacao WHERE id = ?", (lote_id,))
        atual = cursor.fetchone()
        observacao_atual = atual["observacao"] if atual and atual["observacao"] else ""
        nova_observacao = (observacao_atual + "\n" + texto).strip() if observacao_atual else texto
        cursor.execute("UPDATE lotes_importacao SET observacao = ? WHERE id = ?", (nova_observacao, lote_id))
        conn.commit()
    finally:
        conn.close()


def listar_lotes_importacao():
    """Retorna os lotes de importação, mais recente primeiro."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lotes_importacao ORDER BY id DESC")
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def marcar_reserva(colaborador_id):
    """Marca um colaborador como 'reserva'."""
    if not colaborador_id:
        return
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE colaboradores SET status = 'reserva'
            WHERE id = ? AND status != 'afastado'
        """, (colaborador_id,))
        conn.commit()
    finally:
        conn.close()


def processar_linha_rodape(texto, lote_id=None):
    """Processa uma linha de rodapé da planilha."""
    if not texto or not str(texto).strip():
        return {"tipo": "vazio"}

    texto_limpo = str(texto).strip()
    upper = texto_limpo.upper()

    if upper.startswith("RESERVAS"):
        return {"tipo": "ignorado", "motivo": "linha RESERVAS não processada"}

    if upper.startswith("MOTORISTAS"):
        conteudo = texto_limpo.split(":", 1)[1] if ":" in texto_limpo else ""
        nomes = [n.strip() for n in conteudo.split(",") if n.strip()]
        ids = []
        for nome in nomes:
            colaborador_id = obter_ou_criar_colaborador(nome, "motorista")
            marcar_reserva(colaborador_id)
            ids.append(colaborador_id)
        return {"tipo": "reserva_motoristas", "colaboradores": ids}

    if upper.startswith("AJUDANTES"):
        conteudo = texto_limpo.split(":", 1)[1] if ":" in texto_limpo else ""
        nomes = [n.strip() for n in conteudo.split(",") if n.strip()]
        ids = []
        for nome in nomes:
            colaborador_id = obter_ou_criar_colaborador(nome, "ajudante")
            marcar_reserva(colaborador_id)
            ids.append(colaborador_id)
        return {"tipo": "reserva_ajudantes", "colaboradores": ids}

    if upper.startswith("OCORRENCIAS") or upper.startswith("OCORRÊNCIAS"):
        return {"tipo": "ignorado", "motivo": "linha OCORRENCIAS não processada"}

    if "INSTRUÇÃO TRANSBORDO" in upper or "INSTRUCAO TRANSBORDO" in upper:
        if lote_id:
            atualizar_observacao_lote(lote_id, texto_limpo)
        return {"tipo": "observacao_lote", "texto": texto_limpo}

    return {"tipo": "ignorado", "motivo": "linha de rodapé não reconhecida"}


if __name__ == "__main__":
    _ensure_db()
    _migrar_status_reserva()
    print("Banco de dados verificado e estrutura atualizada com sucesso.")