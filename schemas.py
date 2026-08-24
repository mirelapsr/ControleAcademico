"""
schemas.py — CAMADA DE VALIDAÇÃO
=================================
Contratos de entrada/saída da API (Pydantic). 
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic.alias_generators import to_camel


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO BASE
# ---------------------------------------------------------------------------
class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


# ---------------------------------------------------------------------------
# ENUMs (espelham os ENUM do Academic.sql)
# ---------------------------------------------------------------------------

class TurnoEnum(str, Enum):
    manha = "Manha"
    tarde = "Tarde"
    noite = "Noite"
    integral = "Integral"


class SituacaoPeriodoEnum(str, Enum):
    ativo = "Ativo"
    encerrado = "Encerrado"


class SituacaoAlunoEnum(str, Enum):
    ativo = "Ativo"
    inativo = "Inativo"
    transferido = "Transferido"


class SituacaoProfessorEnum(str, Enum):
    ativo = "Ativo"
    inativo = "Inativo"


class SituacaoMatriculaEnum(str, Enum):
    ativa = "Ativa"
    cancelada = "Cancelada"
    transferida = "Transferida"
    concluida = "Concluida"


class TipoResponsavelEnum(str, Enum):
    pai = "Pai"
    mae = "Mae"
    responsavel_legal = "ResponsavelLegal"
    outro = "Outro"


class TipoAvaliacaoEnum(str, Enum):
    prova = "Prova"
    trabalho = "Trabalho"
    projeto = "Projeto"
    recuperacao = "Recuperacao"


class SituacaoFrequenciaEnum(str, Enum):
    presente = "Presente"
    falta = "Falta"
    falta_justificada = "FaltaJustificada"


class SituacaoBoletimEnum(str, Enum):
    aberto = "Aberto"
    fechado = "Fechado"


class SituacaoBoletoEnum(str, Enum):
    pendente = "Pendente"
    pago = "Pago"
    atrasado = "Atrasado"
    cancelado = "Cancelado"


# ---------------------------------------------------------------------------
# ESCOLA
# ---------------------------------------------------------------------------

class EscolaEntrada(ApiModel):
    nome_escola: str = Field(..., max_length=150)
    codigo_inep: Optional[str] = Field(None, max_length=8)
    cnpj: Optional[str] = Field(None, max_length=14)
    endereco_escola: Optional[str] = Field(None, max_length=200)
    telefone_escola: Optional[str] = Field(None, max_length=13)
    email_escola: Optional[EmailStr] = None


class EscolaAtualizacao(ApiModel):
    nome_escola: Optional[str] = Field(None, max_length=150)
    codigo_inep: Optional[str] = Field(None, max_length=8)
    cnpj: Optional[str] = Field(None, max_length=14)
    endereco_escola: Optional[str] = Field(None, max_length=200)
    telefone_escola: Optional[str] = Field(None, max_length=13)
    email_escola: Optional[EmailStr] = None


class EscolaSaida(EscolaEntrada):
    id_escola: int


# ---------------------------------------------------------------------------
# PERIODO
# ---------------------------------------------------------------------------

class PeriodoEntrada(ApiModel):
    ano: int = Field(..., ge=2000, le=2100)
    nome_periodo: str = Field(..., max_length=30)
    data_inicio: date
    data_fim: date
    situacao: SituacaoPeriodoEnum = SituacaoPeriodoEnum.ativo


class PeriodoAtualizacao(ApiModel):
    ano: Optional[int] = Field(None, ge=2000, le=2100)
    nome_periodo: Optional[str] = Field(None, max_length=30)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    situacao: Optional[SituacaoPeriodoEnum] = None


class PeriodoSaida(PeriodoEntrada):
    id_periodo: int


# ---------------------------------------------------------------------------
# MATERIA
# ---------------------------------------------------------------------------

class MateriaEntrada(ApiModel):
    nome_materia: str = Field(..., max_length=80)
    carga_horaria: int = Field(..., gt=0)


class MateriaAtualizacao(ApiModel):
    nome_materia: Optional[str] = Field(None, max_length=80)
    carga_horaria: Optional[int] = Field(None, gt=0)


class MateriaSaida(MateriaEntrada):
    id_materia: int


# ---------------------------------------------------------------------------
# RESPONSAVEL
# ---------------------------------------------------------------------------

class ResponsavelEntrada(ApiModel):
    nome_resp: str = Field(..., max_length=100)
    cpf_resp: Optional[str] = Field(None, max_length=11)
    telefone_resp: Optional[str] = Field(None, max_length=13)
    email_resp: Optional[EmailStr] = None
    cep_resp: Optional[str] = Field(None, max_length=8)
    endereco_resp: Optional[str] = Field(None, max_length=200)


class ResponsavelAtualizacao(ApiModel):
    nome_resp: Optional[str] = Field(None, max_length=100)
    cpf_resp: Optional[str] = Field(None, max_length=11)
    telefone_resp: Optional[str] = Field(None, max_length=13)
    email_resp: Optional[EmailStr] = None
    cep_resp: Optional[str] = Field(None, max_length=8)
    endereco_resp: Optional[str] = Field(None, max_length=200)


class ResponsavelSaida(ResponsavelEntrada):
    id_responsavel: int


# ---------------------------------------------------------------------------
# ALUNO
# ---------------------------------------------------------------------------

class AlunoEntrada(ApiModel):
    numero_matricula: str = Field(..., max_length=20)
    nome_aluno: str = Field(..., max_length=100)
    data_nascimento: date
    cpf_aluno: Optional[str] = Field(None, max_length=11)
    telefone_aluno: Optional[str] = Field(None, max_length=13)
    email_aluno: Optional[EmailStr] = None
    cep_aluno: Optional[str] = Field(None, max_length=8)
    endereco_aluno: Optional[str] = Field(None, max_length=200)
    situacao: SituacaoAlunoEnum = SituacaoAlunoEnum.ativo


class AlunoAtualizacao(ApiModel):
    numero_matricula: Optional[str] = Field(None, max_length=20)
    nome_aluno: Optional[str] = Field(None, max_length=100)
    data_nascimento: Optional[date] = None
    cpf_aluno: Optional[str] = Field(None, max_length=11)
    telefone_aluno: Optional[str] = Field(None, max_length=13)
    email_aluno: Optional[EmailStr] = None
    cep_aluno: Optional[str] = Field(None, max_length=8)
    endereco_aluno: Optional[str] = Field(None, max_length=200)
    situacao: Optional[SituacaoAlunoEnum] = None


class AlunoSaida(AlunoEntrada):
    id_aluno: int


# ---------------------------------------------------------------------------
# TURMA
# ---------------------------------------------------------------------------

class TurmaEntrada(ApiModel):
    nome_turma: str = Field(..., max_length=30)
    serie: Optional[str] = Field(None, max_length=45)
    turno: TurnoEnum
    capacidade: Optional[int] = Field(None, gt=0)
    escola_id: int
    ano_letivo: int = Field(..., ge=2000, le=2100)


class TurmaAtualizacao(ApiModel):
    nome_turma: Optional[str] = Field(None, max_length=30)
    serie: Optional[str] = Field(None, max_length=45)
    turno: Optional[TurnoEnum] = None
    capacidade: Optional[int] = Field(None, gt=0)
    escola_id: Optional[int] = None
    ano_letivo: Optional[int] = Field(None, ge=2000, le=2100)


class TurmaSaida(TurmaEntrada):
    id_turma: int


# ---------------------------------------------------------------------------
# PROFESSOR
# ---------------------------------------------------------------------------

class ProfessorEntrada(ApiModel):
    nome_prof: str = Field(..., max_length=100)
    cpf_prof: Optional[str] = Field(None, max_length=11)
    telefone_prof: Optional[str] = Field(None, max_length=13)
    email_prof: Optional[EmailStr] = None
    cep_prof: Optional[str] = Field(None, max_length=8)
    endereco_prof: Optional[str] = Field(None, max_length=200)
    situacao: SituacaoProfessorEnum = SituacaoProfessorEnum.ativo
    escola_id: int


class ProfessorAtualizacao(ApiModel):
    nome_prof: Optional[str] = Field(None, max_length=100)
    cpf_prof: Optional[str] = Field(None, max_length=11)
    telefone_prof: Optional[str] = Field(None, max_length=13)
    email_prof: Optional[EmailStr] = None
    cep_prof: Optional[str] = Field(None, max_length=8)
    endereco_prof: Optional[str] = Field(None, max_length=200)
    situacao: Optional[SituacaoProfessorEnum] = None
    escola_id: Optional[int] = None


class ProfessorSaida(ProfessorEntrada):
    id_professor: int


# ---------------------------------------------------------------------------
# MATRICULA
# ---------------------------------------------------------------------------

class MatriculaEntrada(ApiModel):
    aluno_id: int
    turma_id: int
    data_matricula: date
    situacao: SituacaoMatriculaEnum = SituacaoMatriculaEnum.ativa


class MatriculaAtualizacao(ApiModel):
    aluno_id: Optional[int] = None
    turma_id: Optional[int] = None
    data_matricula: Optional[date] = None
    situacao: Optional[SituacaoMatriculaEnum] = None


class MatriculaSaida(MatriculaEntrada):
    id_matricula: int


# ---------------------------------------------------------------------------
# ALUNORESPONSAVEL (vínculo aluno <-> responsável)
# ---------------------------------------------------------------------------

class VinculoResponsavelEntrada(ApiModel):
    tipo_responsavel: TipoResponsavelEnum
    responsavel_financeiro: bool = False


class VinculoResponsavelSaida(ApiModel):
    aluno_id: int
    responsavel_id: int
    tipo_responsavel: TipoResponsavelEnum
    responsavel_financeiro: bool


# ---------------------------------------------------------------------------
# GRADE CURRICULAR
# ---------------------------------------------------------------------------

class GradeCurricularEntrada(ApiModel):
    turma_id: int
    materia_id: int
    professor_id: int


class GradeCurricularSaida(GradeCurricularEntrada):
    id_grade: int


# ---------------------------------------------------------------------------
# AVALIACAO
# ---------------------------------------------------------------------------

class AvaliacaoEntrada(ApiModel):
    grade_id: int
    periodo_id: int
    tipo: TipoAvaliacaoEnum
    nome_avaliacao: str = Field(..., max_length=100)
    data_avaliacao: date
    peso: Decimal = Field(default=Decimal("1.00"), gt=0, le=99.99)


class AvaliacaoAtualizacao(ApiModel):
    grade_id: Optional[int] = None
    periodo_id: Optional[int] = None
    tipo: Optional[TipoAvaliacaoEnum] = None
    nome_avaliacao: Optional[str] = Field(None, max_length=100)
    data_avaliacao: Optional[date] = None
    peso: Optional[Decimal] = Field(None, gt=0, le=99.99)


class AvaliacaoSaida(AvaliacaoEntrada):
    id_avaliacao: int


# ---------------------------------------------------------------------------
# NOTA
# ---------------------------------------------------------------------------

class NotaEntrada(ApiModel):
    avaliacao_id: int
    aluno_id: int
    valor_nota: Decimal = Field(..., ge=0, le=10)


class NotaAtualizacao(ApiModel):
    valor_nota: Optional[Decimal] = Field(None, ge=0, le=10)


class NotaSaida(NotaEntrada):
    id_nota: int


# ---------------------------------------------------------------------------
# FREQUENCIA
# ---------------------------------------------------------------------------

class FrequenciaEntrada(ApiModel):
    grade_id: int
    aluno_id: int
    data_frequencia: date
    situacao: SituacaoFrequenciaEnum


class FrequenciaAtualizacao(ApiModel):
    situacao: Optional[SituacaoFrequenciaEnum] = None
    data_frequencia: Optional[date] = None


class FrequenciaSaida(FrequenciaEntrada):
    id_frequencia: int


# ---------------------------------------------------------------------------
# BOLETIM
# ---------------------------------------------------------------------------

class BoletimEntrada(ApiModel):
    aluno_id: int
    periodo_id: int
    materia_id: int
    media_final: Decimal = Field(..., ge=0, le=10)
    situacao: SituacaoBoletimEnum = SituacaoBoletimEnum.aberto


class BoletimAtualizacao(ApiModel):
    media_final: Optional[Decimal] = Field(None, ge=0, le=10)
    situacao: Optional[SituacaoBoletimEnum] = None


class BoletimSaida(BoletimEntrada):
    id_boletim: int


# ---------------------------------------------------------------------------
# BOLETO
# ---------------------------------------------------------------------------

class BoletoEntrada(ApiModel):
    numero_boleto: str = Field(..., max_length=50)
    aluno_id: int
    competencia: str = Field(..., min_length=7, max_length=7, description="Formato AAAA-MM")
    valor_mensalidade: Decimal = Field(..., gt=0)
    data_vencimento: date
    situacao: SituacaoBoletoEnum = SituacaoBoletoEnum.pendente


class BoletoAtualizacao(ApiModel):
    data_pagamento: Optional[date] = None
    situacao: Optional[SituacaoBoletoEnum] = None


class BoletoSaida(ApiModel):
    id_boleto: int
    numero_boleto: str
    aluno_id: int
    competencia: str
    valor_mensalidade: Decimal
    data_vencimento: date
    data_pagamento: Optional[date] = None
    situacao: SituacaoBoletoEnum