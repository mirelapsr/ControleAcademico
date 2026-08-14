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
        idescola        SERIAL PRIMARY KEY,
        nomeescola      VARCHAR(150) NOT NULL,
        codigoinep      VARCHAR(8),
        cnpj            VARCHAR(14),
        enderecoescola  VARCHAR(200),
        telefoneescola  VARCHAR(13),
        emailescola     VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS periodo (
        idperiodo       SERIAL PRIMARY KEY,
        ano             SMALLINT NOT NULL,
        nomeperiodo     VARCHAR(30) NOT NULL,
        datainicio      DATE NOT NULL,
        datafim         DATE NOT NULL,
        situacao        VARCHAR(50) CHECK (situacao IN ('Ativo','Encerrado')) NOT NULL DEFAULT 'Ativo'
    );

    CREATE TABLE IF NOT EXISTS materia (
        idmateria       SERIAL PRIMARY KEY,
        nomemateria     VARCHAR(80) NOT NULL,
        cargahoraria    INTEGER CHECK (cargahoraria > 0),
        CONSTRAINT uq_materia_nome UNIQUE (nomemateria)
    );

    CREATE TABLE IF NOT EXISTS responsavel (
        idresponsavel   SERIAL PRIMARY KEY,
        nomeresp        VARCHAR(100) NOT NULL,
        cpfresp         VARCHAR(11),
        telefoneresp    VARCHAR(13),
        emailresp       VARCHAR(100),
        cepresp         VARCHAR(8),
        enderecoresp    VARCHAR(200)
    );

    CREATE TABLE IF NOT EXISTS aluno (
        idaluno         SERIAL PRIMARY KEY,
        numeromatricula VARCHAR(20) NOT NULL,
        nomealuno       VARCHAR(100) NOT NULL,
        datanascimento  DATE NOT NULL,
        cpfaluno        VARCHAR(11),
        telefonealuno   VARCHAR(13),
        emailaluno      VARCHAR(100),
        cepaluno        VARCHAR(8),
        enderecoaluno   VARCHAR(200),
        situacao        VARCHAR(50) CHECK (situacao IN ('Ativo','Inativo','Transferido')) NOT NULL DEFAULT 'Ativo'
    );

    CREATE TABLE IF NOT EXISTS turma (
        idturma              SERIAL PRIMARY KEY,
        nometurma            VARCHAR(30) NOT NULL,
        serie                VARCHAR(45),
        turno                VARCHAR(50) CHECK (turno IN ('Manha','Tarde','Noite','Integral')) NOT NULL,
        capacidade           INT,
        escola_idescola      INT NOT NULL,
        anoletivo            SMALLINT NOT NULL,
        CONSTRAINT fk_turma_escola FOREIGN KEY (escola_idescola) REFERENCES escola(idescola)
    );

    CREATE TABLE IF NOT EXISTS professor (
        idprofessor     SERIAL PRIMARY KEY,
        nomeprof        VARCHAR(100) NOT NULL,
        cpfprof         VARCHAR(11),
        telefoneprof    VARCHAR(13),
        emailprof       VARCHAR(100),
        cepprof         VARCHAR(8),
        enderecoprof    VARCHAR(200),
        situacao        VARCHAR(50) CHECK (situacao IN ('Ativo','Inativo')) NOT NULL DEFAULT 'Ativo',
        escola_idescola INT NOT NULL,
        CONSTRAINT fk_professor_escola FOREIGN KEY (escola_idescola) REFERENCES escola(idescola)
    );

    CREATE TABLE IF NOT EXISTS alunoresponsavel (
        aluno_idaluno             INT NOT NULL,
        responsavel_idresponsavel INT NOT NULL,
        tiporesponsavel           VARCHAR(50) CHECK (tiporesponsavel IN ('Pai','Mae','ResponsavelLegal','Outro')) NOT NULL,
        responsavelfinanceiro     BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (aluno_idaluno, responsavel_idresponsavel),
        CONSTRAINT fk_ar_aluno FOREIGN KEY (aluno_idaluno) REFERENCES aluno(idaluno),
        CONSTRAINT fk_ar_responsavel FOREIGN KEY (responsavel_idresponsavel) REFERENCES responsavel(idresponsavel)
    );

    CREATE TABLE IF NOT EXISTS matricula (
        idmatricula     SERIAL PRIMARY KEY,
        aluno_idaluno   INT NOT NULL,
        turma_idturma   INT NOT NULL,
        datamatricula   DATE NOT NULL,
        situacao        VARCHAR(50) CHECK (situacao IN ('Ativa','Cancelada','Transferida','Concluida')) NOT NULL DEFAULT 'Ativa',
        CONSTRAINT fk_matricula_aluno FOREIGN KEY (aluno_idaluno) REFERENCES aluno(idaluno),
        CONSTRAINT fk_matricula_turma FOREIGN KEY (turma_idturma) REFERENCES turma(idturma)
    );

    CREATE TABLE IF NOT EXISTS grade_curricular (
        idgrade               SERIAL PRIMARY KEY,
        turma_idturma         INT NOT NULL,
        materia_idmateria     INT NOT NULL,
        professor_idprofessor INT NOT NULL,
        CONSTRAINT fk_grade_turma FOREIGN KEY (turma_idturma) REFERENCES turma(idturma),
        CONSTRAINT fk_grade_materia FOREIGN KEY (materia_idmateria) REFERENCES materia(idmateria),
        CONSTRAINT fk_grade_professor FOREIGN KEY (professor_idprofessor) REFERENCES professor(idprofessor),
        CONSTRAINT uq_turma_materia UNIQUE (turma_idturma, materia_idmateria)
    );

    CREATE TABLE IF NOT EXISTS avaliacao (
        idavaliacao       SERIAL PRIMARY KEY,
        grade_idgrade     INT NOT NULL,
        periodo_idperiodo INT NOT NULL,
        tipo              VARCHAR(50) CHECK (tipo IN ('Prova','Trabalho','Projeto','Recuperacao')) NOT NULL,
        nomeavaliacao     VARCHAR(100) NOT NULL,
        dataavaliacao     DATE NOT NULL,
        peso              DECIMAL(4,2) NOT NULL DEFAULT 1.00,
        CONSTRAINT fk_avaliacao_grade FOREIGN KEY (grade_idgrade) REFERENCES grade_curricular(idgrade),
        CONSTRAINT fk_avaliacao_periodo FOREIGN KEY (periodo_idperiodo) REFERENCES periodo(idperiodo)
    );

    CREATE TABLE IF NOT EXISTS nota (
        idnota                SERIAL PRIMARY KEY,
        avaliacao_idavaliacao INT NOT NULL,
        aluno_idaluno         INT NOT NULL,
        valornota             DECIMAL(4,2) NOT NULL,
        CONSTRAINT fk_nota_avaliacao FOREIGN KEY (avaliacao_idavaliacao) REFERENCES avaliacao(idavaliacao),
        CONSTRAINT fk_nota_aluno FOREIGN KEY (aluno_idaluno) REFERENCES aluno(idaluno),
        CONSTRAINT uq_nota_avaliacao_aluno UNIQUE (avaliacao_idavaliacao, aluno_idaluno)
    );

    CREATE TABLE IF NOT EXISTS frequencia (
        idfrequencia    SERIAL PRIMARY KEY,
        grade_idgrade   INT NOT NULL,
        aluno_idaluno   INT NOT NULL,
        datafrequencia  DATE NOT NULL,
        situacao        VARCHAR(50) CHECK (situacao IN ('Presente','Falta','FaltaJustificada')) NOT NULL,
        CONSTRAINT fk_frequencia_grade FOREIGN KEY (grade_idgrade) REFERENCES grade_curricular(idgrade),
        CONSTRAINT fk_frequencia_aluno FOREIGN KEY (aluno_idaluno) REFERENCES aluno(idaluno),
        CONSTRAINT uq_freq_aluno_grade_data UNIQUE (grade_idgrade, aluno_idaluno, datafrequencia)
    );

    CREATE TABLE IF NOT EXISTS boletim (
        idboletim         SERIAL PRIMARY KEY,
        aluno_idaluno     INT NOT NULL,
        periodo_idperiodo INT NOT NULL,
        materia_idmateria INT NOT NULL,
        mediafinal        DECIMAL(4,2) NOT NULL,
        situacao          VARCHAR(50) CHECK (situacao IN ('Aberto','Fechado')) NOT NULL DEFAULT 'Aberto',
        CONSTRAINT fk_boletim_aluno FOREIGN KEY (aluno_idaluno) REFERENCES aluno(idaluno),
        CONSTRAINT fk_boletim_periodo FOREIGN KEY (periodo_idperiodo) REFERENCES periodo(idperiodo),
        CONSTRAINT fk_boletim_materia FOREIGN KEY (materia_idmateria) REFERENCES materia(idmateria),
        CONSTRAINT uq_boletim_aluno_periodo_materia UNIQUE (aluno_idaluno, periodo_idperiodo, materia_idmateria)
    );

    CREATE TABLE IF NOT EXISTS boleto (
        idboleto         SERIAL PRIMARY KEY,
        numeroboleto     VARCHAR(50) NOT NULL,
        aluno_idaluno    INT NOT NULL,
        competencia      CHAR(7) NOT NULL,
        valormensalidade DECIMAL(10,2) NOT NULL,
        datavencimento   DATE NOT NULL,
        datapagamento    DATE,
        situacao         VARCHAR(50) CHECK (situacao IN ('Pendente','Pago','Atrasado','Cancelado')) NOT NULL DEFAULT 'Pendente',
        CONSTRAINT fk_boleto_aluno FOREIGN KEY (aluno_idaluno) REFERENCES aluno(idaluno)
    );
    """

    views = """
    CREATE OR REPLACE VIEW vw_aluno_escola_atual AS
    SELECT a.idaluno, e.idescola, e.nomeescola
    FROM aluno a
    JOIN matricula m ON m.aluno_idaluno = a.idaluno AND m.situacao = 'Ativa'
    JOIN turma t ON t.idturma = m.turma_idturma
    JOIN escola e ON e.idescola = t.escola_idescola;

    CREATE OR REPLACE VIEW vw_aluno_responsavel_financeiro AS
    SELECT ar.aluno_idaluno, r.idresponsavel, r.nomeresp, r.emailresp, r.telefoneresp
    FROM alunoresponsavel ar
    JOIN responsavel r ON r.idresponsavel = ar.responsavel_idresponsavel
    WHERE ar.responsavelfinanceiro = TRUE;

    CREATE OR REPLACE VIEW vw_aluno_media_dinamica AS
    SELECT
        n.aluno_idaluno,
        a.periodo_idperiodo,
        g.materia_idmateria,
        ROUND(SUM(n.valornota * a.peso) / SUM(a.peso), 2) AS mediacalculada,
        COUNT(n.idnota) AS qtdavaliacoescontabilizadas
    FROM nota n
    JOIN avaliacao a ON a.idavaliacao = n.avaliacao_idavaliacao
    JOIN grade_curricular g ON g.idgrade = a.grade_idgrade
    GROUP BY n.aluno_idaluno, a.periodo_idperiodo, g.materia_idmateria;
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
            """INSERT INTO escola (nomeescola, codigoinep, cnpj, enderecoescola, telefoneescola, emailescola)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING idescola""",
            (nome, codigo_inep, cnpj, endereco, telefone, email),
        )
        novo_id = cur.fetchone()["idescola"]
        cur.execute("""SELECT idescola AS "idEscola", nomeescola AS "NomeEscola", codigoinep AS "CodigoInep",
                cnpj AS "Cnpj", enderecoescola AS "EnderecoEscola", telefoneescola AS "TelefoneEscola",
                emailescola AS "EmailEscola", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM escola WHERE idescola = %s""", (novo_id,))
        return cur.fetchone()


def listar_escolas():
    with cursor() as cur:
        cur.execute("""SELECT idescola AS "idEscola", nomeescola AS "NomeEscola", codigoinep AS "CodigoInep",
                cnpj AS "Cnpj", enderecoescola AS "EnderecoEscola", telefoneescola AS "TelefoneEscola",
                emailescola AS "EmailEscola", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM escola ORDER BY idescola""")
        return cur.fetchall()


def buscar_escola(id_escola):
    with cursor() as cur:
        cur.execute("""SELECT idescola AS "idEscola", nomeescola AS "NomeEscola", codigoinep AS "CodigoInep",
                cnpj AS "Cnpj", enderecoescola AS "EnderecoEscola", telefoneescola AS "TelefoneEscola",
                emailescola AS "EmailEscola", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM escola WHERE idescola = %s""", (id_escola,))
        return cur.fetchone()


def atualizar_escola(id_escola, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE escola SET {set_clause} WHERE idescola = %s", (*campos.values(), id_escola))
        cur.execute("""SELECT idescola AS "idEscola", nomeescola AS "NomeEscola", codigoinep AS "CodigoInep",
                cnpj AS "Cnpj", enderecoescola AS "EnderecoEscola", telefoneescola AS "TelefoneEscola",
                emailescola AS "EmailEscola", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM escola WHERE idescola = %s""", (id_escola,))
        return cur.fetchone()


def excluir_escola(id_escola) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM escola WHERE idescola = %s", (id_escola,))
        return cur.rowcount > 0


# ===========================================================================
# PERIODO
# ===========================================================================

def inserir_periodo(ano, nome_periodo, data_inicio, data_fim, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO periodo (ano, nomeperiodo, datainicio, datafim, situacao)
               VALUES (%s, %s, %s, %s, %s) RETURNING idperiodo""",
            (ano, nome_periodo, data_inicio, data_fim, situacao),
        )
        novo_id = cur.fetchone()["idperiodo"]
        cur.execute("""SELECT idperiodo AS "idPeriodo", ano AS "Ano", nomeperiodo AS "NomePeriodo",
                datainicio AS "DataInicio", datafim AS "DataFim", situacao AS "Situacao",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM periodo WHERE idperiodo = %s""", (novo_id,))
        return cur.fetchone()


def listar_periodos():
    with cursor() as cur:
        cur.execute("""SELECT idperiodo AS "idPeriodo", ano AS "Ano", nomeperiodo AS "NomePeriodo",
                datainicio AS "DataInicio", datafim AS "DataFim", situacao AS "Situacao",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM periodo ORDER BY idperiodo""")
        return cur.fetchall()


def buscar_periodo(id_periodo):
    with cursor() as cur:
        cur.execute("""SELECT idperiodo AS "idPeriodo", ano AS "Ano", nomeperiodo AS "NomePeriodo",
                datainicio AS "DataInicio", datafim AS "DataFim", situacao AS "Situacao",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM periodo WHERE idperiodo = %s""", (id_periodo,))
        return cur.fetchone()


def atualizar_periodo(id_periodo, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE periodo SET {set_clause} WHERE idperiodo = %s", (*campos.values(), id_periodo))
        cur.execute("""SELECT idperiodo AS "idPeriodo", ano AS "Ano", nomeperiodo AS "NomePeriodo",
                datainicio AS "DataInicio", datafim AS "DataFim", situacao AS "Situacao",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM periodo WHERE idperiodo = %s""", (id_periodo,))
        return cur.fetchone()


def excluir_periodo(id_periodo) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM periodo WHERE idperiodo = %s", (id_periodo,))
        return cur.rowcount > 0


# ===========================================================================
# MATERIA
# ===========================================================================

def inserir_materia(nome, carga_horaria):
    with cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO materia (nomemateria, cargahoraria) VALUES (%s, %s) RETURNING idmateria", 
            (nome, carga_horaria)
        )
        novo_id = cur.fetchone()["idmateria"]
        cur.execute("""SELECT idmateria AS "idMateria", nomemateria AS "NomeMateria", cargahoraria AS "CargaHoraria"
                FROM materia WHERE idmateria = %s""", (novo_id,))
        return cur.fetchone()


def listar_materias():
    with cursor() as cur:
        cur.execute("""SELECT idmateria AS "idMateria", nomemateria AS "NomeMateria", cargahoraria AS "CargaHoraria"
                FROM materia ORDER BY idmateria""")
        return cur.fetchall()


def buscar_materia(id_materia):
    with cursor() as cur:
        cur.execute("""SELECT idmateria AS "idMateria", nomemateria AS "NomeMateria", cargahoraria AS "CargaHoraria"
                FROM materia WHERE idmateria = %s""", (id_materia,))
        return cur.fetchone()


def atualizar_materia(id_materia, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE materia SET {set_clause} WHERE idmateria = %s", (*campos.values(), id_materia))
        cur.execute("""SELECT idmateria AS "idMateria", nomemateria AS "NomeMateria", cargahoraria AS "CargaHoraria"
                FROM materia WHERE idmateria = %s""", (id_materia,))
        return cur.fetchone()


def excluir_materia(id_materia) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM materia WHERE idmateria = %s", (id_materia,))
        return cur.rowcount > 0


# ===========================================================================
# RESPONSAVEL
# ===========================================================================

def inserir_responsavel(nome, cpf, telefone, email, cep, endereco):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO responsavel (nomeresp, cpfresp, telefoneresp, emailresp, cepresp, enderecoresp)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING idresponsavel""",
            (nome, cpf, telefone, email, cep, endereco),
        )
        novo_id = cur.fetchone()["idresponsavel"]
        cur.execute("""SELECT idresponsavel AS "idResponsavel", nomeresp AS "NomeResp", cpfresp AS "CpfResp",
                telefoneresp AS "TelefoneResp", emailresp AS "EmailResp", cepresp AS "CepResp",
                enderecoresp AS "EnderecoResp", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM responsavel WHERE idresponsavel = %s""", (novo_id,))
        return cur.fetchone()


def listar_responsaveis():
    with cursor() as cur:
        cur.execute("""SELECT idresponsavel AS "idResponsavel", nomeresp AS "NomeResp", cpfresp AS "CpfResp",
                telefoneresp AS "TelefoneResp", emailresp AS "EmailResp", cepresp AS "CepResp",
                enderecoresp AS "EnderecoResp", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM responsavel ORDER BY idresponsavel""")
        return cur.fetchall()


def buscar_responsavel(id_responsavel):
    with cursor() as cur:
        cur.execute("""SELECT idresponsavel AS "idResponsavel", nomeresp AS "NomeResp", cpfresp AS "CpfResp",
                telefoneresp AS "TelefoneResp", emailresp AS "EmailResp", cepresp AS "CepResp",
                enderecoresp AS "EnderecoResp", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM responsavel WHERE idresponsavel = %s""", (id_responsavel,))
        return cur.fetchone()


def atualizar_responsavel(id_responsavel, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE responsavel SET {set_clause} WHERE idresponsavel = %s",
            (*campos.values(), id_responsavel),
        )
        cur.execute("""SELECT idresponsavel AS "idResponsavel", nomeresp AS "NomeResp", cpfresp AS "CpfResp",
                telefoneresp AS "TelefoneResp", emailresp AS "EmailResp", cepresp AS "CepResp",
                enderecoresp AS "EnderecoResp", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM responsavel WHERE idresponsavel = %s""", (id_responsavel,))
        return cur.fetchone()


def excluir_responsavel(id_responsavel) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM responsavel WHERE idresponsavel = %s", (id_responsavel,))
        return cur.rowcount > 0


# ===========================================================================
# ALUNO
# ===========================================================================

def inserir_aluno(numero_matricula, nome, data_nascimento, cpf, telefone, email, cep, endereco, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO aluno (numeromatricula, nomealuno, datanascimento, cpfaluno,
                                   telefonealuno, emailaluno, cepaluno, enderecoaluno, situacao)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING idaluno""",
            (numero_matricula, nome, data_nascimento, cpf, telefone, email, cep, endereco, situacao),
        )
        novo_id = cur.fetchone()["idaluno"]
        cur.execute("""SELECT idaluno AS "idAluno", numeromatricula AS "NumeroMatricula", nomealuno AS "NomeAluno",
                datanascimento AS "DataNascimento", cpfaluno AS "CpfAluno", telefonealuno AS "TelefoneAluno",
                emailaluno AS "EmailAluno", cepaluno AS "CepAluno", enderecoaluno AS "EnderecoAluno",
                situacao AS "Situacao", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM aluno WHERE idaluno = %s""", (novo_id,))
        return cur.fetchone()

def listar_alunos(situacao: str | None = None, nome: str | None = None):
    query = """SELECT idaluno AS "idAluno", numeromatricula AS "NumeroMatricula", nomealuno AS "NomeAluno",
                datanascimento AS "DataNascimento", cpfaluno AS "CpfAluno", telefonealuno AS "TelefoneAluno",
                emailaluno AS "EmailAluno", cepaluno AS "CepAluno", enderecoaluno AS "EnderecoAluno",
                situacao AS "Situacao", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM aluno WHERE 1=1"""
    params = []
    if situacao:
        query += " AND situacao = %s"
        params.append(situacao)
    if nome:
        query += " AND nomealuno LIKE %s"
        params.append(f"%{nome}%")
    query += " ORDER BY idaluno"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT idaluno AS "idAluno", numeromatricula AS "NumeroMatricula", nomealuno AS "NomeAluno",
                datanascimento AS "DataNascimento", cpfaluno AS "CpfAluno", telefonealuno AS "TelefoneAluno",
                emailaluno AS "EmailAluno", cepaluno AS "CepAluno", enderecoaluno AS "EnderecoAluno",
                situacao AS "Situacao", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM aluno WHERE idaluno = %s""", (id_aluno,))
        return cur.fetchone()


def atualizar_aluno(id_aluno, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE aluno SET {set_clause} WHERE idaluno = %s", (*campos.values(), id_aluno))
        cur.execute("""SELECT idaluno AS "idAluno", numeromatricula AS "NumeroMatricula", nomealuno AS "NomeAluno",
                datanascimento AS "DataNascimento", cpfaluno AS "CpfAluno", telefonealuno AS "TelefoneAluno",
                emailaluno AS "EmailAluno", cepaluno AS "CepAluno", enderecoaluno AS "EnderecoAluno",
                situacao AS "Situacao", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM aluno WHERE idaluno = %s""", (id_aluno,))
        return cur.fetchone()


def excluir_aluno(id_aluno) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM aluno WHERE idaluno = %s", (id_aluno,))
        return cur.rowcount > 0


# Views ligadas ao aluno --------------------------------------------------

def escola_atual_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT idaluno AS "idAluno", idescola AS "idEscola", nomeescola AS "NomeEscola"
                FROM vw_aluno_escola_atual WHERE idaluno = %s""", (id_aluno,))
        return cur.fetchone()


def responsaveis_financeiros_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT aluno_idaluno AS "Aluno_idAluno", idresponsavel AS "idResponsavel", nomeresp AS "NomeResp",
                emailresp AS "EmailResp", telefoneresp AS "TelefoneResp"
                FROM vw_aluno_responsavel_financeiro WHERE aluno_idaluno = %s""", (id_aluno,))
        return cur.fetchall()


def medias_dinamicas_do_aluno(id_aluno):
    with cursor() as cur:
        cur.execute("""SELECT aluno_idaluno AS "Aluno_idAluno", periodo_idperiodo AS "Periodo_idPeriodo", materia_idmateria AS "Materia_idMateria",
                mediacalculada AS "MediaCalculada", qtdavaliacoescontabilizadas AS "QtdAvaliacoesContabilizadas"
                FROM vw_aluno_media_dinamica WHERE aluno_idaluno = %s""", (id_aluno,))
        return cur.fetchall()


# ===========================================================================
# TURMA
# ===========================================================================

def inserir_turma(nome, serie, turno, capacidade, escola_id, ano_letivo):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO turma (nometurma, serie, turno, capacidade, escola_idescola, anoletivo)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING idturma""",
            (nome, serie, turno, capacidade, escola_id, ano_letivo),
        )
        novo_id = cur.fetchone()["idturma"]
        cur.execute("""SELECT idturma AS "idTurma", nometurma AS "NomeTurma", serie AS "Serie",
                turno AS "Turno", capacidade AS "Capacidade", escola_idescola AS "Escola_idEscola",
                anoletivo AS "AnoLetivo", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM turma WHERE idturma = %s""", (novo_id,))
        return cur.fetchone()


def listar_turmas(escola_id: int | None = None):
    query = """SELECT idturma AS "idTurma", nometurma AS "NomeTurma", serie AS "Serie",
                turno AS "Turno", capacidade AS "Capacidade", escola_idescola AS "Escola_idEscola",
                anoletivo AS "AnoLetivo", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM turma WHERE 1=1"""
    params = []
    if escola_id:
        query += " AND escola_idescola = %s"
        params.append(escola_id)
    query += " ORDER BY idturma"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_turma(id_turma):
    with cursor() as cur:
        cur.execute("""SELECT idturma AS "idTurma", nometurma AS "NomeTurma", serie AS "Serie",
                turno AS "Turno", capacidade AS "Capacidade", escola_idescola AS "Escola_idEscola",
                anoletivo AS "AnoLetivo", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM turma WHERE idturma = %s""", (id_turma,))
        return cur.fetchone()


def atualizar_turma(id_turma, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE turma SET {set_clause} WHERE idturma = %s", (*campos.values(), id_turma))
        cur.execute("""SELECT idturma AS "idTurma", nometurma AS "NomeTurma", serie AS "Serie",
                turno AS "Turno", capacidade AS "Capacidade", escola_idescola AS "Escola_idEscola",
                anoletivo AS "AnoLetivo", criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM turma WHERE idturma = %s""", (id_turma,))
        return cur.fetchone()


def excluir_turma(id_turma) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM turma WHERE idturma = %s", (id_turma,))
        return cur.rowcount > 0


# ===========================================================================
# PROFESSOR
# ===========================================================================

def inserir_professor(nome, cpf, telefone, email, cep, endereco, situacao, escola_id):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO professor (nomeprof, cpfprof, telefoneprof, emailprof, cepprof,
                                       enderecoprof, situacao, escola_idescola)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING idprofessor""",
            (nome, cpf, telefone, email, cep, endereco, situacao, escola_id),
        )
        novo_id = cur.fetchone()["idprofessor"]
        cur.execute("""SELECT idprofessor AS "idProfessor", nomeprof AS "NomeProf", cpfprof AS "CpfProf",
                telefoneprof AS "TelefoneProf", emailprof AS "EmailProf", cepprof AS "CepProf",
                enderecoprof AS "EnderecoProf", situacao AS "Situacao", escola_idescola AS "Escola_idEscola",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM professor WHERE idprofessor = %s""", (novo_id,))
        return cur.fetchone()


def listar_professores(escola_id: int | None = None):
    query = """SELECT idprofessor AS "idProfessor", nomeprof AS "NomeProf", cpfprof AS "CpfProf",
                telefoneprof AS "TelefoneProf", emailprof AS "EmailProf", cepprof AS "CepProf",
                enderecoprof AS "EnderecoProf", situacao AS "Situacao", escola_idescola AS "Escola_idEscola",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM professor WHERE 1=1"""
    params = []
    if escola_id:
        query += " AND escola_idescola = %s"
        params.append(escola_id)
    query += " ORDER BY idprofessor"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_professor(id_professor):
    with cursor() as cur:
        cur.execute("""SELECT idprofessor AS "idProfessor", nomeprof AS "NomeProf", cpfprof AS "CpfProf",
                telefoneprof AS "TelefoneProf", emailprof AS "EmailProf", cepprof AS "CepProf",
                enderecoprof AS "EnderecoProf", situacao AS "Situacao", escola_idescola AS "Escola_idEscola",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM professor WHERE idprofessor = %s""", (id_professor,))
        return cur.fetchone()


def atualizar_professor(id_professor, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE professor SET {set_clause} WHERE idprofessor = %s", (*campos.values(), id_professor))
        cur.execute("""SELECT idprofessor AS "idProfessor", nomeprof AS "NomeProf", cpfprof AS "CpfProf",
                telefoneprof AS "TelefoneProf", emailprof AS "EmailProf", cepprof AS "CepProf",
                enderecoprof AS "EnderecoProf", situacao AS "Situacao", escola_idescola AS "Escola_idEscola",
                criadoem AS "CriadoEm", atualizadoem AS "AtualizadoEm"
                FROM professor WHERE idprofessor = %s""", (id_professor,))
        return cur.fetchone()


def excluir_professor(id_professor) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM professor WHERE idprofessor = %s", (id_professor,))
        return cur.rowcount > 0


# ===========================================================================
# MATRICULA (aluno <-> turma)
# ===========================================================================

def inserir_matricula(aluno_id, turma_id, data_matricula, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO matricula (aluno_idaluno, turma_idturma, datamatricula, situacao)
               VALUES (%s, %s, %s, %s) RETURNING idmatricula""",
            (aluno_id, turma_id, data_matricula, situacao),
        )
        novo_id = cur.fetchone()["idmatricula"]
        cur.execute("""SELECT idmatricula AS "idMatricula", aluno_idaluno AS "Aluno_idAluno", turma_idturma AS "Turma_idTurma",
                datamatricula AS "DataMatricula", situacao AS "Situacao", criadoem AS "CriadoEm",
                atualizadoem AS "AtualizadoEm"
                FROM matricula WHERE idmatricula = %s""", (novo_id,))
        return cur.fetchone()


def listar_matriculas(aluno_id: int | None = None, turma_id: int | None = None):
    query = """SELECT idmatricula AS "idMatricula", aluno_idaluno AS "Aluno_idAluno", turma_idturma AS "Turma_idTurma",
                datamatricula AS "DataMatricula", situacao AS "Situacao", criadoem AS "CriadoEm",
                atualizadoem AS "AtualizadoEm"
                FROM matricula WHERE 1=1"""
    params = []
    if aluno_id:
        query += " AND aluno_idaluno = %s"
        params.append(aluno_id)
    if turma_id:
        query += " AND turma_idturma = %s"
        params.append(turma_id)
    query += " ORDER BY idmatricula"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_matricula(id_matricula):
    with cursor() as cur:
        cur.execute("""SELECT idmatricula AS "idMatricula", aluno_idaluno AS "Aluno_idAluno", turma_idturma AS "Turma_idTurma",
                datamatricula AS "DataMatricula", situacao AS "Situacao", criadoem AS "CriadoEm",
                atualizadoem AS "AtualizadoEm"
                FROM matricula WHERE idmatricula = %s""", (id_matricula,))
        return cur.fetchone()


def atualizar_matricula(id_matricula, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE matricula SET {set_clause} WHERE idmatricula = %s", (*campos.values(), id_matricula))
        cur.execute("""SELECT idmatricula AS "idMatricula", aluno_idaluno AS "Aluno_idAluno", turma_idturma AS "Turma_idTurma",
                datamatricula AS "DataMatricula", situacao AS "Situacao", criadoem AS "CriadoEm",
                atualizadoem AS "AtualizadoEm"
                FROM matricula WHERE idmatricula = %s""", (id_matricula,))
        return cur.fetchone()


def excluir_matricula(id_matricula) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM matricula WHERE idmatricula = %s", (id_matricula,))
        return cur.rowcount > 0


# ===========================================================================
# ALUNORESPONSAVEL (junção aluno <-> responsavel, PK composta)
# ===========================================================================

def vincular_responsavel(aluno_id, responsavel_id, tipo, financeiro):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO alunoresponsavel (aluno_idaluno, responsavel_idresponsavel, tiporesponsavel, responsavelfinanceiro)
               VALUES (%s, %s, %s, %s)""",
            (aluno_id, responsavel_id, tipo, financeiro),
        )
        cur.execute(
            """SELECT aluno_idaluno AS "Aluno_idAluno", responsavel_idresponsavel AS "Responsavel_idResponsavel", tiporesponsavel AS "TipoResponsavel",
                responsavelfinanceiro AS "ResponsavelFinanceiro"
                FROM alunoresponsavel WHERE aluno_idaluno = %s AND responsavel_idresponsavel = %s""",
            (aluno_id, responsavel_id),
        )
        return cur.fetchone()


def listar_responsaveis_do_aluno(aluno_id):
    with cursor() as cur:
        cur.execute(
            """SELECT ar.aluno_idaluno AS "Aluno_idAluno",
                      ar.responsavel_idresponsavel AS "Responsavel_idResponsavel",
                      ar.tiporesponsavel AS "TipoResponsavel",
                      ar.responsavelfinanceiro AS "ResponsavelFinanceiro",
                      r.nomeresp AS "NomeResp", r.emailresp AS "EmailResp", r.telefoneresp AS "TelefoneResp"
               FROM alunoresponsavel ar
               JOIN responsavel r ON r.idresponsavel = ar.responsavel_idresponsavel
               WHERE ar.aluno_idaluno = %s""",
            (aluno_id,),
        )
        return cur.fetchall()


def buscar_vinculo(aluno_id, responsavel_id):
    with cursor() as cur:
        cur.execute(
            """SELECT aluno_idaluno AS "Aluno_idAluno", responsavel_idresponsavel AS "Responsavel_idResponsavel", tiporesponsavel AS "TipoResponsavel",
                responsavelfinanceiro AS "ResponsavelFinanceiro"
                FROM alunoresponsavel WHERE aluno_idaluno = %s AND responsavel_idresponsavel = %s""",
            (aluno_id, responsavel_id),
        )
        return cur.fetchone()


def desvincular_responsavel(aluno_id, responsavel_id) -> bool:
    with cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM alunoresponsavel WHERE aluno_idaluno = %s AND responsavel_idresponsavel = %s",
            (aluno_id, responsavel_id),
        )
        return cur.rowcount > 0


# ===========================================================================
# GRADE CURRICULAR (turma <-> materia <-> professor)
# ===========================================================================

def inserir_grade(turma_id, materia_id, professor_id):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO grade_curricular (turma_idturma, materia_idmateria, professor_idprofessor)
               VALUES (%s, %s, %s) RETURNING idgrade""",
            (turma_id, materia_id, professor_id),
        )
        novo_id = cur.fetchone()["idgrade"]
        cur.execute("""SELECT idgrade AS "idGrade", turma_idturma AS "Turma_idTurma", materia_idmateria AS "Materia_idMateria",
                professor_idprofessor AS "Professor_idProfessor"
                FROM grade_curricular WHERE idgrade = %s""", (novo_id,))
        return cur.fetchone()


def listar_grades(turma_id: int | None = None):
    query = """SELECT idgrade AS "idGrade", turma_idturma AS "Turma_idTurma", materia_idmateria AS "Materia_idMateria",
                professor_idprofessor AS "Professor_idProfessor"
                FROM grade_curricular WHERE 1=1"""
    params = []
    if turma_id:
        query += " AND turma_idturma = %s"
        params.append(turma_id)
    query += " ORDER BY idgrade"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_grade(id_grade):
    with cursor() as cur:
        cur.execute("""SELECT idgrade AS "idGrade", turma_idturma AS "Turma_idTurma", materia_idmateria AS "Materia_idMateria",
                professor_idprofessor AS "Professor_idProfessor"
                FROM grade_curricular WHERE idgrade = %s""", (id_grade,))
        return cur.fetchone()


def excluir_grade(id_grade) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM grade_curricular WHERE idgrade = %s", (id_grade,))
        return cur.rowcount > 0


# ===========================================================================
# AVALIACAO
# ===========================================================================

def inserir_avaliacao(grade_id, periodo_id, tipo, nome, data_avaliacao, peso):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO avaliacao (grade_idgrade, periodo_idperiodo, tipo, nomeavaliacao, dataavaliacao, peso)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING idavaliacao""",
            (grade_id, periodo_id, tipo, nome, data_avaliacao, peso),
        )
        novo_id = cur.fetchone()["idavaliacao"]
        cur.execute("""SELECT idavaliacao AS "idAvaliacao", grade_idgrade AS "Grade_idGrade", periodo_idperiodo AS "Periodo_idPeriodo",
                tipo AS "Tipo", nomeavaliacao AS "NomeAvaliacao", dataavaliacao AS "DataAvaliacao",
                peso AS "Peso"
                FROM avaliacao WHERE idavaliacao = %s""", (novo_id,))
        return cur.fetchone()


def listar_avaliacoes(grade_id: int | None = None, periodo_id: int | None = None):
    query = """SELECT idavaliacao AS "idAvaliacao", grade_idgrade AS "Grade_idGrade", periodo_idperiodo AS "Periodo_idPeriodo",
                tipo AS "Tipo", nomeavaliacao AS "NomeAvaliacao", dataavaliacao AS "DataAvaliacao",
                peso AS "Peso"
                FROM avaliacao WHERE 1=1"""
    params = []
    if grade_id:
        query += " AND grade_idgrade = %s"
        params.append(grade_id)
    if periodo_id:
        query += " AND periodo_idperiodo = %s"
        params.append(periodo_id)
    query += " ORDER BY idavaliacao"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_avaliacao(id_avaliacao):
    with cursor() as cur:
        cur.execute("""SELECT idavaliacao AS "idAvaliacao", grade_idgrade AS "Grade_idGrade", periodo_idperiodo AS "Periodo_idPeriodo",
                tipo AS "Tipo", nomeavaliacao AS "NomeAvaliacao", dataavaliacao AS "DataAvaliacao",
                peso AS "Peso"
                FROM avaliacao WHERE idavaliacao = %s""", (id_avaliacao,))
        return cur.fetchone()


def atualizar_avaliacao(id_avaliacao, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE avaliacao SET {set_clause} WHERE idavaliacao = %s", (*campos.values(), id_avaliacao))
        cur.execute("""SELECT idavaliacao AS "idAvaliacao", grade_idgrade AS "Grade_idGrade", periodo_idperiodo AS "Periodo_idPeriodo",
                tipo AS "Tipo", nomeavaliacao AS "NomeAvaliacao", dataavaliacao AS "DataAvaliacao",
                peso AS "Peso"
                FROM avaliacao WHERE idavaliacao = %s""", (id_avaliacao,))
        return cur.fetchone()


def excluir_avaliacao(id_avaliacao) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM avaliacao WHERE idavaliacao = %s", (id_avaliacao,))
        return cur.rowcount > 0


# ===========================================================================
# NOTA
# ===========================================================================

def inserir_nota(avaliacao_id, aluno_id, valor):
    with cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO nota (avaliacao_idavaliacao, aluno_idaluno, valornota) VALUES (%s, %s, %s) RETURNING idnota",
            (avaliacao_id, aluno_id, valor),
        )
        novo_id = cur.fetchone()["idnota"]
        cur.execute("""SELECT idnota AS "idNota", avaliacao_idavaliacao AS "Avaliacao_idAvaliacao", aluno_idaluno AS "Aluno_idAluno",
                valornota AS "ValorNota"
                FROM nota WHERE idnota = %s""", (novo_id,))
        return cur.fetchone()

def listar_notas(avaliacao_id: int | None = None, aluno_id: int | None = None):
    query = """SELECT idnota AS "idNota", avaliacao_idavaliacao AS "Avaliacao_idAvaliacao", aluno_idaluno AS "Aluno_idAluno",
                valornota AS "ValorNota"
                FROM nota WHERE 1=1"""
    params = []
    if avaliacao_id:
        query += " AND avaliacao_idavaliacao = %s"
        params.append(avaliacao_id)
    if aluno_id:
        query += " AND aluno_idaluno = %s"
        params.append(aluno_id)
    query += " ORDER BY idnota"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_nota(id_nota):
    with cursor() as cur:
        cur.execute("""SELECT idnota AS "idNota", avaliacao_idavaliacao AS "Avaliacao_idAvaliacao", aluno_idaluno AS "Aluno_idAluno",
                valornota AS "ValorNota"
                FROM nota WHERE idnota = %s""", (id_nota,))
        return cur.fetchone()


def atualizar_nota(id_nota, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE nota SET {set_clause} WHERE idnota = %s", (*campos.values(), id_nota))
        cur.execute("""SELECT idnota AS "idNota", avaliacao_idavaliacao AS "Avaliacao_idAvaliacao", aluno_idaluno AS "Aluno_idAluno",
                valornota AS "ValorNota"
                FROM nota WHERE idnota = %s""", (id_nota,))
        return cur.fetchone()


def excluir_nota(id_nota) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM nota WHERE idnota = %s", (id_nota,))
        return cur.rowcount > 0


# ===========================================================================
# FREQUENCIA
# ===========================================================================

def inserir_frequencia(grade_id, aluno_id, data_frequencia, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO frequencia (grade_idgrade, aluno_idaluno, datafrequencia, situacao)
               VALUES (%s, %s, %s, %s) RETURNING idfrequencia""",
            (grade_id, aluno_id, data_frequencia, situacao),
        )
        novo_id = cur.fetchone()["idfrequencia"]
        cur.execute("""SELECT idfrequencia AS "idFrequencia", grade_idgrade AS "Grade_idGrade", aluno_idaluno AS "Aluno_idAluno",
                datafrequencia AS "DataFrequencia", situacao AS "Situacao"
                FROM frequencia WHERE idfrequencia = %s""", (novo_id,))
        return cur.fetchone()


def listar_frequencias(grade_id: int | None = None, aluno_id: int | None = None):
    query = """SELECT idfrequencia AS "idFrequencia", grade_idgrade AS "Grade_idGrade", aluno_idaluno AS "Aluno_idAluno",
                datafrequencia AS "DataFrequencia", situacao AS "Situacao"
                FROM frequencia WHERE 1=1"""
    params = []
    if grade_id:
        query += " AND grade_idgrade = %s"
        params.append(grade_id)
    if aluno_id:
        query += " AND aluno_idaluno = %s"
        params.append(aluno_id)
    query += " ORDER BY idfrequencia"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_frequencia(id_frequencia):
    with cursor() as cur:
        cur.execute("""SELECT idfrequencia AS "idFrequencia", grade_idgrade AS "Grade_idGrade", aluno_idaluno AS "Aluno_idAluno",
                datafrequencia AS "DataFrequencia", situacao AS "Situacao"
                FROM frequencia WHERE idfrequencia = %s""", (id_frequencia,))
        return cur.fetchone()


def atualizar_frequencia(id_frequencia, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE frequencia SET {set_clause} WHERE idfrequencia = %s",
            (*campos.values(), id_frequencia),
        )
        cur.execute("""SELECT idfrequencia AS "idFrequencia", grade_idgrade AS "Grade_idGrade", aluno_idaluno AS "Aluno_idAluno",
                datafrequencia AS "DataFrequencia", situacao AS "Situacao"
                FROM frequencia WHERE idfrequencia = %s""", (id_frequencia,))
        return cur.fetchone()


def excluir_frequencia(id_frequencia) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM frequencia WHERE idfrequencia = %s", (id_frequencia,))
        return cur.rowcount > 0


# ===========================================================================
# BOLETIM
# ===========================================================================

def inserir_boletim(aluno_id, periodo_id, materia_id, media_final, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO boletim (aluno_idaluno, periodo_idperiodo, materia_idmateria, mediafinal, situacao)
               VALUES (%s, %s, %s, %s, %s) RETURNING idboletim""",
            (aluno_id, periodo_id, materia_id, media_final, situacao),
        )
        novo_id = cur.fetchone()["idboletim"]
        cur.execute("""SELECT idboletim AS "idBoletim", aluno_idaluno AS "Aluno_idAluno", periodo_idperiodo AS "Periodo_idPeriodo",
                materia_idmateria AS "Materia_idMateria", mediafinal AS "MediaFinal", situacao AS "Situacao"
                FROM boletim WHERE idboletim = %s""", (novo_id,))
        return cur.fetchone()


def listar_boletins(aluno_id: int | None = None, periodo_id: int | None = None):
    query = """SELECT idboletim AS "idBoletim", aluno_idaluno AS "Aluno_idAluno", periodo_idperiodo AS "Periodo_idPeriodo",
                materia_idmateria AS "Materia_idMateria", mediafinal AS "MediaFinal", situacao AS "Situacao"
                FROM boletim WHERE 1=1"""
    params = []
    if aluno_id:
        query += " AND aluno_idaluno = %s"
        params.append(aluno_id)
    if periodo_id:
        query += " AND periodo_idperiodo = %s"
        params.append(periodo_id)
    query += " ORDER BY idboletim"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_boletim(id_boletim):
    with cursor() as cur:
        cur.execute("""SELECT idboletim AS "idBoletim", aluno_idaluno AS "Aluno_idAluno", periodo_idperiodo AS "Periodo_idPeriodo",
                materia_idmateria AS "Materia_idMateria", mediafinal AS "MediaFinal", situacao AS "Situacao"
                FROM boletim WHERE idboletim = %s""", (id_boletim,))
        return cur.fetchone()


def atualizar_boletim(id_boletim, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boletim SET {set_clause} WHERE idboletim = %s", (*campos.values(), id_boletim))
        cur.execute("""SELECT idboletim AS "idBoletim", aluno_idaluno AS "Aluno_idAluno", periodo_idperiodo AS "Periodo_idPeriodo",
                materia_idmateria AS "Materia_idMateria", mediafinal AS "MediaFinal", situacao AS "Situacao"
                FROM boletim WHERE idboletim = %s""", (id_boletim,))
        return cur.fetchone()


def excluir_boletim(id_boletim) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM boletim WHERE idboletim = %s", (id_boletim,))
        return cur.rowcount > 0


# ===========================================================================
# BOLETO
# ===========================================================================

def inserir_boleto(numero_boleto, aluno_id, competencia, valor, data_vencimento, situacao):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO boleto (numeroboleto, aluno_idaluno, competencia, valormensalidade, datavencimento, situacao)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING idboleto""",
            (numero_boleto, aluno_id, competencia, valor, data_vencimento, situacao),
        )
        novo_id = cur.fetchone()["idboleto"]
        cur.execute("""SELECT idboleto AS "idBoleto", numeroboleto AS "NumeroBoleto", aluno_idaluno AS "Aluno_idAluno",
                competencia AS "Competencia", valormensalidade AS "ValorMensalidade", datavencimento AS "DataVencimento",
                datapagamento AS "DataPagamento", situacao AS "Situacao"
                FROM boleto WHERE idboleto = %s""", (novo_id,))
        return cur.fetchone()


def listar_boletos(aluno_id: int | None = None, situacao: str | None = None):
    query = """SELECT idboleto AS "idBoleto", numeroboleto AS "NumeroBoleto", aluno_idaluno AS "Aluno_idAluno",
                competencia AS "Competencia", valormensalidade AS "ValorMensalidade", datavencimento AS "DataVencimento",
                datapagamento AS "DataPagamento", situacao AS "Situacao"
                FROM boleto WHERE 1=1"""
    params = []
    if aluno_id:
        query += " AND aluno_idaluno = %s"
        params.append(aluno_id)
    if situacao:
        query += " AND situacao = %s"
        params.append(situacao)
    query += " ORDER BY idboleto"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_boleto(id_boleto):
    with cursor() as cur:
        cur.execute("""SELECT idboleto AS "idBoleto", numeroboleto AS "NumeroBoleto", aluno_idaluno AS "Aluno_idAluno",
                competencia AS "Competencia", valormensalidade AS "ValorMensalidade", datavencimento AS "DataVencimento",
                datapagamento AS "DataPagamento", situacao AS "Situacao"
                FROM boleto WHERE idboleto = %s""", (id_boleto,))
        return cur.fetchone()


def atualizar_boleto(id_boleto, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boleto SET {set_clause} WHERE idboleto = %s", (*campos.values(), id_boleto))
        cur.execute("""SELECT idboleto AS "idBoleto", numeroboleto AS "NumeroBoleto", aluno_idaluno AS "Aluno_idAluno",
                competencia AS "Competencia", valormensalidade AS "ValorMensalidade", datavencimento AS "DataVencimento",
                datapagamento AS "DataPagamento", situacao AS "Situacao"
                FROM boleto WHERE idboleto = %s""", (id_boleto,))
        return cur.fetchone()


def excluir_boleto(id_boleto) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM boleto WHERE idboleto = %s", (id_boleto,))
        return cur.rowcount > 0