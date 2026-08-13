-- =========================================================
-- BANCO DE DADOS
-- Observação: Execute este CREATE DATABASE separadamente se o banco não existir.
-- Após criar, mude a conexão do DataGrip para apontar para o CAcademic.
-- CREATE DATABASE CAcademic;
-- =========================================================
-- No PostgreSQL, o DROP CASCADE ignora restrições de chaves estrangeiras na hora de dropar
CREATE DATABASE "CAcademic";
DROP VIEW IF EXISTS vw_aluno_media_dinamica CASCADE;
DROP VIEW IF EXISTS vw_aluno_escola_atual CASCADE;
DROP VIEW IF EXISTS vw_aluno_responsavel_financeiro CASCADE;

DROP TABLE IF EXISTS boleto CASCADE;
DROP TABLE IF EXISTS boletim CASCADE;
DROP TABLE IF EXISTS frequencia CASCADE;
DROP TABLE IF EXISTS nota CASCADE;
DROP TABLE IF EXISTS avaliacao CASCADE;
DROP TABLE IF EXISTS grade_curricular CASCADE;
DROP TABLE IF EXISTS materia CASCADE;
DROP TABLE IF EXISTS professor CASCADE;
DROP TABLE IF EXISTS matricula CASCADE;
DROP TABLE IF EXISTS alunoresponsavel CASCADE;
DROP TABLE IF EXISTS responsavel CASCADE;
DROP TABLE IF EXISTS aluno CASCADE;
DROP TABLE IF EXISTS turma CASCADE;
DROP TABLE IF EXISTS periodo CASCADE;
DROP TABLE IF EXISTS escola CASCADE;

-- ---------------------------------------------------------
-- FUNÇÃO GENÉRICA DE TIMESTAMP
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION atualiza_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.AtualizadoEm = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------
-- escola
-- ---------------------------------------------------------
CREATE TABLE escola (
    idEscola        SERIAL PRIMARY KEY,
    NomeEscola      VARCHAR(150) NOT NULL,
    CodigoInep      VARCHAR(8)  UNIQUE,
    Cnpj            VARCHAR(14) UNIQUE,
    EnderecoEscola  VARCHAR(200),
    TelefoneEscola  VARCHAR(13),
    EmailEscola     VARCHAR(100),
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_escola_upd BEFORE UPDATE ON escola
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- periodo
-- ---------------------------------------------------------
CREATE TABLE periodo (
    idPeriodo       SERIAL PRIMARY KEY,
    Ano             SMALLINT NOT NULL,
    NomePeriodo     VARCHAR(30) NOT NULL,
    DataInicio      DATE NOT NULL,
    DataFim         DATE NOT NULL,
    Situacao        VARCHAR(50) NOT NULL DEFAULT 'Ativo',
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_periodo_situacao CHECK (Situacao IN ('Ativo','Encerrado')),
    CONSTRAINT chk_periodo_datas CHECK (DataFim > DataInicio)
);

CREATE TRIGGER trg_periodo_upd BEFORE UPDATE ON periodo
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- turma
-- ---------------------------------------------------------
CREATE TABLE turma (
    idTurma              SERIAL PRIMARY KEY,
    NomeTurma            VARCHAR(30) NOT NULL,
    Serie                VARCHAR(45),
    Turno                VARCHAR(50) NOT NULL,
    Capacidade           INTEGER,
    Escola_idEscola      INTEGER NOT NULL,
    AnoLetivo            SMALLINT NOT NULL,
    CriadoEm             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_turma_turno CHECK (Turno IN ('Manha','Tarde','Noite','Integral')),
    CONSTRAINT chk_turma_capacidade CHECK (Capacidade IS NULL OR Capacidade > 0),
    CONSTRAINT fk_turma_escola FOREIGN KEY (Escola_idEscola) REFERENCES escola(idEscola) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_turma_escola_ano ON turma (Escola_idEscola, AnoLetivo);

CREATE TRIGGER trg_turma_upd BEFORE UPDATE ON turma
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- aluno
-- ---------------------------------------------------------
CREATE TABLE aluno (
    idAluno         SERIAL PRIMARY KEY,
    NumeroMatricula VARCHAR(20) NOT NULL UNIQUE,
    NomeAluno       VARCHAR(100) NOT NULL,
    DataNascimento  DATE NOT NULL,
    CpfAluno        VARCHAR(11) UNIQUE,
    TelefoneAluno   VARCHAR(13),
    EmailAluno      VARCHAR(100),
    CepAluno        VARCHAR(8),
    EnderecoAluno   VARCHAR(200),
    Situacao        VARCHAR(50) NOT NULL DEFAULT 'Ativo',
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_aluno_situacao CHECK (Situacao IN ('Ativo','Inativo','Transferido')),
    CONSTRAINT chk_cpf_aluno CHECK (CpfAluno IS NULL OR CpfAluno ~ '^[0-9]{11}$')
);

CREATE TRIGGER trg_aluno_upd BEFORE UPDATE ON aluno
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- responsavel
-- ---------------------------------------------------------
CREATE TABLE responsavel (
    idResponsavel   SERIAL PRIMARY KEY,
    NomeResp        VARCHAR(100) NOT NULL,
    CpfResp         VARCHAR(11) UNIQUE,
    TelefoneResp    VARCHAR(13),
    EmailResp       VARCHAR(100),
    CepResp         VARCHAR(8),
    EnderecoResp    VARCHAR(200),
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cpf_resp CHECK (CpfResp IS NULL OR CpfResp ~ '^[0-9]{11}$')
);

CREATE TRIGGER trg_responsavel_upd BEFORE UPDATE ON responsavel
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- alunoresponsavel
-- ---------------------------------------------------------
CREATE TABLE alunoresponsavel (
    Aluno_idAluno             INTEGER NOT NULL,
    Responsavel_idResponsavel INTEGER NOT NULL,
    TipoResponsavel           VARCHAR(50) NOT NULL,
    ResponsavelFinanceiro     BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (Aluno_idAluno, Responsavel_idResponsavel),
    CONSTRAINT chk_ar_tipo CHECK (TipoResponsavel IN ('Pai','Mae','ResponsavelLegal','Outro')),
    CONSTRAINT fk_ar_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ar_responsavel FOREIGN KEY (Responsavel_idResponsavel) REFERENCES responsavel(idResponsavel) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Triggers de Regras de Negócio: Responsável Financeiro Único
CREATE OR REPLACE FUNCTION func_ar_financeiro_unico_ins() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ResponsavelFinanceiro = TRUE THEN
        IF EXISTS (
            SELECT 1 FROM alunoresponsavel
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND ResponsavelFinanceiro = TRUE
        ) THEN
            RAISE EXCEPTION 'Aluno já possui um responsável financeiro cadastrado.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ar_financeiro_unico_ins
BEFORE INSERT ON alunoresponsavel
FOR EACH ROW EXECUTE FUNCTION func_ar_financeiro_unico_ins();


CREATE OR REPLACE FUNCTION func_ar_financeiro_unico_upd() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ResponsavelFinanceiro = TRUE THEN
        IF EXISTS (
            SELECT 1 FROM alunoresponsavel
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND ResponsavelFinanceiro = TRUE
              AND Responsavel_idResponsavel <> NEW.Responsavel_idResponsavel
        ) THEN
            RAISE EXCEPTION 'Aluno já possui um responsável financeiro cadastrado.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ar_financeiro_unico_upd
BEFORE UPDATE ON alunoresponsavel
FOR EACH ROW EXECUTE FUNCTION func_ar_financeiro_unico_upd();

-- ---------------------------------------------------------
-- matricula
-- ---------------------------------------------------------
CREATE TABLE matricula (
    idMatricula     SERIAL PRIMARY KEY,
    Aluno_idAluno   INTEGER NOT NULL,
    Turma_idTurma   INTEGER NOT NULL,
    DataMatricula   DATE NOT NULL,
    Situacao        VARCHAR(50) NOT NULL DEFAULT 'Ativa',
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_matricula_situacao CHECK (Situacao IN ('Ativa','Cancelada','Transferida','Concluida')),
    CONSTRAINT fk_matricula_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_matricula_turma FOREIGN KEY (Turma_idTurma) REFERENCES turma(idTurma) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_matricula_aluno_situacao ON matricula (Aluno_idAluno, Situacao);

CREATE TRIGGER trg_matricula_upd BEFORE UPDATE ON matricula
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- Triggers de Regras de Negócio: Matrícula Única Ativa
CREATE OR REPLACE FUNCTION func_matricula_unica_ativa_ins() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.Situacao = 'Ativa' THEN
        IF EXISTS (
            SELECT 1 FROM matricula
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND Situacao = 'Ativa'
        ) THEN
            RAISE EXCEPTION 'Aluno já possui uma matrícula ativa.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_matricula_unica_ativa_ins
BEFORE INSERT ON matricula
FOR EACH ROW EXECUTE FUNCTION func_matricula_unica_ativa_ins();


CREATE OR REPLACE FUNCTION func_matricula_unica_ativa_upd() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.Situacao = 'Ativa' THEN
        IF EXISTS (
            SELECT 1 FROM matricula
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND Situacao = 'Ativa'
              AND idMatricula <> NEW.idMatricula
        ) THEN
            RAISE EXCEPTION 'Aluno já possui uma matrícula ativa.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_matricula_unica_ativa_upd
BEFORE UPDATE ON matricula
FOR EACH ROW EXECUTE FUNCTION func_matricula_unica_ativa_upd();

-- ---------------------------------------------------------
-- professor
-- ---------------------------------------------------------
CREATE TABLE professor (
    idProfessor     SERIAL PRIMARY KEY,
    NomeProf        VARCHAR(100) NOT NULL,
    CpfProf         VARCHAR(11) UNIQUE,
    TelefoneProf    VARCHAR(13),
    EmailProf       VARCHAR(100),
    CepProf         VARCHAR(8),
    EnderecoProf    VARCHAR(200),
    Situacao        VARCHAR(50) NOT NULL DEFAULT 'Ativo',
    Escola_idEscola INTEGER NOT NULL,
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_prof_situacao CHECK (Situacao IN ('Ativo','Inativo')),
    CONSTRAINT chk_cpf_prof CHECK (CpfProf IS NULL OR CpfProf ~ '^[0-9]{11}$'),
    CONSTRAINT fk_professor_escola FOREIGN KEY (Escola_idEscola) REFERENCES escola(idEscola) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TRIGGER trg_professor_upd BEFORE UPDATE ON professor
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- materia
-- ---------------------------------------------------------
CREATE TABLE materia (
    idMateria       SERIAL PRIMARY KEY,
    NomeMateria     VARCHAR(80) NOT NULL,
    CargaHoraria    INTEGER,
    CONSTRAINT uq_materia_nome UNIQUE (NomeMateria),
    CONSTRAINT chk_materia_carga CHECK (CargaHoraria IS NULL OR CargaHoraria > 0)
);

-- ---------------------------------------------------------
-- grade_curricular
-- ---------------------------------------------------------
CREATE TABLE grade_curricular (
    idGrade               SERIAL PRIMARY KEY,
    Turma_idTurma         INTEGER NOT NULL,
    Materia_idMateria     INTEGER NOT NULL,
    Professor_idProfessor INTEGER NOT NULL,
    CONSTRAINT fk_grade_turma FOREIGN KEY (Turma_idTurma) REFERENCES turma(idTurma) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_grade_materia FOREIGN KEY (Materia_idMateria) REFERENCES materia(idMateria) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_grade_professor FOREIGN KEY (Professor_idProfessor) REFERENCES professor(idProfessor) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_turma_materia UNIQUE (Turma_idTurma, Materia_idMateria)
);

-- ---------------------------------------------------------
-- avaliacao
-- ---------------------------------------------------------
CREATE TABLE avaliacao (
    idAvaliacao       SERIAL PRIMARY KEY,
    Grade_idGrade     INTEGER NOT NULL,
    Periodo_idPeriodo INTEGER NOT NULL,
    Tipo              VARCHAR(50) NOT NULL,
    NomeAvaliacao     VARCHAR(100) NOT NULL,
    DataAvaliacao     DATE NOT NULL,
    Peso              DECIMAL(4,2) NOT NULL DEFAULT 1.00,
    CONSTRAINT chk_avaliacao_tipo CHECK (Tipo IN ('Prova','Trabalho','Projeto','Recuperacao')),
    CONSTRAINT chk_avaliacao_peso CHECK (Peso > 0),
    CONSTRAINT fk_avaliacao_grade FOREIGN KEY (Grade_idGrade) REFERENCES grade_curricular(idGrade) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_avaliacao_periodo FOREIGN KEY (Periodo_idPeriodo) REFERENCES periodo(idPeriodo) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_avaliacao_grade_periodo ON avaliacao (Grade_idGrade, Periodo_idPeriodo);

-- ---------------------------------------------------------
-- nota
-- ---------------------------------------------------------
CREATE TABLE nota (
    idNota                SERIAL PRIMARY KEY,
    Avaliacao_idAvaliacao INTEGER NOT NULL,
    Aluno_idAluno         INTEGER NOT NULL,
    ValorNota             DECIMAL(4,2) NOT NULL,
    CONSTRAINT chk_nota_valor CHECK (ValorNota BETWEEN 0 AND 10),
    CONSTRAINT fk_nota_avaliacao FOREIGN KEY (Avaliacao_idAvaliacao) REFERENCES avaliacao(idAvaliacao) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_nota_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_nota_avaliacao_aluno UNIQUE (Avaliacao_idAvaliacao, Aluno_idAluno)
);

CREATE INDEX idx_nota_aluno ON nota (Aluno_idAluno);

-- ---------------------------------------------------------
-- frequencia
-- ---------------------------------------------------------
CREATE TABLE frequencia (
    idFrequencia    SERIAL PRIMARY KEY,
    Grade_idGrade   INTEGER NOT NULL,
    Aluno_idAluno   INTEGER NOT NULL,
    DataFrequencia  DATE NOT NULL,
    Situacao        VARCHAR(50) NOT NULL,
    CONSTRAINT chk_freq_situacao CHECK (Situacao IN ('Presente','Falta','FaltaJustificada')),
    CONSTRAINT fk_frequencia_grade FOREIGN KEY (Grade_idGrade) REFERENCES grade_curricular(idGrade) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_frequencia_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_freq_aluno_grade_data UNIQUE (Grade_idGrade, Aluno_idAluno, DataFrequencia)
);

CREATE INDEX idx_frequencia_aluno_data ON frequencia (Aluno_idAluno, DataFrequencia);

-- ---------------------------------------------------------
-- boletim
-- ---------------------------------------------------------
CREATE TABLE boletim (
    idBoletim         SERIAL PRIMARY KEY,
    Aluno_idAluno     INTEGER NOT NULL,
    Periodo_idPeriodo INTEGER NOT NULL,
    Materia_idMateria INTEGER NOT NULL,
    MediaFinal        DECIMAL(4,2) NOT NULL,
    Situacao          VARCHAR(50) NOT NULL DEFAULT 'Aberto',
    CONSTRAINT chk_boletim_situacao CHECK (Situacao IN ('Aberto','Fechado')),
    CONSTRAINT fk_boletim_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_boletim_periodo FOREIGN KEY (Periodo_idPeriodo) REFERENCES periodo(idPeriodo) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_boletim_materia FOREIGN KEY (Materia_idMateria) REFERENCES materia(idMateria) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_boletim_aluno_periodo_materia UNIQUE (Aluno_idAluno, Periodo_idPeriodo, Materia_idMateria)
);

-- ---------------------------------------------------------
-- boleto
-- ---------------------------------------------------------
CREATE TABLE boleto (
    idBoleto         SERIAL PRIMARY KEY,
    NumeroBoleto     VARCHAR(50) NOT NULL UNIQUE,
    Aluno_idAluno    INTEGER NOT NULL,
    Competencia      CHAR(7) NOT NULL,
    ValorMensalidade DECIMAL(10,2) NOT NULL,
    DataVencimento   DATE NOT NULL,
    DataPagamento    DATE,
    Situacao         VARCHAR(50) NOT NULL DEFAULT 'Pendente',
    CONSTRAINT chk_boleto_situacao CHECK (Situacao IN ('Pendente','Pago','Atrasado','Cancelado')),
    CONSTRAINT chk_boleto_competencia CHECK (Competencia ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    CONSTRAINT chk_boleto_valor CHECK (ValorMensalidade > 0),
    CONSTRAINT chk_boleto_pagamento CHECK (
        (Situacao = 'Pago' AND DataPagamento IS NOT NULL) OR (Situacao <> 'Pago')
    ),
    CONSTRAINT fk_boleto_aluno FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_boleto_situacao_vencimento ON boleto (Situacao, DataVencimento);

-- =========================================================
-- Views
-- =========================================================

CREATE OR REPLACE VIEW vw_aluno_escola_atual AS
SELECT
    a.idAluno,
    e.idEscola,
    e.NomeEscola
FROM aluno a
JOIN matricula m ON m.Aluno_idAluno = a.idAluno AND m.Situacao = 'Ativa'
JOIN turma t ON t.idTurma = m.Turma_idTurma
JOIN escola e ON e.idEscola = t.Escola_idEscola;

CREATE OR REPLACE VIEW vw_aluno_responsavel_financeiro AS
SELECT
    ar.Aluno_idAluno,
    r.idResponsavel,
    r.NomeResp,
    r.EmailResp,
    r.TelefoneResp
FROM alunoresponsavel ar
JOIN responsavel r ON r.idResponsavel = ar.Responsavel_idResponsavel
WHERE ar.ResponsavelFinanceiro = TRUE;

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
GROUP BY
    n.Aluno_idAluno,
    a.Periodo_idPeriodo,
    g.Materia_idMateria;
