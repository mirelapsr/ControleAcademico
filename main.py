"""
main.py — CAMADA DE ROTAS
=========================
"cada rota apenas (1) valida a entrada via Pydantic,
(2) chama UMA função de db.py, (3) traduz o resultado em resposta HTTP.


Tratamento de erros:
  - 404 Not Found   -> ID informado não existe.
  - 409 Conflict     -> violação de UNIQUE (ex.: grade turma+matéria repetida,
                        nota duplicada para a mesma avaliação/aluno, etc.).
  - 400 Bad Request  -> violação de FK (ex.: Escola_idEscola inexistente) ou
                        nenhum campo enviado para atualização.
"""

from typing import List, Optional

import pymysql
from fastapi import FastAPI, HTTPException, Query, status

import db
from schemas import (
    EscolaEntrada, EscolaAtualizacao, EscolaSaida,
    PeriodoEntrada, PeriodoAtualizacao, PeriodoSaida,
    MateriaEntrada, MateriaAtualizacao, MateriaSaida,
    ResponsavelEntrada, ResponsavelAtualizacao, ResponsavelSaida,
    AlunoEntrada, AlunoAtualizacao, AlunoSaida,
    TurmaEntrada, TurmaAtualizacao, TurmaSaida,
    ProfessorEntrada, ProfessorAtualizacao, ProfessorSaida,
    MatriculaEntrada, MatriculaAtualizacao, MatriculaSaida,
    VinculoResponsavelEntrada, VinculoResponsavelSaida,
    GradeCurricularEntrada, GradeCurricularSaida,
    AvaliacaoEntrada, AvaliacaoAtualizacao, AvaliacaoSaida,
    NotaEntrada, NotaAtualizacao, NotaSaida,
    FrequenciaEntrada, FrequenciaAtualizacao, FrequenciaSaida,
    BoletimEntrada, BoletimAtualizacao, BoletimSaida,
    BoletoEntrada, BoletoAtualizacao, BoletoSaida,
)

app = FastAPI(
    title="CAcademic API",
    description="API de gestão acadêmica (escolas, turmas, alunos, professores, matrículas, notas, frequência, financeiro).",
    version="2.0.0",
)


@app.on_event("startup")
def ao_iniciar():
    db.criar_tabelas()


@app.get("/", tags=["Health"])
def raiz():
    return {"status": "ok", "service": "CAcademic API", "docs": "/docs"}


# ---------------------------------------------------------------------------
# Helpers de camada de rota
# ---------------------------------------------------------------------------

def campos_para_update(payload) -> dict:
    """Converte um schema *Atualizacao em dict só com campos enviados
    (exclude_unset), convertendo Enums para seus valores string."""
    campos = payload.model_dump(exclude_unset=True)
    for chave, valor in campos.items():
        if hasattr(valor, "value"):
            campos[chave] = valor.value
    if not campos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum campo informado para atualização.")
    return campos


def tratar_integrity_error(exc: pymysql.err.IntegrityError):
    """Traduz IntegrityError do MySQL em HTTPException.
    1062 = Duplicate entry (UNIQUE) -> 409
    1451/1452 = violação de FK -> 400
    """
    codigo = exc.args[0] if exc.args else None
    mensagem = exc.args[1] if len(exc.args) > 1 else str(exc)
    if codigo == 1062:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Registro duplicado: {mensagem}")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro de integridade referencial: {mensagem}")


# ===========================================================================
# ESCOLA
# ===========================================================================

@app.post("/escolas", response_model=EscolaSaida, status_code=status.HTTP_201_CREATED, tags=["Escola"])
def criar_escola(payload: EscolaEntrada):
    try:
        return db.inserir_escola(
            payload.NomeEscola, payload.CodigoInep, payload.Cnpj,
            payload.EnderecoEscola, payload.TelefoneEscola, payload.EmailEscola,
        )
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/escolas", response_model=List[EscolaSaida], tags=["Escola"])
def listar_escolas():
    return db.listar_escolas()


@app.get("/escolas/{id_escola}", response_model=EscolaSaida, tags=["Escola"])
def obter_escola(id_escola: int):
    escola = db.buscar_escola(id_escola)
    if not escola:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escola não encontrada.")
    return escola


@app.patch("/escolas/{id_escola}", response_model=EscolaSaida, tags=["Escola"])
def atualizar_escola(id_escola: int, payload: EscolaAtualizacao):
    if not db.buscar_escola(id_escola):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escola não encontrada.")
    campos = campos_para_update(payload)
    try:
        return db.atualizar_escola(id_escola, campos)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.delete("/escolas/{id_escola}", status_code=status.HTTP_204_NO_CONTENT, tags=["Escola"])
def deletar_escola(id_escola: int):
    if not db.buscar_escola(id_escola):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escola não encontrada.")
    try:
        db.excluir_escola(id_escola)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# PERIODO
# ===========================================================================

@app.post("/periodos", response_model=PeriodoSaida, status_code=status.HTTP_201_CREATED, tags=["Periodo"])
def criar_periodo(payload: PeriodoEntrada):
    return db.inserir_periodo(payload.Ano, payload.NomePeriodo, payload.DataInicio, payload.DataFim, payload.Situacao.value)


@app.get("/periodos", response_model=List[PeriodoSaida], tags=["Periodo"])
def listar_periodos():
    return db.listar_periodos()


@app.get("/periodos/{id_periodo}", response_model=PeriodoSaida, tags=["Periodo"])
def obter_periodo(id_periodo: int):
    periodo = db.buscar_periodo(id_periodo)
    if not periodo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período não encontrado.")
    return periodo


@app.patch("/periodos/{id_periodo}", response_model=PeriodoSaida, tags=["Periodo"])
def atualizar_periodo(id_periodo: int, payload: PeriodoAtualizacao):
    if not db.buscar_periodo(id_periodo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período não encontrado.")
    return db.atualizar_periodo(id_periodo, campos_para_update(payload))


@app.delete("/periodos/{id_periodo}", status_code=status.HTTP_204_NO_CONTENT, tags=["Periodo"])
def deletar_periodo(id_periodo: int):
    if not db.buscar_periodo(id_periodo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período não encontrado.")
    try:
        db.excluir_periodo(id_periodo)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# MATERIA
# ===========================================================================

@app.post("/materias", response_model=MateriaSaida, status_code=status.HTTP_201_CREATED, tags=["Materia"])
def criar_materia(payload: MateriaEntrada):
    return db.inserir_materia(payload.NomeMateria, payload.CargaHoraria)


@app.get("/materias", response_model=List[MateriaSaida], tags=["Materia"])
def listar_materias():
    return db.listar_materias()


@app.get("/materias/{id_materia}", response_model=MateriaSaida, tags=["Materia"])
def obter_materia(id_materia: int):
    materia = db.buscar_materia(id_materia)
    if not materia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matéria não encontrada.")
    return materia


@app.patch("/materias/{id_materia}", response_model=MateriaSaida, tags=["Materia"])
def atualizar_materia(id_materia: int, payload: MateriaAtualizacao):
    if not db.buscar_materia(id_materia):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matéria não encontrada.")
    return db.atualizar_materia(id_materia, campos_para_update(payload))


@app.delete("/materias/{id_materia}", status_code=status.HTTP_204_NO_CONTENT, tags=["Materia"])
def deletar_materia(id_materia: int):
    if not db.buscar_materia(id_materia):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matéria não encontrada.")
    try:
        db.excluir_materia(id_materia)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# RESPONSAVEL
# ===========================================================================

@app.post("/responsaveis", response_model=ResponsavelSaida, status_code=status.HTTP_201_CREATED, tags=["Responsavel"])
def criar_responsavel(payload: ResponsavelEntrada):
    return db.inserir_responsavel(
        payload.NomeResp, payload.CpfResp, payload.TelefoneResp,
        payload.EmailResp, payload.CepResp, payload.EnderecoResp,
    )


@app.get("/responsaveis", response_model=List[ResponsavelSaida], tags=["Responsavel"])
def listar_responsaveis():
    return db.listar_responsaveis()


@app.get("/responsaveis/{id_responsavel}", response_model=ResponsavelSaida, tags=["Responsavel"])
def obter_responsavel(id_responsavel: int):
    responsavel = db.buscar_responsavel(id_responsavel)
    if not responsavel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsável não encontrado.")
    return responsavel


@app.patch("/responsaveis/{id_responsavel}", response_model=ResponsavelSaida, tags=["Responsavel"])
def atualizar_responsavel(id_responsavel: int, payload: ResponsavelAtualizacao):
    if not db.buscar_responsavel(id_responsavel):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsável não encontrado.")
    return db.atualizar_responsavel(id_responsavel, campos_para_update(payload))


@app.delete("/responsaveis/{id_responsavel}", status_code=status.HTTP_204_NO_CONTENT, tags=["Responsavel"])
def deletar_responsavel(id_responsavel: int):
    if not db.buscar_responsavel(id_responsavel):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsável não encontrado.")
    try:
        db.excluir_responsavel(id_responsavel)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# ALUNO
# ===========================================================================

@app.post("/alunos", response_model=AlunoSaida, status_code=status.HTTP_201_CREATED, tags=["Aluno"])
def criar_aluno(payload: AlunoEntrada):
    return db.inserir_aluno(
        payload.NumeroMatricula, payload.NomeAluno, payload.DataNascimento, payload.CpfAluno,
        payload.TelefoneAluno, payload.EmailAluno, payload.CepAluno, payload.EnderecoAluno,
        payload.Situacao.value,
    )


@app.get("/alunos", response_model=List[AlunoSaida], tags=["Aluno"])
def listar_alunos(situacao: Optional[str] = Query(None), nome: Optional[str] = Query(None)):
    return db.listar_alunos(situacao=situacao, nome=nome)


@app.get("/alunos/{id_aluno}", response_model=AlunoSaida, tags=["Aluno"])
def obter_aluno(id_aluno: int):
    aluno = db.buscar_aluno(id_aluno)
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return aluno


@app.patch("/alunos/{id_aluno}", response_model=AlunoSaida, tags=["Aluno"])
def atualizar_aluno(id_aluno: int, payload: AlunoAtualizacao):
    if not db.buscar_aluno(id_aluno):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return db.atualizar_aluno(id_aluno, campos_para_update(payload))


@app.delete("/alunos/{id_aluno}", status_code=status.HTTP_204_NO_CONTENT, tags=["Aluno"])
def deletar_aluno(id_aluno: int):
    if not db.buscar_aluno(id_aluno):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    try:
        db.excluir_aluno(id_aluno)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# Endpoints derivados das VIEWS do schema -----------------------------------

@app.get("/alunos/{id_aluno}/escola-atual", tags=["Aluno"])
def escola_atual_do_aluno(id_aluno: int):
    if not db.buscar_aluno(id_aluno):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    resultado = db.escola_atual_do_aluno(id_aluno)
    if not resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não possui matrícula ativa em nenhuma escola.")
    return resultado


@app.get("/alunos/{id_aluno}/responsaveis-financeiros", tags=["Aluno"])
def responsaveis_financeiros_do_aluno(id_aluno: int):
    if not db.buscar_aluno(id_aluno):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return db.responsaveis_financeiros_do_aluno(id_aluno)


@app.get("/alunos/{id_aluno}/medias", tags=["Aluno"])
def medias_dinamicas_do_aluno(id_aluno: int):
    if not db.buscar_aluno(id_aluno):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return db.medias_dinamicas_do_aluno(id_aluno)


# ===========================================================================
# TURMA
# ===========================================================================

@app.post("/turmas", response_model=TurmaSaida, status_code=status.HTTP_201_CREATED, tags=["Turma"])
def criar_turma(payload: TurmaEntrada):
    try:
        return db.inserir_turma(
            payload.NomeTurma, payload.Serie, payload.Turno.value,
            payload.Capacidade, payload.Escola_idEscola, payload.AnoLetivo,
        )
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/turmas", response_model=List[TurmaSaida], tags=["Turma"])
def listar_turmas(escola_id: Optional[int] = Query(None)):
    return db.listar_turmas(escola_id=escola_id)


@app.get("/turmas/{id_turma}", response_model=TurmaSaida, tags=["Turma"])
def obter_turma(id_turma: int):
    turma = db.buscar_turma(id_turma)
    if not turma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada.")
    return turma


@app.patch("/turmas/{id_turma}", response_model=TurmaSaida, tags=["Turma"])
def atualizar_turma(id_turma: int, payload: TurmaAtualizacao):
    if not db.buscar_turma(id_turma):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada.")
    try:
        return db.atualizar_turma(id_turma, campos_para_update(payload))
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.delete("/turmas/{id_turma}", status_code=status.HTTP_204_NO_CONTENT, tags=["Turma"])
def deletar_turma(id_turma: int):
    if not db.buscar_turma(id_turma):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada.")
    try:
        db.excluir_turma(id_turma)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# PROFESSOR
# ===========================================================================

@app.post("/professores", response_model=ProfessorSaida, status_code=status.HTTP_201_CREATED, tags=["Professor"])
def criar_professor(payload: ProfessorEntrada):
    try:
        return db.inserir_professor(
            payload.NomeProf, payload.CpfProf, payload.TelefoneProf, payload.EmailProf,
            payload.CepProf, payload.EnderecoProf, payload.Situacao.value, payload.Escola_idEscola,
        )
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/professores", response_model=List[ProfessorSaida], tags=["Professor"])
def listar_professores(escola_id: Optional[int] = Query(None)):
    return db.listar_professores(escola_id=escola_id)


@app.get("/professores/{id_professor}", response_model=ProfessorSaida, tags=["Professor"])
def obter_professor(id_professor: int):
    professor = db.buscar_professor(id_professor)
    if not professor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado.")
    return professor


@app.patch("/professores/{id_professor}", response_model=ProfessorSaida, tags=["Professor"])
def atualizar_professor(id_professor: int, payload: ProfessorAtualizacao):
    if not db.buscar_professor(id_professor):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado.")
    try:
        return db.atualizar_professor(id_professor, campos_para_update(payload))
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.delete("/professores/{id_professor}", status_code=status.HTTP_204_NO_CONTENT, tags=["Professor"])
def deletar_professor(id_professor: int):
    if not db.buscar_professor(id_professor):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado.")
    try:
        db.excluir_professor(id_professor)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# MATRICULA
# ===========================================================================

@app.post("/matriculas", response_model=MatriculaSaida, status_code=status.HTTP_201_CREATED, tags=["Matricula"])
def criar_matricula(payload: MatriculaEntrada):
    try:
        return db.inserir_matricula(payload.Aluno_idAluno, payload.Turma_idTurma, payload.DataMatricula, payload.Situacao.value)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/matriculas", response_model=List[MatriculaSaida], tags=["Matricula"])
def listar_matriculas(aluno_id: Optional[int] = Query(None), turma_id: Optional[int] = Query(None)):
    return db.listar_matriculas(aluno_id=aluno_id, turma_id=turma_id)


@app.get("/matriculas/{id_matricula}", response_model=MatriculaSaida, tags=["Matricula"])
def obter_matricula(id_matricula: int):
    matricula = db.buscar_matricula(id_matricula)
    if not matricula:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matrícula não encontrada.")
    return matricula


@app.patch("/matriculas/{id_matricula}", response_model=MatriculaSaida, tags=["Matricula"])
def atualizar_matricula(id_matricula: int, payload: MatriculaAtualizacao):
    if not db.buscar_matricula(id_matricula):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matrícula não encontrada.")
    try:
        return db.atualizar_matricula(id_matricula, campos_para_update(payload))
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.delete("/matriculas/{id_matricula}", status_code=status.HTTP_204_NO_CONTENT, tags=["Matricula"])
def deletar_matricula(id_matricula: int):
    if not db.buscar_matricula(id_matricula):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matrícula não encontrada.")
    db.excluir_matricula(id_matricula)


# ===========================================================================
# VÍNCULO ALUNO <-> RESPONSAVEL
# ===========================================================================

@app.post(
    "/alunos/{id_aluno}/responsaveis/{id_responsavel}",
    response_model=VinculoResponsavelSaida,
    status_code=status.HTTP_201_CREATED,
    tags=["Vinculo Aluno-Responsavel"],
)
def vincular_responsavel(id_aluno: int, id_responsavel: int, payload: VinculoResponsavelEntrada):
    if not db.buscar_aluno(id_aluno):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    if not db.buscar_responsavel(id_responsavel):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsável não encontrado.")
    try:
        return db.vincular_responsavel(id_aluno, id_responsavel, payload.TipoResponsavel.value, int(payload.ResponsavelFinanceiro))
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get(
    "/alunos/{id_aluno}/responsaveis",
    response_model=List[VinculoResponsavelSaida],
    tags=["Vinculo Aluno-Responsavel"],
)
def listar_responsaveis_do_aluno(id_aluno: int):
    if not db.buscar_aluno(id_aluno):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return db.listar_responsaveis_do_aluno(id_aluno)


@app.delete(
    "/alunos/{id_aluno}/responsaveis/{id_responsavel}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Vinculo Aluno-Responsavel"],
)
def desvincular_responsavel(id_aluno: int, id_responsavel: int):
    if not db.buscar_vinculo(id_aluno, id_responsavel):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vínculo não encontrado.")
    db.desvincular_responsavel(id_aluno, id_responsavel)


# ===========================================================================
# GRADE CURRICULAR
# ===========================================================================

@app.post("/grades", response_model=GradeCurricularSaida, status_code=status.HTTP_201_CREATED, tags=["Grade Curricular"])
def criar_grade(payload: GradeCurricularEntrada):
    try:
        return db.inserir_grade(payload.Turma_idTurma, payload.Materia_idMateria, payload.Professor_idProfessor)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/grades", response_model=List[GradeCurricularSaida], tags=["Grade Curricular"])
def listar_grades(turma_id: Optional[int] = Query(None)):
    return db.listar_grades(turma_id=turma_id)


@app.get("/grades/{id_grade}", response_model=GradeCurricularSaida, tags=["Grade Curricular"])
def obter_grade(id_grade: int):
    grade = db.buscar_grade(id_grade)
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade curricular não encontrada.")
    return grade


@app.delete("/grades/{id_grade}", status_code=status.HTTP_204_NO_CONTENT, tags=["Grade Curricular"])
def deletar_grade(id_grade: int):
    if not db.buscar_grade(id_grade):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade curricular não encontrada.")
    try:
        db.excluir_grade(id_grade)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# AVALIACAO
# ===========================================================================

@app.post("/avaliacoes", response_model=AvaliacaoSaida, status_code=status.HTTP_201_CREATED, tags=["Avaliacao"])
def criar_avaliacao(payload: AvaliacaoEntrada):
    try:
        return db.inserir_avaliacao(
            payload.Grade_idGrade, payload.Periodo_idPeriodo, payload.Tipo.value,
            payload.NomeAvaliacao, payload.DataAvaliacao, payload.Peso,
        )
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/avaliacoes", response_model=List[AvaliacaoSaida], tags=["Avaliacao"])
def listar_avaliacoes(grade_id: Optional[int] = Query(None), periodo_id: Optional[int] = Query(None)):
    return db.listar_avaliacoes(grade_id=grade_id, periodo_id=periodo_id)


@app.get("/avaliacoes/{id_avaliacao}", response_model=AvaliacaoSaida, tags=["Avaliacao"])
def obter_avaliacao(id_avaliacao: int):
    avaliacao = db.buscar_avaliacao(id_avaliacao)
    if not avaliacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada.")
    return avaliacao


@app.patch("/avaliacoes/{id_avaliacao}", response_model=AvaliacaoSaida, tags=["Avaliacao"])
def atualizar_avaliacao(id_avaliacao: int, payload: AvaliacaoAtualizacao):
    if not db.buscar_avaliacao(id_avaliacao):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada.")
    try:
        return db.atualizar_avaliacao(id_avaliacao, campos_para_update(payload))
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.delete("/avaliacoes/{id_avaliacao}", status_code=status.HTTP_204_NO_CONTENT, tags=["Avaliacao"])
def deletar_avaliacao(id_avaliacao: int):
    if not db.buscar_avaliacao(id_avaliacao):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada.")
    try:
        db.excluir_avaliacao(id_avaliacao)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


# ===========================================================================
# NOTA
# ===========================================================================

@app.post("/notas", response_model=NotaSaida, status_code=status.HTTP_201_CREATED, tags=["Nota"])
def criar_nota(payload: NotaEntrada):
    try:
        return db.inserir_nota(payload.Avaliacao_idAvaliacao, payload.Aluno_idAluno, payload.ValorNota)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/notas", response_model=List[NotaSaida], tags=["Nota"])
def listar_notas(avaliacao_id: Optional[int] = Query(None), aluno_id: Optional[int] = Query(None)):
    return db.listar_notas(avaliacao_id=avaliacao_id, aluno_id=aluno_id)


@app.get("/notas/{id_nota}", response_model=NotaSaida, tags=["Nota"])
def obter_nota(id_nota: int):
    nota = db.buscar_nota(id_nota)
    if not nota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada.")
    return nota


@app.patch("/notas/{id_nota}", response_model=NotaSaida, tags=["Nota"])
def atualizar_nota(id_nota: int, payload: NotaAtualizacao):
    if not db.buscar_nota(id_nota):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada.")
    return db.atualizar_nota(id_nota, campos_para_update(payload))


@app.delete("/notas/{id_nota}", status_code=status.HTTP_204_NO_CONTENT, tags=["Nota"])
def deletar_nota(id_nota: int):
    if not db.buscar_nota(id_nota):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada.")
    db.excluir_nota(id_nota)


# ===========================================================================
# FREQUENCIA
# ===========================================================================

@app.post("/frequencias", response_model=FrequenciaSaida, status_code=status.HTTP_201_CREATED, tags=["Frequencia"])
def criar_frequencia(payload: FrequenciaEntrada):
    try:
        return db.inserir_frequencia(payload.Grade_idGrade, payload.Aluno_idAluno, payload.DataFrequencia, payload.Situacao.value)
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/frequencias", response_model=List[FrequenciaSaida], tags=["Frequencia"])
def listar_frequencias(grade_id: Optional[int] = Query(None), aluno_id: Optional[int] = Query(None)):
    return db.listar_frequencias(grade_id=grade_id, aluno_id=aluno_id)


@app.get("/frequencias/{id_frequencia}", response_model=FrequenciaSaida, tags=["Frequencia"])
def obter_frequencia(id_frequencia: int):
    frequencia = db.buscar_frequencia(id_frequencia)
    if not frequencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de frequência não encontrado.")
    return frequencia


@app.patch("/frequencias/{id_frequencia}", response_model=FrequenciaSaida, tags=["Frequencia"])
def atualizar_frequencia(id_frequencia: int, payload: FrequenciaAtualizacao):
    if not db.buscar_frequencia(id_frequencia):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de frequência não encontrado.")
    try:
        return db.atualizar_frequencia(id_frequencia, campos_para_update(payload))
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.delete("/frequencias/{id_frequencia}", status_code=status.HTTP_204_NO_CONTENT, tags=["Frequencia"])
def deletar_frequencia(id_frequencia: int):
    if not db.buscar_frequencia(id_frequencia):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de frequência não encontrado.")
    db.excluir_frequencia(id_frequencia)


# ===========================================================================
# BOLETIM
# ===========================================================================

@app.post("/boletins", response_model=BoletimSaida, status_code=status.HTTP_201_CREATED, tags=["Boletim"])
def criar_boletim(payload: BoletimEntrada):
    try:
        return db.inserir_boletim(
            payload.Aluno_idAluno, payload.Periodo_idPeriodo, payload.Materia_idMateria,
            payload.MediaFinal, payload.Situacao.value,
        )
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/boletins", response_model=List[BoletimSaida], tags=["Boletim"])
def listar_boletins(aluno_id: Optional[int] = Query(None), periodo_id: Optional[int] = Query(None)):
    return db.listar_boletins(aluno_id=aluno_id, periodo_id=periodo_id)


@app.get("/boletins/{id_boletim}", response_model=BoletimSaida, tags=["Boletim"])
def obter_boletim(id_boletim: int):
    boletim = db.buscar_boletim(id_boletim)
    if not boletim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boletim não encontrado.")
    return boletim


@app.patch("/boletins/{id_boletim}", response_model=BoletimSaida, tags=["Boletim"])
def atualizar_boletim(id_boletim: int, payload: BoletimAtualizacao):
    if not db.buscar_boletim(id_boletim):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boletim não encontrado.")
    return db.atualizar_boletim(id_boletim, campos_para_update(payload))


@app.delete("/boletins/{id_boletim}", status_code=status.HTTP_204_NO_CONTENT, tags=["Boletim"])
def deletar_boletim(id_boletim: int):
    if not db.buscar_boletim(id_boletim):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boletim não encontrado.")
    db.excluir_boletim(id_boletim)


# ===========================================================================
# BOLETO
# ===========================================================================

@app.post("/boletos", response_model=BoletoSaida, status_code=status.HTTP_201_CREATED, tags=["Boleto"])
def criar_boleto(payload: BoletoEntrada):
    try:
        return db.inserir_boleto(
            payload.NumeroBoleto, payload.Aluno_idAluno, payload.Competencia,
            payload.ValorMensalidade, payload.DataVencimento, payload.Situacao.value,
        )
    except pymysql.err.IntegrityError as exc:
        tratar_integrity_error(exc)


@app.get("/boletos", response_model=List[BoletoSaida], tags=["Boleto"])
def listar_boletos(aluno_id: Optional[int] = Query(None), situacao: Optional[str] = Query(None)):
    return db.listar_boletos(aluno_id=aluno_id, situacao=situacao)


@app.get("/boletos/{id_boleto}", response_model=BoletoSaida, tags=["Boleto"])
def obter_boleto(id_boleto: int):
    boleto = db.buscar_boleto(id_boleto)
    if not boleto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boleto não encontrado.")
    return boleto


@app.patch("/boletos/{id_boleto}", response_model=BoletoSaida, tags=["Boleto"])
def atualizar_boleto(id_boleto: int, payload: BoletoAtualizacao):
    if not db.buscar_boleto(id_boleto):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boleto não encontrado.")
    return db.atualizar_boleto(id_boleto, campos_para_update(payload))


@app.delete("/boletos/{id_boleto}", status_code=status.HTTP_204_NO_CONTENT, tags=["Boleto"])
def deletar_boleto(id_boleto: int):
    if not db.buscar_boleto(id_boleto):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boleto não encontrado.")
    db.excluir_boleto(id_boleto)
