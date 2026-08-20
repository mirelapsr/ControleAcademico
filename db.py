"""
db.py — CAMADA DE BANCO
=======================
Banco: PostgreSQL (database CAcademic).
Driver: psycopg2, com RealDictCursor (as linhas voltam como dict).

Pré-requisito: o banco `CAcademic` já deve existir. A API, no
startup, cria as TABELAS (`criar_tabelas`) usando `CREATE TABLE IF NOT
EXISTS` — portanto é seguro reiniciar a API sem perder dados.
"""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "postgres"),       
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "CAcademic"),
    "port": int(os.getenv("DB_PORT", "5432")),      
}


def conectar():
    return psycopg2.connect(
        host=CONFIG["host"],
        user=CONFIG["user"],
        password=CONFIG["password"],
        dbname=CONFIG["database"], 
        port=CONFIG["port"],
        cursor_factory=RealDictCursor 
    )


@contextmanager
def cursor(commit: bool = False):
    """Context manager: abre conexão + cursor, faz commit/rollback e fecha
    tudo ao final. commit=True para INSERT/UPDATE/DELETE; False para SELECT.

    Uso:
        with cursor(commit=True) as cur:
            cur.execute("INSERT INTO aluno (...) VALUES (...)", (...))
            novo_id = cur.lastrowid
    """
    conn = conectar()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ===========================================================================
# CRIAÇÃO DE TABELAS (idempotente — usa CREATE TABLE IF NOT EXISTS)
# ===========================================================================

def criar_tabelas() -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS escola (
        id_escola        SERIAL PRIMARY KEY,
        nome_escola      VARCHAR(150) NOT NULL,
        codigo_inep      VARCHAR(8),
        cnpj             VARCHAR(14),
        endereco_escola  VARCHAR(200),
        telefone_escola  VARCHAR(13),
        email_escola     VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS periodo (
        id_periodo       SERIAL PRIMARY KEY,
        ano              SMALLINT NOT NULL,
        nome_periodo     VARCHAR(30) NOT NULL,
        data_inicio      DATE NOT NULL,
        data_fim         DATE NOT NULL,
        situacao         VARCHAR(50) CHECK (situacao IN ('Ativo','Encerrado')) NOT NULL DEFAULT 'Ativo'
    );

    CREATE TABLE IF NOT EXISTS materia (
        id_materia       SERIAL PRIMARY KEY,
        nome_materia     VARCHAR(80) NOT NULL,
        carga_horaria    INTEGER CHECK (carga_horaria > 0),
        CONSTRAINT uq_materia_nome UNIQUE (nome_materia)
    );

    CREATE TABLE IF NOT EXISTS responsavel (
        id_responsavel   SERIAL PRIMARY KEY,
        nome_resp        VARCHAR(100) NOT NULL,
        cpf_resp         VARCHAR(11),
        telefone_resp    VARCHAR(13),
        email_resp       VARCHAR(100),
        cep_resp         VARCHAR(8),
        endereco_resp    VARCHAR(200)
    );

    CREATE TABLE IF NOT EXISTS aluno (
        id_aluno           SERIAL PRIMARY KEY,
        numero_matricula   VARCHAR(20) NOT NULL,
        nome_aluno         VARCHAR(100) NOT NULL,
        data_nascimento    DATE NOT NULL,
        cpf_aluno          VARCHAR(11),
        telefone_aluno     VARCHAR(13),
        email_aluno        VARCHAR(100),
        cep_aluno          VARCHAR(8),
        endereco_aluno     VARCHAR(200),
        situacao           VARCHAR(50) CHECK (situacao IN ('Ativo','Inativo','Transferido')) NOT NULL DEFAULT 'Ativo'
    );

    CREATE TABLE IF NOT EXISTS turma (
        id_turma             SERIAL PRIMARY KEY,
        nome_turma           VARCHAR(30) NOT NULL,
        serie                VARCHAR(45),
        turno                VARCHAR(50) CHECK (turno IN ('Manha','Tarde','Noite','Integral')) NOT NULL,
        capacidade           INT,
        escola_id_escola     INT NOT NULL,
        ano_letivo           SMALLINT NOT NULL,
        CONSTRAINT fk_turma_escola FOREIGN KEY (escola_id_escola) REFERENCES escola(id_escola)
    );

    CREATE TABLE IF NOT EXISTS professor (
        id_professor     SERIAL PRIMARY KEY,
        nome_prof        VARCHAR(100) NOT NULL,
        cpf_prof         VARCHAR(11),
        telefone_prof    VARCHAR(13),
        email_prof       VARCHAR(100),
        cep_prof         VARCHAR(8),
        endereco_prof    VARCHAR(200),
        situacao         VARCHAR(50) CHECK (situacao IN ('Ativo','Inativo')) NOT NULL DEFAULT 'Ativo',
        escola_id_escola INT NOT NULL,
        CONSTRAINT fk_professor_escola FOREIGN KEY (escola_id_escola) REFERENCES escola(id_escola)
    );

    CREATE TABLE IF NOT EXISTS alunoresponsavel (
        aluno_id_aluno               INT NOT NULL,
        responsavel_id_responsavel   INT NOT NULL,
        tipo_responsavel             VARCHAR(50) CHECK (tipo_responsavel IN ('Pai','Mae','ResponsavelLegal','Outro')) NOT NULL,
        responsavel_financeiro       BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (aluno_id_aluno, responsavel_id_responsavel),
        CONSTRAINT fk_ar_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno),
        CONSTRAINT fk_ar_responsavel FOREIGN KEY (responsavel_id_responsavel) REFERENCES responsavel(id_responsavel)
    );

    CREATE TABLE IF NOT EXISTS matricula (
        id_matricula     SERIAL PRIMARY KEY,
        aluno_id_aluno   INT NOT NULL,
        turma_id_turma   INT NOT NULL,
        data_matricula   DATE NOT NULL,
        situacao         VARCHAR(50) CHECK (situacao IN ('Ativa','Cancelada','Transferida','Concluida')) NOT NULL DEFAULT 'Ativa',
        CONSTRAINT fk_matricula_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno),
        CONSTRAINT fk_matricula_turma FOREIGN KEY (turma_id_turma) REFERENCES turma(id_turma)
    );

    CREATE TABLE IF NOT EXISTS grade_curricular (
        id_grade                SERIAL PRIMARY KEY,
        turma_id_turma          INT NOT NULL,
        materia_id_materia      INT NOT NULL,
        professor_id_professor  INT NOT NULL,
        CONSTRAINT fk_grade_turma FOREIGN KEY (turma_id_turma) REFERENCES turma(id_turma),
        CONSTRAINT fk_grade_materia FOREIGN KEY (materia_id_materia) REFERENCES materia(id_materia),
        CONSTRAINT fk_grade_professor FOREIGN KEY (professor_id_professor) REFERENCES professor(id_professor),
        CONSTRAINT uq_turma_materia UNIQUE (turma_id_turma, materia_id_materia)
    );

    CREATE TABLE IF NOT EXISTS avaliacao (
        id_avaliacao        SERIAL PRIMARY KEY,
        grade_id_grade      INT NOT NULL,
        periodo_id_periodo  INT NOT NULL,
        tipo                VARCHAR(50) CHECK (tipo IN ('Prova','Trabalho','Projeto','Recuperacao')) NOT NULL,
        nome_avaliacao      VARCHAR(100) NOT NULL,
        data_avaliacao      DATE NOT NULL,
        peso                DECIMAL(4,2) NOT NULL DEFAULT 1.00,
        CONSTRAINT fk_avaliacao_grade FOREIGN KEY (grade_id_grade) REFERENCES grade_curricular(id_grade),
        CONSTRAINT fk_avaliacao_periodo FOREIGN KEY (periodo_id_periodo) REFERENCES periodo(id_periodo)
    );

    CREATE TABLE IF NOT EXISTS nota (
        id_nota                 SERIAL PRIMARY KEY,
        avaliacao_id_avaliacao  INT NOT NULL,
        aluno_id_aluno          INT NOT NULL,
        valor_nota              DECIMAL(4,2) NOT NULL,
        CONSTRAINT fk_nota_avaliacao FOREIGN KEY (avaliacao_id_avaliacao) REFERENCES avaliacao(id_avaliacao),
        CONSTRAINT fk_nota_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno),
        CONSTRAINT uq_nota_avaliacao_aluno UNIQUE (avaliacao_id_avaliacao, aluno_id_aluno)
    );

    CREATE TABLE IF NOT EXISTS frequencia (
        id_frequencia    SERIAL PRIMARY KEY,
        grade_id_grade   INT NOT NULL,
        aluno_id_aluno   INT NOT NULL,
        data_frequencia  DATE NOT NULL,
        situacao         VARCHAR(50) CHECK (situacao IN ('Presente','Falta','FaltaJustificada')) NOT NULL,
        CONSTRAINT fk_frequencia_grade FOREIGN KEY (grade_id_grade) REFERENCES grade_curricular(id_grade),
        CONSTRAINT fk_frequencia_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno),
        CONSTRAINT uq_freq_aluno_grade_data UNIQUE (grade_id_grade, aluno_id_aluno, data_frequencia)
    );

    CREATE TABLE IF NOT EXISTS boletim (
        id_boletim          SERIAL PRIMARY KEY,
        aluno_id_aluno      INT NOT NULL,
        periodo_id_periodo  INT NOT NULL,
        materia_id_materia  INT NOT NULL,
        media_final         DECIMAL(4,2) NOT NULL,
        situacao            VARCHAR(50) CHECK (situacao IN ('Aberto','Fechado')) NOT NULL DEFAULT 'Aberto',
        CONSTRAINT fk_boletim_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno),
        CONSTRAINT fk_boletim_periodo FOREIGN KEY (periodo_id_periodo) REFERENCES periodo(id_periodo),
        CONSTRAINT fk_boletim_materia FOREIGN KEY (materia_id_materia) REFERENCES materia(id_materia),
        CONSTRAINT uq_boletim_aluno_periodo_materia UNIQUE (aluno_id_aluno, periodo_id_periodo, materia_id_materia)
    );

    CREATE TABLE IF NOT EXISTS boleto (
        id_boleto          SERIAL PRIMARY KEY,
        numero_boleto      VARCHAR(50) NOT NULL,
        aluno_id_aluno     INT NOT NULL,
        competencia        CHAR(7) NOT NULL,
        valor_mensalidade  DECIMAL(10,2) NOT NULL,
        data_vencimento    DATE NOT NULL,
        data_pagamento     DATE,
        situacao           VARCHAR(50) CHECK (situacao IN ('Pendente','Pago','Atrasado','Cancelado')) NOT NULL DEFAULT 'Pendente',
        CONSTRAINT fk_boleto_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno)
    );
    """

    views = """
    CREATE OR REPLACE VIEW vw_aluno_escola_atual AS
    SELECT a.id_aluno, e.id_escola, e.nome_escola
    FROM aluno a
    JOIN matricula m ON m.aluno_id_aluno = a.id_aluno AND m.situacao = 'Ativa'
    JOIN turma t ON t.id_turma = m.turma_id_turma
    JOIN escola e ON e.id_escola = t.escola_id_escola;

    CREATE OR REPLACE VIEW vw_aluno_responsavel_financeiro AS
    SELECT ar.aluno_id_aluno, r.id_responsavel, r.nome_resp, r.email_resp, r.telefone_resp
    FROM alunoresponsavel ar
    JOIN responsavel r ON r.id_responsavel = ar.responsavel_id_responsavel
    WHERE ar.responsavel_financeiro = TRUE;

    CREATE OR REPLACE VIEW vw_aluno_media_dinamica AS
    SELECT
        n.aluno_id_aluno,
        a.periodo_id_periodo,
        g.materia_id_materia,
        ROUND(SUM(n.valor_nota * a.peso) / SUM(a.peso), 2) AS media_calculada,
        COUNT(n.id_nota) AS qtd_avaliacoes_contabilizadas
    FROM nota n
    JOIN avaliacao a ON a.id_avaliacao = n.avaliacao_id_avaliacao
    JOIN grade_curricular g ON g.id_grade = a.grade_id_grade
    GROUP BY n.aluno_id_aluno, a.periodo_id_periodo, g.materia_id_materia;
    """

    conn = conectar()
    try:
        with conn.cursor() as cur:
            for statement in ddl.split(";"):
                if statement.strip():
                    cur.execute(statement)
            for statement in views.split(";"):
                if statement.strip():
                    cur.execute(statement)
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# ESCOLA
# ===========================================================================

def inserir_escola(nome, codigo_inep, cnpj, endereco, telefone, email):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO escola (nome_escola, codigo_inep, cnpj, endereco_escola, telefone_escola, email_escola)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_escola""",
            (nome, codigo_inep, cnpj, endereco, telefone, email),
        )
        novo_id = cur.fetchone()["id_escola"]
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, endereco_escola, telefone_escola,
                email_escola, criado_em, atualizado_em
                FROM escola WHERE id_escola = %s""", (novo_id,))
        return cur.fetchone()


def listar_escolas():
    with cursor() as cur:
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, endereco_escola, telefone_escola,
                email_escola, criado_em, atualizado_em
                FROM escola ORDER BY id_escola""")
        return cur.fetchall()


def buscar_escola(id_escola):
    with cursor() as cur:
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, endereco_escola, telefone_escola,
                email_escola, criado_em, atualizado_em
                FROM escola WHERE id_escola = %s""", (id_escola,))
        return cur.fetchone()


def atualizar_escola(id_escola, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE escola SET {set_clause} WHERE id_escola = %s", (*campos.values(), id_escola))
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, endereco_escola, telefone_escola,
                email_escola, criado_em, atualizado_em
                FROM escola WHERE id_escola = %s""", (id_escola,))
        return cur.fetchone()


def excluir_escola(id_escola) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM escola WHERE id_escola = %s", (id_escola,))
        return cur.rowcount > 0


# ===========================================================================
# PERIODO
# ===========================================================================

def inserir_periodo(ano, nome_periodo, data_inicio, data_fim, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO periodo (ano, nome_periodo, data_inicio, data_fim, situacao)
               VALUES (%s, %s, %s, %s, %s) RETURNING id_periodo""",
            (ano, nome_periodo, data_inicio, data_fim, situacao),
        )
        novo_id = cur.fetchone()["id_periodo"]
        cur.execute("""SELECT id_periodo, ano, nome_periodo,
                data_inicio, data_fim, situacao,
                criado_em, atualizado_em
                FROM periodo WHERE id_periodo = %s""", (novo_id,))
        return cur.fetchone()


def listar_periodos():
    with cursor() as cur:
        cur.execute("""SELECT id_periodo, ano, nome_periodo,
                data_inicio, data_fim, situacao,
                criado_em, atualizado_em
                FROM periodo ORDER BY id_periodo""")
        return cur.fetchall()


def buscar_periodo(id_periodo):
    with cursor() as cur:
        cur.execute("""SELECT id_periodo, ano, nome_periodo,
                data_inicio, data_fim, situacao,
                criado_em, atualizado_em
                FROM periodo WHERE id_periodo = %s""", (id_periodo,))
        return cur.fetchone()


def atualizar_periodo(id_periodo, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE periodo SET {set_clause} WHERE id_periodo = %s", (*campos.values(), id_periodo))
        cur.execute("""SELECT id_periodo, ano, nome_periodo,
                data_inicio, data_fim, situacao,
                criado_em, atualizado_em
                FROM periodo WHERE id_periodo = %s""", (id_periodo,))
        return cur.fetchone()


def excluir_periodo(id_periodo) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM periodo WHERE id_periodo = %s", (id_periodo,))
        return cur.rowcount > 0


# ===========================================================================
# MATERIA
# ===========================================================================

def inserir_materia(nome, carga_horaria):
    with cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO materia (nome_materia, carga_horaria) VALUES (%s, %s) RETURNING id_materia", 
            (nome, carga_horaria)
        )
        novo_id = cur.fetchone()["id_materia"]
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria
                FROM materia WHERE id_materia = %s""", (novo_id,))
        return cur.fetchone()


def listar_materias():
    with cursor() as cur:
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria
                FROM materia ORDER BY id_materia""")
        return cur.fetchall()


def buscar_materia(id_materia):
    with cursor() as cur:
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria
                FROM materia WHERE id_materia = %s""", (id_materia,))
        return cur.fetchone()


def atualizar_materia(id_materia, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE materia SET {set_clause} WHERE id_materia = %s", (*campos.values(), id_materia))
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria
                FROM materia WHERE id_materia = %s""", (id_materia,))
        return cur.fetchone()


def excluir_materia(id_materia) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM materia WHERE id_materia = %s", (id_materia,))
        return cur.rowcount > 0


# ===========================================================================
# RESPONSAVEL
# ===========================================================================

def inserir_responsavel(nome, cpf, telefone, email, cep, endereco):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO responsavel (nome_resp, cpf_resp, telefone_resp, email_resp, cep_resp, endereco_resp)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_responsavel""",
            (nome, cpf, telefone, email, cep, endereco),
        )
        novo_id = cur.fetchone()["id_responsavel"]
        cur.execute("""SELECT id_responsavel, nome_resp, cpf_resp,
                telefone_resp, email_resp, cep_resp,
                endereco_resp, criado_em, atualizado_em
                FROM responsavel WHERE id_responsavel = %s""", (novo_id,))
        return cur.fetchone()


def listar_responsaveis():
    with cursor() as cur:
        cur.execute("""SELECT id_responsavel, nome_resp, cpf_resp,
                telefone_resp, email_resp, cep_resp,
                endereco_resp, criado_em, atualizado_em
                FROM responsavel ORDER BY id_responsavel""")
        return cur.fetchall()


def buscar_responsavel(id_responsavel):
    with cursor() as cur:
        cur.execute("""SELECT id_responsavel, nome_resp, cpf_resp,
                telefone_resp, email_resp, cep_resp,
                endereco_resp, criado_em, atualizado_em
                FROM responsavel WHERE id_responsavel = %s""", (id_responsavel,))
        return cur.fetchone()


def atualizar_responsavel(id_responsavel, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE responsavel SET {set_clause} WHERE id_responsavel = %s",
            (*campos.values(), id_responsavel),
        )
        cur.execute("""SELECT id_responsavel, nome_resp, cpf_resp,
                telefone_resp, email_resp, cep_resp,
                endereco_resp, criado_em, atualizado_em
                FROM responsavel WHERE id_responsavel = %s""", (id_responsavel,))
        return cur.fetchone()


def excluir_responsavel(id_responsavel) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM responsavel WHERE id_responsavel = %s", (id_responsavel,))
        return cur.rowcount > 0


# ===========================================================================
# ALUNO
# ===========================================================================

def inserir_aluno(numero_matricula, nome, data_nascimento, cpf, telefone, email, cep, endereco, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO aluno (numero_matricula, nome_aluno, data_nascimento, cpf_aluno,
                                   telefone_aluno, email_aluno, cep_aluno, endereco_aluno, situacao)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_aluno""",
            (numero_matricula, nome, data_nascimento, cpf, telefone, email, cep, endereco, situacao),
        )
        novo_id = cur.fetchone()["id_aluno"]
        cur.execute("""SELECT id_aluno, numero_matricula, nome_aluno,
                data_nascimento, cpf_aluno, telefone_aluno,
                email_aluno, cep_aluno, endereco_aluno,
                situacao, criado_em, atualizado_em
                FROM aluno WHERE id_aluno = %s""", (novo_id,))
        return cur.fetchone()

def listar_alunos(situacao: str | None = None, nome: str | None = None):
    query = """SELECT id_aluno, numero_matricula, nome_aluno,
                data_nascimento, cpf_aluno, telefone_aluno,
                email_aluno, cep_aluno, endereco_aluno,
                situacao, criado_em, atualizado_em
                FROM aluno WHERE 1=1"""
    params = []
    if situacao:
        query += " AND situacao = %s"
        params.append(situacao)
    if nome:
        query += " AND nome_aluno LIKE %s"
        params.append(f"%{nome}%")
    query += " ORDER BY id_aluno"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT id_aluno, numero_matricula, nome_aluno,
                data_nascimento, cpf_aluno, telefone_aluno,
                email_aluno, cep_aluno, endereco_aluno,
                situacao, criado_em, atualizado_em
                FROM aluno WHERE id_aluno = %s""", (id_aluno,))
        return cur.fetchone()


def atualizar_aluno(id_aluno, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE aluno SET {set_clause} WHERE id_aluno = %s", (*campos.values(), id_aluno))
        cur.execute("""SELECT id_aluno, numero_matricula, nome_aluno,
                data_nascimento, cpf_aluno, telefone_aluno,
                email_aluno, cep_aluno, endereco_aluno,
                situacao, criado_em, atualizado_em
                FROM aluno WHERE id_aluno = %s""", (id_aluno,))
        return cur.fetchone()


def excluir_aluno(id_aluno) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM aluno WHERE id_aluno = %s", (id_aluno,))
        return cur.rowcount > 0


# Views ligadas ao aluno --------------------------------------------------

def escola_atual_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT id_aluno, id_escola, nome_escola
                FROM vw_aluno_escola_atual WHERE id_aluno = %s""", (id_aluno,))
        return cur.fetchone()


def responsaveis_financeiros_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT aluno_id_aluno AS aluno_id, id_responsavel, nome_resp,
                email_resp, telefone_resp
                FROM vw_aluno_responsavel_financeiro WHERE aluno_id_aluno = %s""", (id_aluno,))
        return cur.fetchall()


def medias_dinamicas_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id, materia_id_materia AS materia_id,
                media_calculada, qtd_avaliacoes_contabilizadas
                FROM vw_aluno_media_dinamica WHERE aluno_id_aluno = %s""", (id_aluno,))
        return cur.fetchall()


# ===========================================================================
# TURMA
# ===========================================================================

def inserir_turma(nome, serie, turno, capacidade, escola_id, ano_letivo):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO turma (nome_turma, serie, turno, capacidade, escola_id_escola, ano_letivo)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_turma""",
            (nome, serie, turno, capacidade, escola_id, ano_letivo),
        )
        novo_id = cur.fetchone()["id_turma"]
        cur.execute("""SELECT id_turma, nome_turma, serie,
                turno, capacidade, escola_id_escola AS escola_id,
                ano_letivo, criado_em, atualizado_em
                FROM turma WHERE id_turma = %s""", (novo_id,))
        return cur.fetchone()


def listar_turmas(escola_id: int | None = None):
    query = """SELECT id_turma, nome_turma, serie,
                turno, capacidade, escola_id_escola AS escola_id,
                ano_letivo, criado_em, atualizado_em
                FROM turma WHERE 1=1"""
    params = []
    if escola_id:
        query += " AND escola_id_escola = %s"
        params.append(escola_id)
    query += " ORDER BY id_turma"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_turma(id_turma):
    with cursor() as cur:
        cur.execute("""SELECT id_turma, nome_turma, serie,
                turno, capacidade, escola_id_escola AS escola_id,
                ano_letivo, criado_em, atualizado_em
                FROM turma WHERE id_turma = %s""", (id_turma,))
        return cur.fetchone()


_COLUNAS_DB_TURMA = {"escola_id": "escola_id_escola"}


def atualizar_turma(id_turma, campos: dict):
    set_clause = ", ".join(f"{_COLUNAS_DB_TURMA.get(c, c.lower())} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE turma SET {set_clause} WHERE id_turma = %s", (*campos.values(), id_turma))
        cur.execute("""SELECT id_turma, nome_turma, serie,
                turno, capacidade, escola_id_escola AS escola_id,
                ano_letivo, criado_em, atualizado_em
                FROM turma WHERE id_turma = %s""", (id_turma,))
        return cur.fetchone()


def excluir_turma(id_turma) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM turma WHERE id_turma = %s", (id_turma,))
        return cur.rowcount > 0


# ===========================================================================
# PROFESSOR
# ===========================================================================

def inserir_professor(nome, cpf, telefone, email, cep, endereco, situacao, escola_id):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO professor (nome_prof, cpf_prof, telefone_prof, email_prof, cep_prof,
                                       endereco_prof, situacao, escola_id_escola)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_professor""",
            (nome, cpf, telefone, email, cep, endereco, situacao, escola_id),
        )
        novo_id = cur.fetchone()["id_professor"]
        cur.execute("""SELECT id_professor, nome_prof, cpf_prof,
                telefone_prof, email_prof, cep_prof,
                endereco_prof, situacao, escola_id_escola AS escola_id,
                criado_em, atualizado_em
                FROM professor WHERE id_professor = %s""", (novo_id,))
        return cur.fetchone()


def listar_professores(escola_id: int | None = None):
    query = """SELECT id_professor, nome_prof, cpf_prof,
                telefone_prof, email_prof, cep_prof,
                endereco_prof, situacao, escola_id_escola AS escola_id,
                criado_em, atualizado_em
                FROM professor WHERE 1=1"""
    params = []
    if escola_id:
        query += " AND escola_id_escola = %s"
        params.append(escola_id)
    query += " ORDER BY id_professor"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_professor(id_professor):
    with cursor() as cur:
        cur.execute("""SELECT id_professor, nome_prof, cpf_prof,
                telefone_prof, email_prof, cep_prof,
                endereco_prof, situacao, escola_id_escola AS escola_id,
                criado_em, atualizado_em
                FROM professor WHERE id_professor = %s""", (id_professor,))
        return cur.fetchone()


_COLUNAS_DB_PROFESSOR = {"escola_id": "escola_id_escola"}


def atualizar_professor(id_professor, campos: dict):
    set_clause = ", ".join(f"{_COLUNAS_DB_PROFESSOR.get(c, c.lower())} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE professor SET {set_clause} WHERE id_professor = %s", (*campos.values(), id_professor))
        cur.execute("""SELECT id_professor, nome_prof, cpf_prof,
                telefone_prof, email_prof, cep_prof,
                endereco_prof, situacao, escola_id_escola AS escola_id,
                criado_em, atualizado_em
                FROM professor WHERE id_professor = %s""", (id_professor,))
        return cur.fetchone()


def excluir_professor(id_professor) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM professor WHERE id_professor = %s", (id_professor,))
        return cur.rowcount > 0


# ===========================================================================
# MATRICULA (aluno <-> turma)
# ===========================================================================

def inserir_matricula(aluno_id, turma_id, data_matricula, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO matricula (aluno_id_aluno, turma_id_turma, data_matricula, situacao)
               VALUES (%s, %s, %s, %s) RETURNING id_matricula""",
            (aluno_id, turma_id, data_matricula, situacao),
        )
        novo_id = cur.fetchone()["id_matricula"]
        cur.execute("""SELECT id_matricula, aluno_id_aluno AS aluno_id, turma_id_turma AS turma_id,
                data_matricula, situacao, criado_em,
                atualizado_em
                FROM matricula WHERE id_matricula = %s""", (novo_id,))
        return cur.fetchone()


def listar_matriculas(aluno_id: int | None = None, turma_id: int | None = None):
    query = """SELECT id_matricula, aluno_id_aluno AS aluno_id, turma_id_turma AS turma_id,
                data_matricula, situacao, criado_em,
                atualizado_em
                FROM matricula WHERE 1=1"""
    params = []
    if aluno_id:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    if turma_id:
        query += " AND turma_id_turma = %s"
        params.append(turma_id)
    query += " ORDER BY id_matricula"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_matricula(id_matricula):
    with cursor() as cur:
        cur.execute("""SELECT id_matricula, aluno_id_aluno AS aluno_id, turma_id_turma AS turma_id,
                data_matricula, situacao, criado_em,
                atualizado_em
                FROM matricula WHERE id_matricula = %s""", (id_matricula,))
        return cur.fetchone()


_COLUNAS_DB_MATRICULA = {"aluno_id": "aluno_id_aluno", "turma_id": "turma_id_turma"}


def atualizar_matricula(id_matricula, campos: dict):
    set_clause = ", ".join(f"{_COLUNAS_DB_MATRICULA.get(c, c.lower())} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE matricula SET {set_clause} WHERE id_matricula = %s", (*campos.values(), id_matricula))
        cur.execute("""SELECT id_matricula, aluno_id_aluno AS aluno_id, turma_id_turma AS turma_id,
                data_matricula, situacao, criado_em,
                atualizado_em
                FROM matricula WHERE id_matricula = %s""", (id_matricula,))
        return cur.fetchone()


def excluir_matricula(id_matricula) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM matricula WHERE id_matricula = %s", (id_matricula,))
        return cur.rowcount > 0


# ===========================================================================
# ALUNORESPONSAVEL (junção aluno <-> responsavel, PK composta)
# ===========================================================================

def vincular_responsavel(aluno_id, responsavel_id, tipo, financeiro):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO alunoresponsavel (aluno_id_aluno, responsavel_id_responsavel, tipo_responsavel, responsavel_financeiro)
               VALUES (%s, %s, %s, %s)""",
            (aluno_id, responsavel_id, tipo, financeiro),
        )
        cur.execute(
            """SELECT aluno_id_aluno AS aluno_id, responsavel_id_responsavel AS responsavel_id, tipo_responsavel,
                responsavel_financeiro
                FROM alunoresponsavel WHERE aluno_id_aluno = %s AND responsavel_id_responsavel = %s""",
            (aluno_id, responsavel_id),
        )
        return cur.fetchone()


def listar_responsaveis_do_aluno(aluno_id):
    with cursor() as cur:
        cur.execute(
            """SELECT ar.aluno_id_aluno AS aluno_id,
                      ar.responsavel_id_responsavel AS responsavel_id,
                      ar.tipo_responsavel,
                      ar.responsavel_financeiro,
                      r.nome_resp, r.email_resp, r.telefone_resp
               FROM alunoresponsavel ar
               JOIN responsavel r ON r.id_responsavel = ar.responsavel_id_responsavel
               WHERE ar.aluno_id_aluno = %s""",
            (aluno_id,),
        )
        return cur.fetchall()


def buscar_vinculo(aluno_id, responsavel_id):
    with cursor() as cur:
        cur.execute(
            """SELECT aluno_id_aluno AS aluno_id, responsavel_id_responsavel AS responsavel_id, tipo_responsavel,
                responsavel_financeiro
                FROM alunoresponsavel WHERE aluno_id_aluno = %s AND responsavel_id_responsavel = %s""",
            (aluno_id, responsavel_id),
        )
        return cur.fetchone()


def desvincular_responsavel(aluno_id, responsavel_id) -> bool:
    with cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM alunoresponsavel WHERE aluno_id_aluno = %s AND responsavel_id_responsavel = %s",
            (aluno_id, responsavel_id),
        )
        return cur.rowcount > 0


# ===========================================================================
# GRADE CURRICULAR (turma <-> materia <-> professor)
# ===========================================================================

def inserir_grade(turma_id, materia_id, professor_id):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO grade_curricular (turma_id_turma, materia_id_materia, professor_id_professor)
               VALUES (%s, %s, %s) RETURNING id_grade""",
            (turma_id, materia_id, professor_id),
        )
        novo_id = cur.fetchone()["id_grade"]
        cur.execute("""SELECT id_grade, turma_id_turma AS turma_id, materia_id_materia AS materia_id,
                professor_id_professor AS professor_id
                FROM grade_curricular WHERE id_grade = %s""", (novo_id,))
        return cur.fetchone()


def listar_grades(turma_id: int | None = None):
    query = """SELECT id_grade, turma_id_turma AS turma_id, materia_id_materia AS materia_id,
                professor_id_professor AS professor_id
                FROM grade_curricular WHERE 1=1"""
    params = []
    if turma_id:
        query += " AND turma_id_turma = %s"
        params.append(turma_id)
    query += " ORDER BY id_grade"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_grade(id_grade):
    with cursor() as cur:
        cur.execute("""SELECT id_grade, turma_id_turma AS turma_id, materia_id_materia AS materia_id,
                professor_id_professor AS professor_id
                FROM grade_curricular WHERE id_grade = %s""", (id_grade,))
        return cur.fetchone()


def excluir_grade(id_grade) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM grade_curricular WHERE id_grade = %s", (id_grade,))
        return cur.rowcount > 0


# ===========================================================================
# AVALIACAO
# ===========================================================================

def inserir_avaliacao(grade_id, periodo_id, tipo, nome, data_avaliacao, peso):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO avaliacao (grade_id_grade, periodo_id_periodo, tipo, nome_avaliacao, data_avaliacao, peso)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_avaliacao""",
            (grade_id, periodo_id, tipo, nome, data_avaliacao, peso),
        )
        novo_id = cur.fetchone()["id_avaliacao"]
        cur.execute("""SELECT id_avaliacao, grade_id_grade AS grade_id, periodo_id_periodo AS periodo_id,
                tipo, nome_avaliacao, data_avaliacao,
                peso
                FROM avaliacao WHERE id_avaliacao = %s""", (novo_id,))
        return cur.fetchone()


def listar_avaliacoes(grade_id: int | None = None, periodo_id: int | None = None):
    query = """SELECT id_avaliacao, grade_id_grade AS grade_id, periodo_id_periodo AS periodo_id,
                tipo, nome_avaliacao, data_avaliacao,
                peso
                FROM avaliacao WHERE 1=1"""
    params = []
    if grade_id:
        query += " AND grade_id_grade = %s"
        params.append(grade_id)
    if periodo_id:
        query += " AND periodo_id_periodo = %s"
        params.append(periodo_id)
    query += " ORDER BY id_avaliacao"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_avaliacao(id_avaliacao):
    with cursor() as cur:
        cur.execute("""SELECT id_avaliacao, grade_id_grade AS grade_id, periodo_id_periodo AS periodo_id,
                tipo, nome_avaliacao, data_avaliacao,
                peso
                FROM avaliacao WHERE id_avaliacao = %s""", (id_avaliacao,))
        return cur.fetchone()


_COLUNAS_DB_AVALIACAO = {"grade_id": "grade_id_grade", "periodo_id": "periodo_id_periodo"}


def atualizar_avaliacao(id_avaliacao, campos: dict):
    set_clause = ", ".join(f"{_COLUNAS_DB_AVALIACAO.get(c, c.lower())} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE avaliacao SET {set_clause} WHERE id_avaliacao = %s", (*campos.values(), id_avaliacao))
        cur.execute("""SELECT id_avaliacao, grade_id_grade AS grade_id, periodo_id_periodo AS periodo_id,
                tipo, nome_avaliacao, data_avaliacao,
                peso
                FROM avaliacao WHERE id_avaliacao = %s""", (id_avaliacao,))
        return cur.fetchone()


def excluir_avaliacao(id_avaliacao) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM avaliacao WHERE id_avaliacao = %s", (id_avaliacao,))
        return cur.rowcount > 0


# ===========================================================================
# NOTA
# ===========================================================================

def inserir_nota(avaliacao_id, aluno_id, valor):
    with cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO nota (avaliacao_id_avaliacao, aluno_id_aluno, valor_nota) VALUES (%s, %s, %s) RETURNING id_nota",
            (avaliacao_id, aluno_id, valor),
        )
        novo_id = cur.fetchone()["id_nota"]
        cur.execute("""SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota
                FROM nota WHERE id_nota = %s""", (novo_id,))
        return cur.fetchone()

def listar_notas(avaliacao_id: int | None = None, aluno_id: int | None = None):
    query = """SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota
                FROM nota WHERE 1=1"""
    params = []
    if avaliacao_id:
        query += " AND avaliacao_id_avaliacao = %s"
        params.append(avaliacao_id)
    if aluno_id:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    query += " ORDER BY id_nota"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_nota(id_nota):
    with cursor() as cur:
        cur.execute("""SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota
                FROM nota WHERE id_nota = %s""", (id_nota,))
        return cur.fetchone()


def atualizar_nota(id_nota, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE nota SET {set_clause} WHERE id_nota = %s", (*campos.values(), id_nota))
        cur.execute("""SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota
                FROM nota WHERE id_nota = %s""", (id_nota,))
        return cur.fetchone()


def excluir_nota(id_nota) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM nota WHERE id_nota = %s", (id_nota,))
        return cur.rowcount > 0


# ===========================================================================
# FREQUENCIA
# ===========================================================================

def inserir_frequencia(grade_id, aluno_id, data_frequencia, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO frequencia (grade_id_grade, aluno_id_aluno, data_frequencia, situacao)
               VALUES (%s, %s, %s, %s) RETURNING id_frequencia""",
            (grade_id, aluno_id, data_frequencia, situacao),
        )
        novo_id = cur.fetchone()["id_frequencia"]
        cur.execute("""SELECT id_frequencia, grade_id_grade AS grade_id, aluno_id_aluno AS aluno_id,
                data_frequencia, situacao
                FROM frequencia WHERE id_frequencia = %s""", (novo_id,))
        return cur.fetchone()


def listar_frequencias(grade_id: int | None = None, aluno_id: int | None = None):
    query = """SELECT id_frequencia, grade_id_grade AS grade_id, aluno_id_aluno AS aluno_id,
                data_frequencia, situacao
                FROM frequencia WHERE 1=1"""
    params = []
    if grade_id:
        query += " AND grade_id_grade = %s"
        params.append(grade_id)
    if aluno_id:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    query += " ORDER BY id_frequencia"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_frequencia(id_frequencia):
    with cursor() as cur:
        cur.execute("""SELECT id_frequencia, grade_id_grade AS grade_id, aluno_id_aluno AS aluno_id,
                data_frequencia, situacao
                FROM frequencia WHERE id_frequencia = %s""", (id_frequencia,))
        return cur.fetchone()


def atualizar_frequencia(id_frequencia, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE frequencia SET {set_clause} WHERE id_frequencia = %s",
            (*campos.values(), id_frequencia),
        )
        cur.execute("""SELECT id_frequencia, grade_id_grade AS grade_id, aluno_id_aluno AS aluno_id,
                data_frequencia, situacao
                FROM frequencia WHERE id_frequencia = %s""", (id_frequencia,))
        return cur.fetchone()


def excluir_frequencia(id_frequencia) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM frequencia WHERE id_frequencia = %s", (id_frequencia,))
        return cur.rowcount > 0


# ===========================================================================
# BOLETIM
# ===========================================================================

def inserir_boletim(aluno_id, periodo_id, materia_id, media_final, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO boletim (aluno_id_aluno, periodo_id_periodo, materia_id_materia, media_final, situacao)
               VALUES (%s, %s, %s, %s, %s) RETURNING id_boletim""",
            (aluno_id, periodo_id, materia_id, media_final, situacao),
        )
        novo_id = cur.fetchone()["id_boletim"]
        cur.execute("""SELECT id_boletim, aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id,
                materia_id_materia AS materia_id, media_final, situacao
                FROM boletim WHERE id_boletim = %s""", (novo_id,))
        return cur.fetchone()


def listar_boletins(aluno_id: int | None = None, periodo_id: int | None = None):
    query = """SELECT id_boletim, aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id,
                materia_id_materia AS materia_id, media_final, situacao
                FROM boletim WHERE 1=1"""
    params = []
    if aluno_id:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    if periodo_id:
        query += " AND periodo_id_periodo = %s"
        params.append(periodo_id)
    query += " ORDER BY id_boletim"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_boletim(id_boletim):
    with cursor() as cur:
        cur.execute("""SELECT id_boletim, aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id,
                materia_id_materia AS materia_id, media_final, situacao
                FROM boletim WHERE id_boletim = %s""", (id_boletim,))
        return cur.fetchone()


def atualizar_boletim(id_boletim, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boletim SET {set_clause} WHERE id_boletim = %s", (*campos.values(), id_boletim))
        cur.execute("""SELECT id_boletim, aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id,
                materia_id_materia AS materia_id, media_final, situacao
                FROM boletim WHERE id_boletim = %s""", (id_boletim,))
        return cur.fetchone()


def excluir_boletim(id_boletim) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM boletim WHERE id_boletim = %s", (id_boletim,))
        return cur.rowcount > 0


# ===========================================================================
# BOLETO
# ===========================================================================

def inserir_boleto(numero_boleto, aluno_id, competencia, valor, data_vencimento, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO boleto (numero_boleto, aluno_id_aluno, competencia, valor_mensalidade, data_vencimento, situacao)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_boleto""",
            (numero_boleto, aluno_id, competencia, valor, data_vencimento, situacao),
        )
        novo_id = cur.fetchone()["id_boleto"]
        cur.execute("""SELECT id_boleto, numero_boleto, aluno_id_aluno AS aluno_id,
                competencia, valor_mensalidade, data_vencimento,
                data_pagamento, situacao
                FROM boleto WHERE id_boleto = %s""", (novo_id,))
        return cur.fetchone()


def listar_boletos(aluno_id: int | None = None, situacao: str | None = None):
    query = """SELECT id_boleto, numero_boleto, aluno_id_aluno AS aluno_id,
                competencia, valor_mensalidade, data_vencimento,
                data_pagamento, situacao
                FROM boleto WHERE 1=1"""
    params = []
    if aluno_id:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    if situacao:
        query += " AND situacao = %s"
        params.append(situacao)
    query += " ORDER BY id_boleto"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_boleto(id_boleto):
    with cursor() as cur:
        cur.execute("""SELECT id_boleto, numero_boleto, aluno_id_aluno AS aluno_id,
                competencia, valor_mensalidade, data_vencimento,
                data_pagamento, situacao
                FROM boleto WHERE id_boleto = %s""", (id_boleto,))
        return cur.fetchone()


def atualizar_boleto(id_boleto, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boleto SET {set_clause} WHERE id_boleto = %s", (*campos.values(), id_boleto))
        cur.execute("""SELECT id_boleto, numero_boleto, aluno_id_aluno AS aluno_id,
                competencia, valor_mensalidade, data_vencimento,
                data_pagamento, situacao
                FROM boleto WHERE id_boleto = %s""", (id_boleto,))
        return cur.fetchone()


def excluir_boleto(id_boleto) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM boleto WHERE id_boleto = %s", (id_boleto,))
        return cur.rowcount > 0