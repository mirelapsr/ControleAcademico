"""
db.py — CAMADA DE BANCO
=======================
Banco: PostgreSQL (database CAcademic).
Driver: psycopg2, com RealDictCursor (as linhas voltam como dict).

Fonte única do schema: `controle2.sql`. Ele recria as tabelas do zero
(rode no console do DataGrip). No startup, `criar_tabelas` só confere a estrutura: não
altera nada se o schema está completo, cria as tabelas se o banco está
vazio (usando o mesmo DDL do arquivo) e interrompe a API se o banco
estiver desatualizado. Reiniciar a API nunca apaga dados.
"""

import logging
import os
import re
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ARQUIVO_SCHEMA = Path(__file__).resolve().parent / "controle2.sql"
_MARCA_INICIO = "-- >>> SCHEMA:INICIO"
_MARCA_FIM = "-- <<< SCHEMA:FIM"
_COMANDOS_PROIBIDOS = re.compile(r"\b(DROP\s+(TABLE|DATABASE|SCHEMA)|TRUNCATE)\b", re.IGNORECASE)

TABELAS_ESPERADAS = (
    "usuario", "escola", "periodo", "turma", "aluno", "responsavel", "alunoresponsavel",
    "matricula", "professor", "materia", "grade_curricular", "avaliacao", "nota",
    "frequencia", "boletim", "boleto",
)
_COLUNAS_OBRIGATORIAS = (
    tuple((t, c) for t in TABELAS_ESPERADAS for c in ("criado_em", "atualizado_em"))
    + (("grade_curricular", "carga_horaria_semanal"), ("nota", "observacao"))
)

DATABASE_URL = os.getenv("DATABASE_URL")

CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "postgres"),       
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "CAcademic"),
    "port": int(os.getenv("DB_PORT", "5432")),      
}


def conectar():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return psycopg2.connect(
        host=CONFIG["host"],
        user=CONFIG["user"],
        password=CONFIG["password"],
        dbname=CONFIG["database"], 
        port=CONFIG["port"],
        cursor_factory=RealDictCursor 
    )


def conectar_admin():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return psycopg2.connect(
        host=CONFIG["host"],
        user=os.getenv("DB_ADMIN_USER", CONFIG["user"]),
        password=os.getenv("DB_ADMIN_PASSWORD", CONFIG["password"]),
        dbname=CONFIG["database"],
        port=CONFIG["port"],
        cursor_factory=RealDictCursor,
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
# SCHEMA (fonte única: controle2.sql)
# ===========================================================================

def _ddl_do_schema() -> str:
    """Devolve o trecho de controle2.sql entre os marcadores SCHEMA:INICIO
    e SCHEMA:FIM: o mesmo DDL que o DataGrip executa na Parte 2, sem a limpeza da Parte 1."""
    try:
        texto = ARQUIVO_SCHEMA.read_text(encoding="utf-8")
        ddl = texto[texto.index(_MARCA_INICIO) + len(_MARCA_INICIO):texto.index(_MARCA_FIM)]
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Schema indisponível: {ARQUIVO_SCHEMA} ausente ou sem marcadores.") from exc
    if _COMANDOS_PROIBIDOS.search(ddl):
        raise RuntimeError("controle2.sql: trecho do schema contém comando destrutivo.")
    return ddl


def _diagnosticar_estrutura(cur) -> tuple[list[str], list[str]]:
    """Devolve (tabelas ausentes, itens desatualizados) em relação ao schema final."""
    cur.execute(
        """SELECT table_name, column_name FROM information_schema.columns
           WHERE table_schema = current_schema() AND table_name = ANY(%s)""",
        (list(TABELAS_ESPERADAS),),
    )
    existentes = {(l["table_name"], l["column_name"]) for l in cur.fetchall()}
    presentes = {tabela for tabela, _ in existentes}

    ausentes = [t for t in TABELAS_ESPERADAS if t not in presentes]
    desatualizados = [
        f"{t}.{c}" for t, c in _COLUNAS_OBRIGATORIAS if t in presentes and (t, c) not in existentes
    ]
    if "avaliacao" in presentes:
        cur.execute(
            """SELECT pg_get_constraintdef(oid) AS definicao FROM pg_constraint
               WHERE conname = 'chk_avaliacao_tipo' AND conrelid = to_regclass('avaliacao')"""
        )
        linha = cur.fetchone()
        if not linha or "Seminario" not in linha["definicao"]:
            desatualizados.append("avaliacao.chk_avaliacao_tipo")
    return ausentes, desatualizados


def criar_tabelas() -> None:
    """Garante que o schema exista exatamente como em controle2.sql.

    - Schema completo e atualizado: não executa nenhum DDL (funciona também
      com um usuário sem permissão de DDL).
    - Tabelas ausentes (banco vazio): executa o DDL do arquivo.
    - Banco existente porém desatualizado: interrompe o startup com instrução
      para recriar o banco. Nunca altera tabelas existentes.
    """
    conn = conectar_admin()
    try:
        with conn.cursor() as cur:
            ausentes, desatualizados = _diagnosticar_estrutura(cur)
            if ausentes:
                logger.info("Criando schema (tabelas ausentes: %s)", ", ".join(ausentes))
                cur.execute(_ddl_do_schema())
                conn.commit()
                ausentes, desatualizados = _diagnosticar_estrutura(cur)
            if ausentes or desatualizados:
                raise RuntimeError(
                    "Banco desatualizado em relação a controle2.sql "
                    f"(ausentes: {ausentes or '-'}; divergentes: {desatualizados or '-'}). "
                    "Execute controle2.sql inteiro no DataGrip para recriar as tabelas."
                )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ===========================================================================
# USUARIO
# ===========================================================================

def inserir_usuario(nome, email, senha_hash, papel="ADMIN"):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO usuario (nome, email, senha_hash, papel)
               VALUES (%s, %s, %s, %s) RETURNING id_usuario""",
            (nome, email.strip().lower(), senha_hash, papel),
        )
        novo_id = cur.fetchone()["id_usuario"]
        cur.execute(
            """SELECT id_usuario, nome, email, senha_hash, papel, ativo, criado_em, atualizado_em
               FROM usuario WHERE id_usuario = %s""",
            (novo_id,),
        )
        return cur.fetchone()


def buscar_usuario(id_usuario):
    with cursor() as cur:
        cur.execute(
            """SELECT id_usuario, nome, email, senha_hash, papel, ativo, criado_em, atualizado_em
               FROM usuario WHERE id_usuario = %s""",
            (id_usuario,),
        )
        return cur.fetchone()


def buscar_usuario_por_email(email):
    with cursor() as cur:
        cur.execute(
            """SELECT id_usuario, nome, email, senha_hash, papel, ativo, criado_em, atualizado_em
               FROM usuario WHERE email = %s""",
            (email.strip().lower(),),
        )
        return cur.fetchone()


# ===========================================================================
# ESCOLA
# ===========================================================================

def inserir_escola(nome, codigo_inep, cnpj, endereco, telefone, email, rede_ensino=None):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO escola (nome_escola, codigo_inep, cnpj, rede_ensino, endereco_escola, telefone_escola, email_escola)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_escola""",
            (nome, codigo_inep, cnpj, rede_ensino, endereco, telefone, email),
        )
        novo_id = cur.fetchone()["id_escola"]
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, rede_ensino, endereco_escola, telefone_escola,
                email_escola, criado_em, atualizado_em
                FROM escola WHERE id_escola = %s""", (novo_id,))
        return cur.fetchone()


def listar_escolas():
    with cursor() as cur:
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, rede_ensino, endereco_escola, telefone_escola,
                email_escola, criado_em, atualizado_em
                FROM escola ORDER BY id_escola""")
        return cur.fetchall()


def buscar_escola(id_escola):
    with cursor() as cur:
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, rede_ensino, endereco_escola, telefone_escola,
                email_escola, criado_em, atualizado_em
                FROM escola WHERE id_escola = %s""", (id_escola,))
        return cur.fetchone()


def atualizar_escola(id_escola, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE escola SET {set_clause} WHERE id_escola = %s", (*campos.values(), id_escola))
        cur.execute("""SELECT id_escola, nome_escola, codigo_inep,
                cnpj, rede_ensino, endereco_escola, telefone_escola,
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
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria, criado_em, atualizado_em
                FROM materia WHERE id_materia = %s""", (novo_id,))
        return cur.fetchone()


def listar_materias():
    with cursor() as cur:
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria, criado_em, atualizado_em
                FROM materia ORDER BY id_materia""")
        return cur.fetchall()


def buscar_materia(id_materia):
    with cursor() as cur:
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria, criado_em, atualizado_em
                FROM materia WHERE id_materia = %s""", (id_materia,))
        return cur.fetchone()


def atualizar_materia(id_materia, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE materia SET {set_clause} WHERE id_materia = %s", (*campos.values(), id_materia))
        cur.execute("""SELECT id_materia, nome_materia, carga_horaria, criado_em, atualizado_em
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
        query += " AND nome_aluno ILIKE %s"
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
    if escola_id is not None:
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
    if escola_id is not None:
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
    if aluno_id is not None:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    if turma_id is not None:
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
                responsavel_financeiro, criado_em, atualizado_em
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
                      r.nome_resp, r.email_resp, r.telefone_resp,
                      ar.criado_em, ar.atualizado_em
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
                responsavel_financeiro, criado_em, atualizado_em
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

def inserir_grade(turma_id, materia_id, professor_id, carga_horaria_semanal=None):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO grade_curricular
                   (turma_id_turma, materia_id_materia, professor_id_professor, carga_horaria_semanal)
               VALUES (%s, %s, %s, %s) RETURNING id_grade""",
            (turma_id, materia_id, professor_id, carga_horaria_semanal),
        )
        novo_id = cur.fetchone()["id_grade"]
        cur.execute("""SELECT id_grade, turma_id_turma AS turma_id, materia_id_materia AS materia_id,
                professor_id_professor AS professor_id,
                carga_horaria_semanal, criado_em, atualizado_em
                FROM grade_curricular WHERE id_grade = %s""", (novo_id,))
        return cur.fetchone()


def listar_grades(turma_id: int | None = None):
    query = """SELECT id_grade, turma_id_turma AS turma_id, materia_id_materia AS materia_id,
                professor_id_professor AS professor_id,
                carga_horaria_semanal, criado_em, atualizado_em
                FROM grade_curricular WHERE 1=1"""
    params = []
    if turma_id is not None:
        query += " AND turma_id_turma = %s"
        params.append(turma_id)
    query += " ORDER BY id_grade"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_grade(id_grade):
    with cursor() as cur:
        cur.execute("""SELECT id_grade, turma_id_turma AS turma_id, materia_id_materia AS materia_id,
                professor_id_professor AS professor_id,
                carga_horaria_semanal, criado_em, atualizado_em
                FROM grade_curricular WHERE id_grade = %s""", (id_grade,))
        return cur.fetchone()

_COLUNAS_DB_GRADE = {
    "turma_id": "turma_id_turma",
    "materia_id": "materia_id_materia",
    "professor_id": "professor_id_professor",
}


def atualizar_grade(id_grade: int, campos: dict):
    set_clause = ", ".join(f"{_COLUNAS_DB_GRADE.get(c, c.lower())} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE grade_curricular SET {set_clause} WHERE id_grade = %s", (*campos.values(), id_grade))
        cur.execute("""SELECT id_grade, turma_id_turma AS turma_id, materia_id_materia AS materia_id,
                professor_id_professor AS professor_id,
                carga_horaria_semanal, criado_em, atualizado_em
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
                peso, criado_em, atualizado_em
                FROM avaliacao WHERE id_avaliacao = %s""", (novo_id,))
        return cur.fetchone()


def listar_avaliacoes(grade_id: int | None = None, periodo_id: int | None = None):
    query = """SELECT id_avaliacao, grade_id_grade AS grade_id, periodo_id_periodo AS periodo_id,
                tipo, nome_avaliacao, data_avaliacao,
                peso, criado_em, atualizado_em
                FROM avaliacao WHERE 1=1"""
    params = []
    if grade_id is not None:
        query += " AND grade_id_grade = %s"
        params.append(grade_id)
    if periodo_id is not None:
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
                peso, criado_em, atualizado_em
                FROM avaliacao WHERE id_avaliacao = %s""", (id_avaliacao,))
        return cur.fetchone()


_COLUNAS_DB_AVALIACAO = {"grade_id": "grade_id_grade", "periodo_id": "periodo_id_periodo"}


def atualizar_avaliacao(id_avaliacao, campos: dict):
    set_clause = ", ".join(f"{_COLUNAS_DB_AVALIACAO.get(c, c.lower())} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE avaliacao SET {set_clause} WHERE id_avaliacao = %s", (*campos.values(), id_avaliacao))
        cur.execute("""SELECT id_avaliacao, grade_id_grade AS grade_id, periodo_id_periodo AS periodo_id,
                tipo, nome_avaliacao, data_avaliacao,
                peso, criado_em, atualizado_em
                FROM avaliacao WHERE id_avaliacao = %s""", (id_avaliacao,))
        return cur.fetchone()


def excluir_avaliacao(id_avaliacao) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM avaliacao WHERE id_avaliacao = %s", (id_avaliacao,))
        return cur.rowcount > 0


# ===========================================================================
# NOTA
# ===========================================================================

def inserir_nota(avaliacao_id, aluno_id, valor, observacao=None):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO nota (avaliacao_id_avaliacao, aluno_id_aluno, valor_nota, observacao)
               VALUES (%s, %s, %s, %s) RETURNING id_nota""",
            (avaliacao_id, aluno_id, valor, observacao),
        )
        novo_id = cur.fetchone()["id_nota"]
        cur.execute("""SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota, observacao, criado_em, atualizado_em
                FROM nota WHERE id_nota = %s""", (novo_id,))
        return cur.fetchone()

def listar_notas(avaliacao_id: int | None = None, aluno_id: int | None = None):
    query = """SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota, observacao, criado_em, atualizado_em
                FROM nota WHERE 1=1"""
    params = []
    if avaliacao_id is not None:
        query += " AND avaliacao_id_avaliacao = %s"
        params.append(avaliacao_id)
    if aluno_id is not None:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    query += " ORDER BY id_nota"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_nota(id_nota):
    with cursor() as cur:
        cur.execute("""SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota, observacao, criado_em, atualizado_em
                FROM nota WHERE id_nota = %s""", (id_nota,))
        return cur.fetchone()


def atualizar_nota(id_nota, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE nota SET {set_clause} WHERE id_nota = %s", (*campos.values(), id_nota))
        cur.execute("""SELECT id_nota, avaliacao_id_avaliacao AS avaliacao_id, aluno_id_aluno AS aluno_id,
                valor_nota, observacao, criado_em, atualizado_em
                FROM nota WHERE id_nota = %s""", (id_nota,))
        return cur.fetchone()


def excluir_nota(id_nota) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM nota WHERE id_nota = %s", (id_nota,))
        return cur.rowcount > 0


# ===========================================================================
# FREQUENCIA
# ===========================================================================

def inserir_frequencia(grade_id, aluno_id, data_frequencia, situacao, justificativa=None):
    with cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO frequencia (grade_id_grade, aluno_id_aluno, data_frequencia, situacao, justificativa)
               VALUES (%s, %s, %s, %s, %s) RETURNING id_frequencia""",
            (grade_id, aluno_id, data_frequencia, situacao, justificativa),
        )
        novo_id = cur.fetchone()["id_frequencia"]
        cur.execute("""SELECT id_frequencia, grade_id_grade AS grade_id, aluno_id_aluno AS aluno_id,
                data_frequencia, situacao, justificativa, criado_em, atualizado_em
                FROM frequencia WHERE id_frequencia = %s""", (novo_id,))
        return cur.fetchone()


def listar_frequencias(grade_id: int | None = None, aluno_id: int | None = None):
    query = """SELECT id_frequencia, grade_id_grade AS grade_id, aluno_id_aluno AS aluno_id,
                data_frequencia, situacao, justificativa, criado_em, atualizado_em
                FROM frequencia WHERE 1=1"""
    params = []
    if grade_id is not None:
        query += " AND grade_id_grade = %s"
        params.append(grade_id)
    if aluno_id is not None:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    query += " ORDER BY id_frequencia"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_frequencia(id_frequencia):
    with cursor() as cur:
        cur.execute("""SELECT id_frequencia, grade_id_grade AS grade_id, aluno_id_aluno AS aluno_id,
                data_frequencia, situacao, justificativa, criado_em, atualizado_em
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
                data_frequencia, situacao, justificativa, criado_em, atualizado_em
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
                materia_id_materia AS materia_id, media_final, situacao, criado_em, atualizado_em
                FROM boletim WHERE id_boletim = %s""", (novo_id,))
        return cur.fetchone()


def listar_boletins(aluno_id: int | None = None, periodo_id: int | None = None):
    query = """SELECT id_boletim, aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id,
                materia_id_materia AS materia_id, media_final, situacao, criado_em, atualizado_em
                FROM boletim WHERE 1=1"""
    params = []
    if aluno_id is not None:
        query += " AND aluno_id_aluno = %s"
        params.append(aluno_id)
    if periodo_id is not None:
        query += " AND periodo_id_periodo = %s"
        params.append(periodo_id)
    query += " ORDER BY id_boletim"
    with cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def buscar_boletim(id_boletim):
    with cursor() as cur:
        cur.execute("""SELECT id_boletim, aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id,
                materia_id_materia AS materia_id, media_final, situacao, criado_em, atualizado_em
                FROM boletim WHERE id_boletim = %s""", (id_boletim,))
        return cur.fetchone()


def atualizar_boletim(id_boletim, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boletim SET {set_clause} WHERE id_boletim = %s", (*campos.values(), id_boletim))
        cur.execute("""SELECT id_boletim, aluno_id_aluno AS aluno_id, periodo_id_periodo AS periodo_id,
                materia_id_materia AS materia_id, media_final, situacao, criado_em, atualizado_em
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
                data_pagamento, situacao, criado_em, atualizado_em
                FROM boleto WHERE id_boleto = %s""", (novo_id,))
        return cur.fetchone()


def listar_boletos(aluno_id: int | None = None, situacao: str | None = None):
    query = """SELECT id_boleto, numero_boleto, aluno_id_aluno AS aluno_id,
                competencia, valor_mensalidade, data_vencimento,
                data_pagamento, situacao, criado_em, atualizado_em
                FROM boleto WHERE 1=1"""
    params = []
    if aluno_id is not None:
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
                data_pagamento, situacao, criado_em, atualizado_em
                FROM boleto WHERE id_boleto = %s""", (id_boleto,))
        return cur.fetchone()


def atualizar_boleto(id_boleto, campos: dict):
    set_clause = ", ".join(f"{c.lower()} = %s" for c in campos)
    with cursor(commit=True) as cur:
        cur.execute(f"UPDATE boleto SET {set_clause} WHERE id_boleto = %s", (*campos.values(), id_boleto))
        cur.execute("""SELECT id_boleto, numero_boleto, aluno_id_aluno AS aluno_id,
                competencia, valor_mensalidade, data_vencimento,
                data_pagamento, situacao, criado_em, atualizado_em
                FROM boleto WHERE id_boleto = %s""", (id_boleto,))
        return cur.fetchone()


def excluir_boleto(id_boleto) -> bool:
    with cursor(commit=True) as cur:
        cur.execute("DELETE FROM boleto WHERE id_boleto = %s", (id_boleto,))
        return cur.rowcount > 0