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

class EscolaEntrada(BaseModel):
    NomeEscola: str = Field(..., max_length=150)
    CodigoInep: Optional[str] = Field(None, max_length=8)
    Cnpj: Optional[str] = Field(None, max_length=14)
    EnderecoEscola: Optional[str] = Field(None, max_length=200)
    TelefoneEscola: Optional[str] = Field(None, max_length=13)
    EmailEscola: Optional[EmailStr] = None


class EscolaAtualizacao(BaseModel):
    NomeEscola: Optional[str] = Field(None, max_length=150)
    CodigoInep: Optional[str] = Field(None, max_length=8)
    Cnpj: Optional[str] = Field(None, max_length=14)
    EnderecoEscola: Optional[str] = Field(None, max_length=200)
    TelefoneEscola: Optional[str] = Field(None, max_length=13)
    EmailEscola: Optional[EmailStr] = None


class EscolaSaida(EscolaEntrada):
    model_config = ConfigDict(from_attributes=True)
    idEscola: int


# ---------------------------------------------------------------------------
# PERIODO
# ---------------------------------------------------------------------------

class PeriodoEntrada(BaseModel):
    Ano: int = Field(..., ge=2000, le=2100)
    NomePeriodo: str = Field(..., max_length=30)
    DataInicio: date
    DataFim: date
    Situacao: SituacaoPeriodoEnum = SituacaoPeriodoEnum.ativo


class PeriodoAtualizacao(BaseModel):
    Ano: Optional[int] = Field(None, ge=2000, le=2100)
    NomePeriodo: Optional[str] = Field(None, max_length=30)
    DataInicio: Optional[date] = None
    DataFim: Optional[date] = None
    Situacao: Optional[SituacaoPeriodoEnum] = None


class PeriodoSaida(PeriodoEntrada):
    model_config = ConfigDict(from_attributes=True)
    idPeriodo: int


# ---------------------------------------------------------------------------
# MATERIA
# ---------------------------------------------------------------------------

class MateriaEntrada(BaseModel):
    NomeMateria: str = Field(..., max_length=80)
    CargaHoraria: Optional[int] = Field(None, gt=0)


class MateriaAtualizacao(BaseModel):
    NomeMateria: Optional[str] = Field(None, max_length=80)
    CargaHoraria: Optional[int] = Field(None, gt=0)


class MateriaSaida(MateriaEntrada):
    model_config = ConfigDict(from_attributes=True)
    idMateria: int


# ---------------------------------------------------------------------------
# RESPONSAVEL
# ---------------------------------------------------------------------------

class ResponsavelEntrada(BaseModel):
    NomeResp: str = Field(..., max_length=100)
    CpfResp: Optional[str] = Field(None, max_length=11)
    TelefoneResp: Optional[str] = Field(None, max_length=13)
    EmailResp: Optional[EmailStr] = None
    CepResp: Optional[str] = Field(None, max_length=8)
    EnderecoResp: Optional[str] = Field(None, max_length=200)


class ResponsavelAtualizacao(BaseModel):
    NomeResp: Optional[str] = Field(None, max_length=100)
    CpfResp: Optional[str] = Field(None, max_length=11)
    TelefoneResp: Optional[str] = Field(None, max_length=13)
    EmailResp: Optional[EmailStr] = None
    CepResp: Optional[str] = Field(None, max_length=8)
    EnderecoResp: Optional[str] = Field(None, max_length=200)


class ResponsavelSaida(ResponsavelEntrada):
    model_config = ConfigDict(from_attributes=True)
    idResponsavel: int


# ---------------------------------------------------------------------------
# ALUNO
# ---------------------------------------------------------------------------

class AlunoEntrada(BaseModel):
    NumeroMatricula: str = Field(..., max_length=20)
    NomeAluno: str = Field(..., max_length=100)
    DataNascimento: date
    CpfAluno: Optional[str] = Field(None, max_length=11)
    TelefoneAluno: Optional[str] = Field(None, max_length=13)
    EmailAluno: Optional[EmailStr] = None
    CepAluno: Optional[str] = Field(None, max_length=8)
    EnderecoAluno: Optional[str] = Field(None, max_length=200)
    Situacao: SituacaoAlunoEnum = SituacaoAlunoEnum.ativo


class AlunoAtualizacao(BaseModel):
    NumeroMatricula: Optional[str] = Field(None, max_length=20)
    NomeAluno: Optional[str] = Field(None, max_length=100)
    DataNascimento: Optional[date] = None
    CpfAluno: Optional[str] = Field(None, max_length=11)
    TelefoneAluno: Optional[str] = Field(None, max_length=13)
    EmailAluno: Optional[EmailStr] = None
    CepAluno: Optional[str] = Field(None, max_length=8)
    EnderecoAluno: Optional[str] = Field(None, max_length=200)
    Situacao: Optional[SituacaoAlunoEnum] = None


class AlunoSaida(AlunoEntrada):
    model_config = ConfigDict(from_attributes=True)
    idAluno: int


# ---------------------------------------------------------------------------
# TURMA
# ---------------------------------------------------------------------------

class TurmaEntrada(BaseModel):
    NomeTurma: str = Field(..., max_length=30)
    Serie: Optional[str] = Field(None, max_length=45)
    Turno: TurnoEnum
    Capacidade: Optional[int] = Field(None, gt=0)
    Escola_idEscola: int
    AnoLetivo: int = Field(..., ge=2000, le=2100)


class TurmaAtualizacao(BaseModel):
    NomeTurma: Optional[str] = Field(None, max_length=30)
    Serie: Optional[str] = Field(None, max_length=45)
    Turno: Optional[TurnoEnum] = None
    Capacidade: Optional[int] = Field(None, gt=0)
    Escola_idEscola: Optional[int] = None
    AnoLetivo: Optional[int] = Field(None, ge=2000, le=2100)


class TurmaSaida(TurmaEntrada):
    model_config = ConfigDict(from_attributes=True)
    idTurma: int


# ---------------------------------------------------------------------------
# PROFESSOR
# ---------------------------------------------------------------------------

class ProfessorEntrada(BaseModel):
    NomeProf: str = Field(..., max_length=100)
    CpfProf: Optional[str] = Field(None, max_length=11)
    TelefoneProf: Optional[str] = Field(None, max_length=13)
    EmailProf: Optional[EmailStr] = None
    CepProf: Optional[str] = Field(None, max_length=8)
    EnderecoProf: Optional[str] = Field(None, max_length=200)
    Situacao: SituacaoProfessorEnum = SituacaoProfessorEnum.ativo
    Escola_idEscola: int


class ProfessorAtualizacao(BaseModel):
    NomeProf: Optional[str] = Field(None, max_length=100)
    CpfProf: Optional[str] = Field(None, max_length=11)
    TelefoneProf: Optional[str] = Field(None, max_length=13)
    EmailProf: Optional[EmailStr] = None
    CepProf: Optional[str] = Field(None, max_length=8)
    EnderecoProf: Optional[str] = Field(None, max_length=200)
    Situacao: Optional[SituacaoProfessorEnum] = None
    Escola_idEscola: Optional[int] = None


class ProfessorSaida(ProfessorEntrada):
    model_config = ConfigDict(from_attributes=True)
    idProfessor: int


# ---------------------------------------------------------------------------
# MATRICULA
# ---------------------------------------------------------------------------

class MatriculaEntrada(BaseModel):
    Aluno_idAluno: int
    Turma_idTurma: int
    DataMatricula: date
    Situacao: SituacaoMatriculaEnum = SituacaoMatriculaEnum.ativa


class MatriculaAtualizacao(BaseModel):
    Aluno_idAluno: Optional[int] = None
    Turma_idTurma: Optional[int] = None
    DataMatricula: Optional[date] = None
    Situacao: Optional[SituacaoMatriculaEnum] = None


class MatriculaSaida(MatriculaEntrada):
    model_config = ConfigDict(from_attributes=True)
    idMatricula: int


# ---------------------------------------------------------------------------
# ALUNORESPONSAVEL (vínculo aluno <-> responsável)
# ---------------------------------------------------------------------------

class VinculoResponsavelEntrada(BaseModel):
    TipoResponsavel: TipoResponsavelEnum
    ResponsavelFinanceiro: bool = False


class VinculoResponsavelSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    Aluno_idAluno: int
    Responsavel_idResponsavel: int
    TipoResponsavel: TipoResponsavelEnum
    ResponsavelFinanceiro: bool


# ---------------------------------------------------------------------------
# GRADE CURRICULAR
# ---------------------------------------------------------------------------

class GradeCurricularEntrada(BaseModel):
    Turma_idTurma: int
    Materia_idMateria: int
    Professor_idProfessor: int


class GradeCurricularSaida(GradeCurricularEntrada):
    model_config = ConfigDict(from_attributes=True)
    idGrade: int


# ---------------------------------------------------------------------------
# AVALIACAO
# ---------------------------------------------------------------------------

class AvaliacaoEntrada(BaseModel):
    Grade_idGrade: int
    Periodo_idPeriodo: int
    Tipo: TipoAvaliacaoEnum
    NomeAvaliacao: str = Field(..., max_length=100)
    DataAvaliacao: date
    Peso: Decimal = Field(default=Decimal("1.00"), gt=0, le=99.99)


class AvaliacaoAtualizacao(BaseModel):
    Grade_idGrade: Optional[int] = None
    Periodo_idPeriodo: Optional[int] = None
    Tipo: Optional[TipoAvaliacaoEnum] = None
    NomeAvaliacao: Optional[str] = Field(None, max_length=100)
    DataAvaliacao: Optional[date] = None
    Peso: Optional[Decimal] = Field(None, gt=0, le=99.99)


class AvaliacaoSaida(AvaliacaoEntrada):
    model_config = ConfigDict(from_attributes=True)
    idAvaliacao: int


# ---------------------------------------------------------------------------
# NOTA
# ---------------------------------------------------------------------------

class NotaEntrada(BaseModel):
    Avaliacao_idAvaliacao: int
    Aluno_idAluno: int
    ValorNota: Decimal = Field(..., ge=0, le=10)


class NotaAtualizacao(BaseModel):
    ValorNota: Optional[Decimal] = Field(None, ge=0, le=10)


class NotaSaida(NotaEntrada):
    model_config = ConfigDict(from_attributes=True)
    idNota: int


# ---------------------------------------------------------------------------
# FREQUENCIA
# ---------------------------------------------------------------------------

class FrequenciaEntrada(BaseModel):
    Grade_idGrade: int
    Aluno_idAluno: int
    DataFrequencia: date
    Situacao: SituacaoFrequenciaEnum


class FrequenciaAtualizacao(BaseModel):
    Situacao: Optional[SituacaoFrequenciaEnum] = None
    DataFrequencia: Optional[date] = None


class FrequenciaSaida(FrequenciaEntrada):
    model_config = ConfigDict(from_attributes=True)
    idFrequencia: int


# ---------------------------------------------------------------------------
# BOLETIM
# ---------------------------------------------------------------------------

class BoletimEntrada(BaseModel):
    Aluno_idAluno: int
    Periodo_idPeriodo: int
    Materia_idMateria: int
    MediaFinal: Decimal = Field(..., ge=0, le=10)
    Situacao: SituacaoBoletimEnum = SituacaoBoletimEnum.aberto


class BoletimAtualizacao(BaseModel):
    MediaFinal: Optional[Decimal] = Field(None, ge=0, le=10)
    Situacao: Optional[SituacaoBoletimEnum] = None


class BoletimSaida(BoletimEntrada):
    model_config = ConfigDict(from_attributes=True)
    idBoletim: int


# ---------------------------------------------------------------------------
# BOLETO
# ---------------------------------------------------------------------------

class BoletoEntrada(BaseModel):
    NumeroBoleto: str = Field(..., max_length=50)
    Aluno_idAluno: int
    Competencia: str = Field(..., min_length=7, max_length=7, description="Formato AAAA-MM")
    ValorMensalidade: Decimal = Field(..., gt=0)
    DataVencimento: date
    Situacao: SituacaoBoletoEnum = SituacaoBoletoEnum.pendente


class BoletoAtualizacao(BaseModel):
    DataPagamento: Optional[date] = None
    Situacao: Optional[SituacaoBoletoEnum] = None


class BoletoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    idBoleto: int
    NumeroBoleto: str
    Aluno_idAluno: int
    Competencia: str
    ValorMensalidade: Decimal
    DataVencimento: date
    DataPagamento: Optional[date] = None
    Situacao: SituacaoBoletoEnum
