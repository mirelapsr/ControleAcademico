"""
db.py — CAMADA DE BANCO
=======================
Única parte do projeto que "fala SQL". As rotas (main.py) nunca escrevem SQL:
elas só chamam as funções daqui. Todas as consultas usam parâmetros via `%s`
(nunca concatenação de valores vindos do cliente).

Banco: MySQL (schema `Academic.sql` — database CAcademic).
Driver: PyMySQL, com DictCursor (equivalente ao RealDictCursor do psycopg2 —
as linhas voltam como dict, não como tupla).

Pré-requisito: o banco `CAcademic` já deve existir (rode `Academic.sql` uma
vez, ou crie manualmente com `CREATE DATABASE CAcademic;`). A API, no
startup, cria as TABELAS (`criar_tabelas`) usando `CREATE TABLE IF NOT
EXISTS` — portanto é seguro reiniciar a API sem perder dados.
"""

import os
from contextlib import contextmanager

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "CAcademic"),
    "port": int(os.getenv("DB_PORT", "3306")),
}


def conectar() -> pymysql.connections.Connection:
    """Abre e devolve uma conexão PyMySQL. cursorclass=DictCursor faz as
    linhas virem como dict (equivalente ao RealDictCursor do psycopg2)."""
    return pymysql.connect(
        host=CONFIG["host"],
        user=CONFIG["user"],
        password=CONFIG["password"],
        database=CONFIG["database"],
        port=CONFIG["port"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
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
# Espelha fielmente Academic.sql, apenas na ordem de dependência das FKs.
# ===========================================================================

def criar_tabelas() -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS escola (
        idEscola        INT AUTO_INCREMENT PRIMARY KEY,
        NomeEscola      VARCHAR(150) NOT NULL,
        CodigoInep      VARCHAR(8),
        Cnpj            VARCHAR(14),
        EnderecoEscola  VARCHAR(200),
        TelefoneEscola  VARCHAR(13),
        EmailEscola     VARCHAR(100)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS periodo (
        idPeriodo       INT AUTO_INCREMENT PRIMARY KEY,
        Ano             YEAR NOT NULL,
        NomePeriodo     VARCHAR(30) NOT NULL,
        DataInicio      DATE NOT NULL,
        DataFim         DATE NOT NULL,
        Situacao        ENUM('Ativo','Encerrado') NOT NULL DEFAULT 'Ativo'
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS materia (
        idMateria       INT AUTO_INCREMENT PRIMARY KEY,
        NomeMateria     VARCHAR(80) NOT NULL,
        CargaHoraria    INT
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS responsavel (
        idResponsavel   INT AUTO_INCREMENT PRIMARY KEY,
        NomeResp        VARCHAR(100) NOT NULL,
        CpfResp         VARCHAR(11),
        TelefoneResp    VARCHAR(13),
        EmailResp       VARCHAR(100),
        CepResp         VARCHAR(8),
        EnderecoResp    VARCHAR(200)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS aluno (
        idAluno         INT AUTO_INCREMENT PRIMARY KEY,
        NumeroMatricula VARCHAR(20) NOT NULL,
        NomeAluno       VARCHAR(100) NOT NULL,
        DataNascimento  DATE NOT NULL,
        CpfAluno        VARCHAR(11),
        TelefoneAluno   VARCHAR(13),
        EmailAluno      VARCHAR(100),
        CepAluno        VARCHAR(8),
        EnderecoAluno   VARCHAR(200),
        Situacao        ENUM('Ativo','Inativo','Transferido') NOT NULL DEFAULT 'Ativo'
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS turma (
        idTurma              INT AUTO_INCREMENT PRIMARY KEY,
        NomeTurma            VARCHAR(30) NOT NULL,
        Serie                VARCHAR(45),
        Turno                ENUM('Manha','Tarde','Noite','Integral') NOT NULL,
        Capacidade           INT,
        Escola_idEscola      INT NOT NULL,
        AnoLetivo            YEAR NOT NULL,
        CONSTRAINT fk_turma_escola FOREIGN KEY (Escola_idEscola) REFERENCES escola(idEscola)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS professor (
        idProfessor     INT AUTO_INCREMENT PRIMARY KEY,
        NomeProf        VARCHAR(100) NOT NULL,
        CpfProf         VARCHAR(11),
        TelefoneProf    VARCHAR(13),
        EmailProf       VARCHAR(100),
        CepProf         VARCHAR(8),
        EnderecoProf    VARCHAR(200),
        Situacao        ENUM('Ativo','Inativo') NOT NULL DEFAULT 'Ativo',
        Escola_idEscola INT NOT NULL,
        CONSTRAINT fk_professor_escola FOREIGN KEY (Escola_idEscola) REFERENCES escola(idEscola)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS alunoresponsavel (
        Aluno_idAluno             INT NOT NULL,
        Responsavel_idResponsavel INT NOT NULL,
        TipoResponsavel           ENUM('Pai','Mae','ResponsavelLegal','Outro') NOT NULL,
        ResponsavelFinanceiro     TINYINT(1) NOT NULL DEFAULT 0,
        PRIMARY KEY (Aluno_idAluno, Responsavel_idResponsavel),
        CONSTRAINT fk_ar_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno),
        CONSTRAINT fk_ar_responsavel FOREIGN KEY (Responsavel_idResponsavel) REFERENCES responsavel(idResponsavel)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS matricula (
        idMatricula     INT AUTO_INCREMENT PRIMARY KEY,
        Aluno_idAluno   INT NOT NULL,
        Turma_idTurma   INT NOT NULL,
        DataMatricula   DATE NOT NULL,
        Situacao        ENUM('Ativa','Cancelada','Transferida','Concluida') NOT NULL DEFAULT 'Ativa',
        CONSTRAINT fk_matricula_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno),
        CONSTRAINT fk_matricula_turma FOREIGN KEY (Turma_idTurma) REFERENCES turma(idTurma)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS grade_curricular (
        idGrade               INT AUTO_INCREMENT PRIMARY KEY,
        Turma_idTurma         INT NOT NULL,
        Materia_idMateria     INT NOT NULL,
        Professor_idProfessor INT NOT NULL,
        CONSTRAINT fk_grade_turma FOREIGN KEY (Turma_idTurma) REFERENCES turma(idTurma),
        CONSTRAINT fk_grade_materia FOREIGN KEY (Materia_idMateria) REFERENCES materia(idMateria),
        CONSTRAINT fk_grade_professor FOREIGN KEY (Professor_idProfessor) REFERENCES professor(idProfessor),
        UNIQUE KEY uq_turma_materia (Turma_idTurma, Materia_idMateria)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS avaliacao (
        idAvaliacao       INT AUTO_INCREMENT PRIMARY KEY,
        Grade_idGrade     INT NOT NULL,
        Periodo_idPeriodo INT NOT NULL,
        Tipo              ENUM('Prova','Trabalho','Projeto','Recuperacao') NOT NULL,
        NomeAvaliacao     VARCHAR(100) NOT NULL,
        DataAvaliacao     DATE NOT NULL,
        Peso              DECIMAL(4,2) NOT NULL DEFAULT 1.00,
        CONSTRAINT fk_avaliacao_grade FOREIGN KEY (Grade_idGrade) REFERENCES grade_curricular(idGrade),
        CONSTRAINT fk_avaliacao_periodo FOREIGN KEY (Periodo_idPeriodo) REFERENCES periodo(idPeriodo)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS nota (
        idNota                INT AUTO_INCREMENT PRIMARY KEY,
        Avaliacao_idAvaliacao INT NOT NULL,
        Aluno_idAluno         INT NOT NULL,
        ValorNota             DECIMAL(4,2) NOT NULL,
        CONSTRAINT fk_nota_avaliacao FOREIGN KEY (Avaliacao_idAvaliacao) REFERENCES avaliacao(idAvaliacao),
        CONSTRAINT fk_nota_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno),
        UNIQUE KEY uq_nota_avaliacao_aluno (Avaliacao_idAvaliacao, Aluno_idAluno)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS frequencia (
        idFrequencia    INT AUTO_INCREMENT PRIMARY KEY,
        Grade_idGrade   INT NOT NULL,
        Aluno_idAluno   INT NOT NULL,
        DataFrequencia  DATE NOT NULL,
        Situacao        ENUM('Presente','Falta','FaltaJustificada') NOT NULL,
        CONSTRAINT fk_frequencia_grade FOREIGN KEY (Grade_idGrade) REFERENCES grade_curricular(idGrade),
        CONSTRAINT fk_frequencia_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno),
        UNIQUE KEY uq_freq_aluno_grade_data (Grade_idGrade, Aluno_idAluno, DataFrequencia)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS boletim (
        idBoletim         INT AUTO_INCREMENT PRIMARY KEY,
        Aluno_idAluno     INT NOT NULL,
        Periodo_idPeriodo INT NOT NULL,
        Materia_idMateria INT NOT NULL,
        MediaFinal        DECIMAL(4,2) NOT NULL,
        Situacao          ENUM('Aberto','Fechado') NOT NULL DEFAULT 'Aberto',
        CONSTRAINT fk_boletim_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno),
        CONSTRAINT fk_boletim_periodo FOREIGN KEY (Periodo_idPeriodo) REFERENCES periodo(idPeriodo),
        CONSTRAINT fk_boletim_materia FOREIGN KEY (Materia_idMateria) REFERENCES materia(idMateria),
        UNIQUE KEY uq_boletim_aluno_periodo_materia (Aluno_idAluno, Periodo_idPeriodo, Materia_idMateria)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS boleto (
        idBoleto         INT AUTO_INCREMENT PRIMARY KEY,
        NumeroBoleto     VARCHAR(50) NOT NULL,
        Aluno_idAluno    INT NOT NULL,
        Competencia      CHAR(7) NOT NULL,
        ValorMensalidade DECIMAL(10,2) NOT NULL,
        DataVencimento   DATE NOT NULL,
        DataPagamento    DATE,
        Situacao         ENUM('Pendente','Pago','Atrasado','Cancelado') NOT NULL DEFAULT 'Pendente',
        CONSTRAINT fk_boleto_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno)
    ) ENGINE=InnoDB;
    """

    views = """
    CREATE OR REPLACE VIEW vw_aluno_escola_atual AS
    SELECT a.idAluno, e.idEscola, e.NomeEscola
    FROM aluno a
    JOIN matricula m ON m.Aluno_idAluno = a.idAluno AND m.Situacao = 'Ativa'
    JOIN turma t ON t.idTurma = m.Turma_idTurma
    JOIN escola e ON e.idEscola = t.Escola_idEscola;

    CREATE OR REPLACE VIEW vw_aluno_responsavel_financeiro AS
    SELECT ar.Aluno_idAluno, r.idResponsavel, r.NomeResp, r.EmailResp, r.TelefoneResp
    FROM alunoresponsavel ar
    JOIN responsavel r ON r.idResponsavel = ar.Responsavel_idResponsavel
    WHERE ar.ResponsavelFinanceiro = 1;

    CREATE OR REPLACE VIEW vw_aluno_media_dinamica AS
    SELECT
        n.Aluno_idAluno,
        a.Periodo_idPeriodo,
        g.Materia_idMateria,
        ROUND(SUM(n.ValorNota * a.Peso) / SUM(a.Peso), 2) AS MediaCalculada,
        COUNT(n.idNota) AS QtdAvaliacoesContabilizadas
    FROM nota n
    JOIN avaliacao a ON a.idAvaliacao = n.Avaliacao_idAvaliacao
    JOIN grade_curricular g ON g.idGrade = a.Grade_idGrade
    GROUP BY n.Aluno_idAluno, a.Periodo_idPeriodo, g.Materia_idMateria;
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
            """INSERT INTO escola (NomeEscola, CodigoInep, Cnpj, EnderecoEscola, TelefoneEscola, EmailEscola)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (nome, codigo_inep, cnpj, endereco, telefone, email),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM escola WHERE idEscola = %s", (novo_id,))
        return cur.fetchone()


def listar_escolas():
    with cursor() as cur:
        cur.execute("SELECT * FROM escola ORDER BY idEscola")
        return cur.fetchall()


def buscar_escola(id_escola):
    with cursor() as cur:
        cur.execute("SELECT * FROM escola WHERE idEscola = %s", (id_escola,))
        return cur.fetchone()


def atualizar_escola(id_escola, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE escola SET {set_clause} WHERE idEscola = %s", (*campos.values(), id_escola))
        cur.execute("SELECT * FROM escola WHERE idEscola = %s", (id_escola,))
        return cur.fetchone()


def excluir_escola(id_escola) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM escola WHERE idEscola = %s", (id_escola,))
        return cur.rowcount > 0


# ===========================================================================
# PERIODO
# ===========================================================================

def inserir_periodo(ano, nome_periodo, data_inicio, data_fim, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO periodo (Ano, NomePeriodo, DataInicio, DataFim, Situacao)
               VALUES (%s, %s, %s, %s, %s)""",
            (ano, nome_periodo, data_inicio, data_fim, situacao),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM periodo WHERE idPeriodo = %s", (novo_id,))
        return cur.fetchone()


def listar_periodos():
    with cursor() as cur:
        cur.execute("SELECT * FROM periodo ORDER BY idPeriodo")
        return cur.fetchall()


def buscar_periodo(id_periodo):
    with cursor() as cur:
        cur.execute("SELECT * FROM periodo WHERE idPeriodo = %s", (id_periodo,))
        return cur.fetchone()


def atualizar_periodo(id_periodo, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE periodo SET {set_clause} WHERE idPeriodo = %s", (*campos.values(), id_periodo))
        cur.execute("SELECT * FROM periodo WHERE idPeriodo = %s", (id_periodo,))
        return cur.fetchone()


def excluir_periodo(id_periodo) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM periodo WHERE idPeriodo = %s", (id_periodo,))
        return cur.rowcount > 0


# ===========================================================================
# MATERIA
# ===========================================================================

def inserir_materia(nome, carga_horaria):
    with cursor(commit=True) as cur:
        cur.execute("INSERT INTO materia (NomeMateria, CargaHoraria) VALUES (%s, %s)", (nome, carga_horaria))
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM materia WHERE idMateria = %s", (novo_id,))
        return cur.fetchone()


def listar_materias():
    with cursor() as cur:
        cur.execute("SELECT * FROM materia ORDER BY idMateria")
        return cur.fetchall()


def buscar_materia(id_materia):
    with cursor() as cur:
        cur.execute("SELECT * FROM materia WHERE idMateria = %s", (id_materia,))
        return cur.fetchone()


def atualizar_materia(id_materia, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE materia SET {set_clause} WHERE idMateria = %s", (*campos.values(), id_materia))
        cur.execute("SELECT * FROM materia WHERE idMateria = %s", (id_materia,))
        return cur.fetchone()


def excluir_materia(id_materia) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM materia WHERE idMateria = %s", (id_materia,))
        return cur.rowcount > 0


# ===========================================================================
# RESPONSAVEL
# ===========================================================================

def inserir_responsavel(nome, cpf, telefone, email, cep, endereco):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO responsavel (NomeResp, CpfResp, TelefoneResp, EmailResp, CepResp, EnderecoResp)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (nome, cpf, telefone, email, cep, endereco),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM responsavel WHERE idResponsavel = %s", (novo_id,))
        return cur.fetchone()


def listar_responsaveis():
    with cursor() as cur:
        cur.execute("SELECT * FROM responsavel ORDER BY idResponsavel")
        return cur.fetchall()


def buscar_responsavel(id_responsavel):
    with cursor() as cur:
        cur.execute("SELECT * FROM responsavel WHERE idResponsavel = %s", (id_responsavel,))
        return cur.fetchone()


def atualizar_responsavel(id_responsavel, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE responsavel SET {set_clause} WHERE idResponsavel = %s",
            (*campos.values(), id_responsavel),
        )
        cur.execute("SELECT * FROM responsavel WHERE idResponsavel = %s", (id_responsavel,))
        return cur.fetchone()


def excluir_responsavel(id_responsavel) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM responsavel WHERE idResponsavel = %s", (id_responsavel,))
        return cur.rowcount > 0


# ===========================================================================
# ALUNO
# ===========================================================================

def inserir_aluno(numero_matricula, nome, data_nascimento, cpf, telefone, email, cep, endereco, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO aluno (NumeroMatricula, NomeAluno, DataNascimento, CpfAluno,
                                   TelefoneAluno, EmailAluno, CepAluno, EnderecoAluno, Situacao)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (numero_matricula, nome, data_nascimento, cpf, telefone, email, cep, endereco, situacao),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM aluno WHERE idAluno = %s", (novo_id,))
        return cur.fetchone()


def listar_alunos(situacao: str | None = None, nome: str | None = None):
    query = "SELECT * FROM aluno WHERE 1=1"
    params = []
    if situacao:
        query += " AND Situacao = %s"
        params.append(situacao)
    if nome:
        query += " AND NomeAluno LIKE %s"
        params.append(f"%{nome}%")
    query += " ORDER BY idAluno"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("SELECT * FROM aluno WHERE idAluno = %s", (id_aluno,))
        return cur.fetchone()


def atualizar_aluno(id_aluno, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE aluno SET {set_clause} WHERE idAluno = %s", (*campos.values(), id_aluno))
        cur.execute("SELECT * FROM aluno WHERE idAluno = %s", (id_aluno,))
        return cur.fetchone()


def excluir_aluno(id_aluno) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM aluno WHERE idAluno = %s", (id_aluno,))
        return cur.rowcount > 0


# Views ligadas ao aluno --------------------------------------------------

def escola_atual_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("SELECT * FROM vw_aluno_escola_atual WHERE idAluno = %s", (id_aluno,))
        return cur.fetchone()


def responsaveis_financeiros_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("SELECT * FROM vw_aluno_responsavel_financeiro WHERE Aluno_idAluno = %s", (id_aluno,))
        return cur.fetchall()


def medias_dinamicas_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("SELECT * FROM vw_aluno_media_dinamica WHERE Aluno_idAluno = %s", (id_aluno,))
        return cur.fetchall()


# ===========================================================================
# TURMA
# ===========================================================================

def inserir_turma(nome, serie, turno, capacidade, escola_id, ano_letivo):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO turma (NomeTurma, Serie, Turno, Capacidade, Escola_idEscola, AnoLetivo)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (nome, serie, turno, capacidade, escola_id, ano_letivo),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM turma WHERE idTurma = %s", (novo_id,))
        return cur.fetchone()


def listar_turmas(escola_id: int | None = None):
    query = "SELECT * FROM turma WHERE 1=1"
    params = []
    if escola_id:
        query += " AND Escola_idEscola = %s"
        params.append(escola_id)
    query += " ORDER BY idTurma"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_turma(id_turma):
    with cursor() as cur:
        cur.execute("SELECT * FROM turma WHERE idTurma = %s", (id_turma,))
        return cur.fetchone()


def atualizar_turma(id_turma, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE turma SET {set_clause} WHERE idTurma = %s", (*campos.values(), id_turma))
        cur.execute("SELECT * FROM turma WHERE idTurma = %s", (id_turma,))
        return cur.fetchone()


def excluir_turma(id_turma) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM turma WHERE idTurma = %s", (id_turma,))
        return cur.rowcount > 0


# ===========================================================================
# PROFESSOR
# ===========================================================================

def inserir_professor(nome, cpf, telefone, email, cep, endereco, situacao, escola_id):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO professor (NomeProf, CpfProf, TelefoneProf, EmailProf, CepProf,
                                       EnderecoProf, Situacao, Escola_idEscola)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (nome, cpf, telefone, email, cep, endereco, situacao, escola_id),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM professor WHERE idProfessor = %s", (novo_id,))
        return cur.fetchone()


def listar_professores(escola_id: int | None = None):
    query = "SELECT * FROM professor WHERE 1=1"
    params = []
    if escola_id:
        query += " AND Escola_idEscola = %s"
        params.append(escola_id)
    query += " ORDER BY idProfessor"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_professor(id_professor):
    with cursor() as cur:
        cur.execute("SELECT * FROM professor WHERE idProfessor = %s", (id_professor,))
        return cur.fetchone()


def atualizar_professor(id_professor, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE professor SET {set_clause} WHERE idProfessor = %s", (*campos.values(), id_professor))
        cur.execute("SELECT * FROM professor WHERE idProfessor = %s", (id_professor,))
        return cur.fetchone()


def excluir_professor(id_professor) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM professor WHERE idProfessor = %s", (id_professor,))
        return cur.rowcount > 0


# ===========================================================================
# MATRICULA (aluno <-> turma)
# ===========================================================================

def inserir_matricula(aluno_id, turma_id, data_matricula, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO matricula (Aluno_idAluno, Turma_idTurma, DataMatricula, Situacao)
               VALUES (%s, %s, %s, %s)""",
            (aluno_id, turma_id, data_matricula, situacao),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM matricula WHERE idMatricula = %s", (novo_id,))
        return cur.fetchone()


def listar_matriculas(aluno_id: int | None = None, turma_id: int | None = None):
    query = "SELECT * FROM matricula WHERE 1=1"
    params = []
    if aluno_id:
        query += " AND Aluno_idAluno = %s"
        params.append(aluno_id)
    if turma_id:
        query += " AND Turma_idTurma = %s"
        params.append(turma_id)
    query += " ORDER BY idMatricula"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_matricula(id_matricula):
    with cursor() as cur:
        cur.execute("SELECT * FROM matricula WHERE idMatricula = %s", (id_matricula,))
        return cur.fetchone()


def atualizar_matricula(id_matricula, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE matricula SET {set_clause} WHERE idMatricula = %s", (*campos.values(), id_matricula))
        cur.execute("SELECT * FROM matricula WHERE idMatricula = %s", (id_matricula,))
        return cur.fetchone()


def excluir_matricula(id_matricula) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM matricula WHERE idMatricula = %s", (id_matricula,))
        return cur.rowcount > 0


# ===========================================================================
# ALUNORESPONSAVEL (junção aluno <-> responsavel, PK composta)
# ===========================================================================

def vincular_responsavel(aluno_id, responsavel_id, tipo, financeiro):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO alunoresponsavel (Aluno_idAluno, Responsavel_idResponsavel, TipoResponsavel, ResponsavelFinanceiro)
               VALUES (%s, %s, %s, %s)""",
            (aluno_id, responsavel_id, tipo, financeiro),
        )
        cur.execute(
            "SELECT * FROM alunoresponsavel WHERE Aluno_idAluno = %s AND Responsavel_idResponsavel = %s",
            (aluno_id, responsavel_id),
        )
        return cur.fetchone()


def listar_responsaveis_do_aluno(aluno_id):
    with cursor() as cur:
        cur.execute(
            """SELECT ar.*, r.NomeResp, r.EmailResp, r.TelefoneResp
               FROM alunoresponsavel ar
               JOIN responsavel r ON r.idResponsavel = ar.Responsavel_idResponsavel
               WHERE ar.Aluno_idAluno = %s""",
            (aluno_id,),
        )
        return cur.fetchall()


def buscar_vinculo(aluno_id, responsavel_id):
    with cursor() as cur:
        cur.execute(
            "SELECT * FROM alunoresponsavel WHERE Aluno_idAluno = %s AND Responsavel_idResponsavel = %s",
            (aluno_id, responsavel_id),
        )
        return cur.fetchone()


def desvincular_responsavel(aluno_id, responsavel_id) -> bool:
    with cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM alunoresponsavel WHERE Aluno_idAluno = %s AND Responsavel_idResponsavel = %s",
            (aluno_id, responsavel_id),
        )
        return cur.rowcount > 0


# ===========================================================================
# GRADE CURRICULAR (turma <-> materia <-> professor)
# ===========================================================================

def inserir_grade(turma_id, materia_id, professor_id):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO grade_curricular (Turma_idTurma, Materia_idMateria, Professor_idProfessor)
               VALUES (%s, %s, %s)""",
            (turma_id, materia_id, professor_id),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM grade_curricular WHERE idGrade = %s", (novo_id,))
        return cur.fetchone()


def listar_grades(turma_id: int | None = None):
    query = "SELECT * FROM grade_curricular WHERE 1=1"
    params = []
    if turma_id:
        query += " AND Turma_idTurma = %s"
        params.append(turma_id)
    query += " ORDER BY idGrade"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_grade(id_grade):
    with cursor() as cur:
        cur.execute("SELECT * FROM grade_curricular WHERE idGrade = %s", (id_grade,))
        return cur.fetchone()


def excluir_grade(id_grade) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM grade_curricular WHERE idGrade = %s", (id_grade,))
        return cur.rowcount > 0


# ===========================================================================
# AVALIACAO
# ===========================================================================

def inserir_avaliacao(grade_id, periodo_id, tipo, nome, data_avaliacao, peso):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO avaliacao (Grade_idGrade, Periodo_idPeriodo, Tipo, NomeAvaliacao, DataAvaliacao, Peso)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (grade_id, periodo_id, tipo, nome, data_avaliacao, peso),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM avaliacao WHERE idAvaliacao = %s", (novo_id,))
        return cur.fetchone()


def listar_avaliacoes(grade_id: int | None = None, periodo_id: int | None = None):
    query = "SELECT * FROM avaliacao WHERE 1=1"
    params = []
    if grade_id:
        query += " AND Grade_idGrade = %s"
        params.append(grade_id)
    if periodo_id:
        query += " AND Periodo_idPeriodo = %s"
        params.append(periodo_id)
    query += " ORDER BY idAvaliacao"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_avaliacao(id_avaliacao):
    with cursor() as cur:
        cur.execute("SELECT * FROM avaliacao WHERE idAvaliacao = %s", (id_avaliacao,))
        return cur.fetchone()


def atualizar_avaliacao(id_avaliacao, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE avaliacao SET {set_clause} WHERE idAvaliacao = %s", (*campos.values(), id_avaliacao))
        cur.execute("SELECT * FROM avaliacao WHERE idAvaliacao = %s", (id_avaliacao,))
        return cur.fetchone()


def excluir_avaliacao(id_avaliacao) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM avaliacao WHERE idAvaliacao = %s", (id_avaliacao,))
        return cur.rowcount > 0


# ===========================================================================
# NOTA
# ===========================================================================

def inserir_nota(avaliacao_id, aluno_id, valor):
    with cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO nota (Avaliacao_idAvaliacao, Aluno_idAluno, ValorNota) VALUES (%s, %s, %s)",
            (avaliacao_id, aluno_id, valor),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM nota WHERE idNota = %s", (novo_id,))
        return cur.fetchone()


def listar_notas(avaliacao_id: int | None = None, aluno_id: int | None = None):
    query = "SELECT * FROM nota WHERE 1=1"
    params = []
    if avaliacao_id:
        query += " AND Avaliacao_idAvaliacao = %s"
        params.append(avaliacao_id)
    if aluno_id:
        query += " AND Aluno_idAluno = %s"
        params.append(aluno_id)
    query += " ORDER BY idNota"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_nota(id_nota):
    with cursor() as cur:
        cur.execute("SELECT * FROM nota WHERE idNota = %s", (id_nota,))
        return cur.fetchone()


def atualizar_nota(id_nota, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE nota SET {set_clause} WHERE idNota = %s", (*campos.values(), id_nota))
        cur.execute("SELECT * FROM nota WHERE idNota = %s", (id_nota,))
        return cur.fetchone()


def excluir_nota(id_nota) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM nota WHERE idNota = %s", (id_nota,))
        return cur.rowcount > 0


# ===========================================================================
# FREQUENCIA
# ===========================================================================

def inserir_frequencia(grade_id, aluno_id, data_frequencia, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO frequencia (Grade_idGrade, Aluno_idAluno, DataFrequencia, Situacao)
               VALUES (%s, %s, %s, %s)""",
            (grade_id, aluno_id, data_frequencia, situacao),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM frequencia WHERE idFrequencia = %s", (novo_id,))
        return cur.fetchone()


def listar_frequencias(grade_id: int | None = None, aluno_id: int | None = None):
    query = "SELECT * FROM frequencia WHERE 1=1"
    params = []
    if grade_id:
        query += " AND Grade_idGrade = %s"
        params.append(grade_id)
    if aluno_id:
        query += " AND Aluno_idAluno = %s"
        params.append(aluno_id)
    query += " ORDER BY idFrequencia"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_frequencia(id_frequencia):
    with cursor() as cur:
        cur.execute("SELECT * FROM frequencia WHERE idFrequencia = %s", (id_frequencia,))
        return cur.fetchone()


def atualizar_frequencia(id_frequencia, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE frequencia SET {set_clause} WHERE idFrequencia = %s",
            (*campos.values(), id_frequencia),
        )
        cur.execute("SELECT * FROM frequencia WHERE idFrequencia = %s", (id_frequencia,))
        return cur.fetchone()


def excluir_frequencia(id_frequencia) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM frequencia WHERE idFrequencia = %s", (id_frequencia,))
        return cur.rowcount > 0


# ===========================================================================
# BOLETIM
# ===========================================================================

def inserir_boletim(aluno_id, periodo_id, materia_id, media_final, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO boletim (Aluno_idAluno, Periodo_idPeriodo, Materia_idMateria, MediaFinal, Situacao)
               VALUES (%s, %s, %s, %s, %s)""",
            (aluno_id, periodo_id, materia_id, media_final, situacao),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM boletim WHERE idBoletim = %s", (novo_id,))
        return cur.fetchone()


def listar_boletins(aluno_id: int | None = None, periodo_id: int | None = None):
    query = "SELECT * FROM boletim WHERE 1=1"
    params = []
    if aluno_id:
        query += " AND Aluno_idAluno = %s"
        params.append(aluno_id)
    if periodo_id:
        query += " AND Periodo_idPeriodo = %s"
        params.append(periodo_id)
    query += " ORDER BY idBoletim"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_boletim(id_boletim):
    with cursor() as cur:
        cur.execute("SELECT * FROM boletim WHERE idBoletim = %s", (id_boletim,))
        return cur.fetchone()


def atualizar_boletim(id_boletim, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boletim SET {set_clause} WHERE idBoletim = %s", (*campos.values(), id_boletim))
        cur.execute("SELECT * FROM boletim WHERE idBoletim = %s", (id_boletim,))
        return cur.fetchone()


def excluir_boletim(id_boletim) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM boletim WHERE idBoletim = %s", (id_boletim,))
        return cur.rowcount > 0


# ===========================================================================
# BOLETO
# ===========================================================================

def inserir_boleto(numero_boleto, aluno_id, competencia, valor, data_vencimento, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO boleto (NumeroBoleto, Aluno_idAluno, Competencia, ValorMensalidade, DataVencimento, Situacao)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (numero_boleto, aluno_id, competencia, valor, data_vencimento, situacao),
        )
        novo_id = cur.lastrowid
        cur.execute("SELECT * FROM boleto WHERE idBoleto = %s", (novo_id,))
        return cur.fetchone()


def listar_boletos(aluno_id: int | None = None, situacao: str | None = None):
    query = "SELECT * FROM boleto WHERE 1=1"
    params = []
    if aluno_id:
        query += " AND Aluno_idAluno = %s"
        params.append(aluno_id)
    if situacao:
        query += " AND Situacao = %s"
        params.append(situacao)
    query += " ORDER BY idBoleto"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_boleto(id_boleto):
    with cursor() as cur:
        cur.execute("SELECT * FROM boleto WHERE idBoleto = %s", (id_boleto,))
        return cur.fetchone()


def atualizar_boleto(id_boleto, campos: dict):
    set_clause = ", ".join(f"{c} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boleto SET {set_clause} WHERE idBoleto = %s", (*campos.values(), id_boleto))
        cur.execute("SELECT * FROM boleto WHERE idBoleto = %s", (id_boleto,))
        return cur.fetchone()


def excluir_boleto(id_boleto) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM boleto WHERE idBoleto = %s", (id_boleto,))
        return cur.rowcount > 0
