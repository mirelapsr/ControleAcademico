CREATE DATABASE IF NOT EXISTS CAcademic
    CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE CAcademic;

SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS vw_aluno_media_dinamica;
DROP VIEW IF EXISTS vw_aluno_escola_atual;
DROP VIEW IF EXISTS vw_aluno_responsavel_financeiro;

DROP TABLE IF EXISTS boleto;
DROP TABLE IF EXISTS boletim;
DROP TABLE IF EXISTS frequencia;
DROP TABLE IF EXISTS nota;
DROP TABLE IF EXISTS avaliacao;
DROP TABLE IF EXISTS grade_curricular;
DROP TABLE IF EXISTS materia;
DROP TABLE IF EXISTS professor;
DROP TABLE IF EXISTS matricula;
DROP TABLE IF EXISTS alunoresponsavel;
DROP TABLE IF EXISTS responsavel;
DROP TABLE IF EXISTS aluno;
DROP TABLE IF EXISTS turma;
DROP TABLE IF EXISTS periodo;
DROP TABLE IF EXISTS escola;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------
-- escola
-- ---------------------------------------------------------
CREATE TABLE escola (
    idEscola        INT AUTO_INCREMENT PRIMARY KEY,
    NomeEscola      VARCHAR(150) NOT NULL,
    CodigoInep      VARCHAR(8)  UNIQUE,      
    Cnpj            VARCHAR(14) UNIQUE,      
    EnderecoEscola  VARCHAR(200),
    TelefoneEscola  VARCHAR(13),
    EmailEscola     VARCHAR(100),
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,                         
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- periodo
-- ---------------------------------------------------------
CREATE TABLE periodo (
    idPeriodo       INT AUTO_INCREMENT PRIMARY KEY,
    Ano             YEAR NOT NULL,
    NomePeriodo     VARCHAR(30) NOT NULL,
    DataInicio      DATE NOT NULL,
    DataFim         DATE NOT NULL,
    Situacao        ENUM('Ativo','Encerrado') NOT NULL DEFAULT 'Ativo',
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_periodo_datas CHECK (DataFim > DataInicio)  
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- turma
-- ---------------------------------------------------------
CREATE TABLE turma (
    idTurma              INT AUTO_INCREMENT PRIMARY KEY,
    NomeTurma            VARCHAR(30) NOT NULL,
    Serie                VARCHAR(45),
    Turno                ENUM('Manha','Tarde','Noite','Integral') NOT NULL,
    Capacidade           INT,
    Escola_idEscola      INT NOT NULL,
    AnoLetivo            YEAR NOT NULL,
    CriadoEm             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_turma_capacidade CHECK (Capacidade IS NULL OR Capacidade > 0), 
    CONSTRAINT fk_turma_escola
        FOREIGN KEY (Escola_idEscola) REFERENCES escola(idEscola)
        ON DELETE RESTRICT ON UPDATE CASCADE      
) ENGINE=InnoDB;

CREATE INDEX idx_turma_escola_ano ON turma (Escola_idEscola, AnoLetivo); 

-- ---------------------------------------------------------
-- aluno
-- ---------------------------------------------------------
CREATE TABLE aluno (
    idAluno         INT AUTO_INCREMENT PRIMARY KEY,
    NumeroMatricula VARCHAR(20) NOT NULL UNIQUE,   
    NomeAluno       VARCHAR(100) NOT NULL,
    DataNascimento  DATE NOT NULL,
    CpfAluno        VARCHAR(11) UNIQUE,            
    TelefoneAluno   VARCHAR(13),
    EmailAluno      VARCHAR(100),
    CepAluno        VARCHAR(8),
    EnderecoAluno   VARCHAR(200),
    Situacao        ENUM('Ativo','Inativo','Transferido') NOT NULL DEFAULT 'Ativo',
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_cpf_aluno CHECK (CpfAluno IS NULL OR CpfAluno REGEXP '^[0-9]{11}$') 
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- responsavel
-- ---------------------------------------------------------
CREATE TABLE responsavel (
    idResponsavel   INT AUTO_INCREMENT PRIMARY KEY,
    NomeResp        VARCHAR(100) NOT NULL,
    CpfResp         VARCHAR(11) UNIQUE,            
    TelefoneResp    VARCHAR(13),
    EmailResp       VARCHAR(100),
    CepResp         VARCHAR(8),
    EnderecoResp    VARCHAR(200),
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_cpf_resp CHECK (CpfResp IS NULL OR CpfResp REGEXP '^[0-9]{11}$')   
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- alunoresponsavel
-- ---------------------------------------------------------
CREATE TABLE alunoresponsavel (
    Aluno_idAluno             INT NOT NULL,
    Responsavel_idResponsavel INT NOT NULL,
    TipoResponsavel           ENUM('Pai','Mae','ResponsavelLegal','Outro') NOT NULL,
    ResponsavelFinanceiro     TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (Aluno_idAluno, Responsavel_idResponsavel),
    CONSTRAINT fk_ar_aluno
        FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno)
        ON DELETE CASCADE ON UPDATE CASCADE,     
    CONSTRAINT fk_ar_responsavel
        FOREIGN KEY (Responsavel_idResponsavel) REFERENCES responsavel(idResponsavel)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;


DELIMITER $$
CREATE TRIGGER trg_ar_financeiro_unico_ins
BEFORE INSERT ON alunoresponsavel
FOR EACH ROW
BEGIN
    IF NEW.ResponsavelFinanceiro = 1 THEN
        IF EXISTS (
            SELECT 1 FROM alunoresponsavel
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND ResponsavelFinanceiro = 1
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Aluno já possui um responsável financeiro cadastrado.';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_ar_financeiro_unico_upd
BEFORE UPDATE ON alunoresponsavel
FOR EACH ROW
BEGIN
    IF NEW.ResponsavelFinanceiro = 1 THEN
        IF EXISTS (
            SELECT 1 FROM alunoresponsavel
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND ResponsavelFinanceiro = 1
              AND Responsavel_idResponsavel <> NEW.Responsavel_idResponsavel
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Aluno já possui um responsável financeiro cadastrado.';
        END IF;
    END IF;
END$$
DELIMITER ;

-- ---------------------------------------------------------
-- matricula
-- ---------------------------------------------------------
CREATE TABLE matricula (
    idMatricula     INT AUTO_INCREMENT PRIMARY KEY,
    Aluno_idAluno   INT NOT NULL,
    Turma_idTurma   INT NOT NULL,
    DataMatricula   DATE NOT NULL,
    Situacao        ENUM('Ativa','Cancelada','Transferida','Concluida') NOT NULL DEFAULT 'Ativa',
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_matricula_aluno
        FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_matricula_turma
        FOREIGN KEY (Turma_idTurma) REFERENCES turma(idTurma)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_matricula_aluno_situacao ON matricula (Aluno_idAluno, Situacao); 


DELIMITER $$
CREATE TRIGGER trg_matricula_unica_ativa_ins
BEFORE INSERT ON matricula
FOR EACH ROW
BEGIN
    IF NEW.Situacao = 'Ativa' THEN
        IF EXISTS (
            SELECT 1 FROM matricula
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND Situacao = 'Ativa'
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Aluno já possui uma matrícula ativa.';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_matricula_unica_ativa_upd
BEFORE UPDATE ON matricula
FOR EACH ROW
BEGIN
    IF NEW.Situacao = 'Ativa' THEN
        IF EXISTS (
            SELECT 1 FROM matricula
            WHERE Aluno_idAluno = NEW.Aluno_idAluno
              AND Situacao = 'Ativa'
              AND idMatricula <> NEW.idMatricula
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Aluno já possui uma matrícula ativa.';
        END IF;
    END IF;
END$$
DELIMITER ;

-- ---------------------------------------------------------
-- professor
-- ---------------------------------------------------------
CREATE TABLE professor (
    idProfessor     INT AUTO_INCREMENT PRIMARY KEY,
    NomeProf        VARCHAR(100) NOT NULL,
    CpfProf         VARCHAR(11) UNIQUE,          
    TelefoneProf    VARCHAR(13),
    EmailProf       VARCHAR(100),
    CepProf         VARCHAR(8),
    EnderecoProf    VARCHAR(200),
    Situacao        ENUM('Ativo','Inativo') NOT NULL DEFAULT 'Ativo',
    Escola_idEscola INT NOT NULL,
    CriadoEm        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AtualizadoEm    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_cpf_prof CHECK (CpfProf IS NULL OR CpfProf REGEXP '^[0-9]{11}$'),  
    CONSTRAINT fk_professor_escola
        FOREIGN KEY (Escola_idEscola) REFERENCES escola(idEscola)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- materia
-- ---------------------------------------------------------
CREATE TABLE materia (
    idMateria       INT AUTO_INCREMENT PRIMARY KEY,
    NomeMateria     VARCHAR(80) NOT NULL,
    CargaHoraria    INT UNSIGNED,                -- OTIMIZADO: elimina negativos por tipo
    CONSTRAINT chk_materia_carga CHECK (CargaHoraria IS NULL OR CargaHoraria > 0) -- OTIMIZADO
) ENGINE=InnoDB;


CREATE TABLE grade_curricular (
    idGrade               INT AUTO_INCREMENT PRIMARY KEY,
    Turma_idTurma         INT NOT NULL,
    Materia_idMateria     INT NOT NULL,
    Professor_idProfessor INT NOT NULL,
    CONSTRAINT fk_grade_turma
        FOREIGN KEY (Turma_idTurma) REFERENCES turma(idTurma)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_grade_materia
        FOREIGN KEY (Materia_idMateria) REFERENCES materia(idMateria)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_grade_professor
        FOREIGN KEY (Professor_idProfessor) REFERENCES professor(idProfessor)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uq_turma_materia (Turma_idTurma, Materia_idMateria)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- avaliacao
-- ---------------------------------------------------------
CREATE TABLE avaliacao (
    idAvaliacao       INT AUTO_INCREMENT PRIMARY KEY,
    Grade_idGrade     INT NOT NULL,
    Periodo_idPeriodo INT NOT NULL,
    Tipo              ENUM('Prova','Trabalho','Projeto','Recuperacao') NOT NULL,
    NomeAvaliacao     VARCHAR(100) NOT NULL,
    DataAvaliacao     DATE NOT NULL,
    Peso              DECIMAL(4,2) NOT NULL DEFAULT 1.00,
    CONSTRAINT chk_avaliacao_peso CHECK (Peso > 0),   -- OTIMIZADO: evita divisão por zero na média
    CONSTRAINT fk_avaliacao_grade
        FOREIGN KEY (Grade_idGrade) REFERENCES grade_curricular(idGrade)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_avaliacao_periodo
        FOREIGN KEY (Periodo_idPeriodo) REFERENCES periodo(idPeriodo)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_avaliacao_grade_periodo ON avaliacao (Grade_idGrade, Periodo_idPeriodo); -- OTIMIZADO: acelera a view de média

-- ---------------------------------------------------------
-- nota
-- ---------------------------------------------------------
CREATE TABLE nota (
    idNota                INT AUTO_INCREMENT PRIMARY KEY,
    Avaliacao_idAvaliacao INT NOT NULL,
    Aluno_idAluno         INT NOT NULL,
    ValorNota             DECIMAL(4,2) NOT NULL,
    CONSTRAINT chk_nota_valor CHECK (ValorNota BETWEEN 0 AND 10), 
    CONSTRAINT fk_nota_avaliacao
        FOREIGN KEY (Avaliacao_idAvaliacao) REFERENCES avaliacao(idAvaliacao)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_nota_aluno
        FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uq_nota_avaliacao_aluno (Avaliacao_idAvaliacao, Aluno_idAluno)
) ENGINE=InnoDB;

CREATE INDEX idx_nota_aluno ON nota (Aluno_idAluno); 

-- ---------------------------------------------------------
-- frequencia
-- ---------------------------------------------------------
CREATE TABLE frequencia (
    idFrequencia    INT AUTO_INCREMENT PRIMARY KEY,
    Grade_idGrade   INT NOT NULL,
    Aluno_idAluno   INT NOT NULL,
    DataFrequencia  DATE NOT NULL,
    Situacao        ENUM('Presente','Falta','FaltaJustificada') NOT NULL,
    CONSTRAINT fk_frequencia_grade
        FOREIGN KEY (Grade_idGrade) REFERENCES grade_curricular(idGrade)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_frequencia_aluno
        FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uq_freq_aluno_grade_data (Grade_idGrade, Aluno_idAluno, DataFrequencia)
) ENGINE=InnoDB;

CREATE INDEX idx_frequencia_aluno_data ON frequencia (Aluno_idAluno, DataFrequencia); 

-- ---------------------------------------------------------
-- boletim
-- ---------------------------------------------------------
CREATE TABLE boletim (
    idBoletim         INT AUTO_INCREMENT PRIMARY KEY,
    Aluno_idAluno     INT NOT NULL,
    Periodo_idPeriodo INT NOT NULL,
    Materia_idMateria INT NOT NULL,
    MediaFinal        DECIMAL(4,2) NOT NULL,
    Situacao          ENUM('Aberto','Fechado') NOT NULL DEFAULT 'Aberto',
    CONSTRAINT fk_boletim_aluno
        FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_boletim_periodo
        FOREIGN KEY (Periodo_idPeriodo) REFERENCES periodo(idPeriodo)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_boletim_materia
        FOREIGN KEY (Materia_idMateria) REFERENCES materia(idMateria)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uq_boletim_aluno_periodo_materia (Aluno_idAluno, Periodo_idPeriodo, Materia_idMateria)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- boleto
-- ---------------------------------------------------------
CREATE TABLE boleto (
    idBoleto         INT AUTO_INCREMENT PRIMARY KEY,
    NumeroBoleto     VARCHAR(50) NOT NULL UNIQUE,   
    Aluno_idAluno    INT NOT NULL,
    Competencia      CHAR(7) NOT NULL,
    ValorMensalidade DECIMAL(10,2) NOT NULL,
    DataVencimento   DATE NOT NULL,
    DataPagamento    DATE,
    Situacao         ENUM('Pendente','Pago','Atrasado','Cancelado') NOT NULL DEFAULT 'Pendente',
    CONSTRAINT chk_boleto_competencia CHECK (Competencia REGEXP '^[0-9]{4}-(0[1-9]|1[0-2])$'), 
    CONSTRAINT chk_boleto_valor CHECK (ValorMensalidade > 0),   
    CONSTRAINT chk_boleto_pagamento CHECK (                      
        (Situacao = 'Pago' AND DataPagamento IS NOT NULL) OR (Situacao <> 'Pago')
    ),
    CONSTRAINT fk_boleto_aluno
        FOREIGN KEY (Aluno_idAluno) REFERENCES aluno(idAluno)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

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
GROUP BY
    n.Aluno_idAluno,
    a.Periodo_idPeriodo,
    g.Materia_idMateria;

USE CAcademic;

SELECT * FROM escola;
SELECT * FROM periodo;
SELECT * FROM materia;
SELECT * FROM responsavel;
SELECT * FROM aluno;
SELECT * FROM turma;
SELECT * FROM professor;
SELECT * FROM matricula;
SELECT * FROM alunoresponsavel;
SELECT * FROM grade_curricular;
SELECT * FROM avaliacao;
SELECT * FROM nota;
SELECT * FROM frequencia;
SELECT * FROM boletim;
SELECT * FROM boleto;

SELECT * FROM vw_aluno_escola_atual;
SELECT * FROM vw_aluno_responsavel_financeiro;
SELECT * FROM vw_aluno_media_dinamica;