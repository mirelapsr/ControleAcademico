-- =========================================================
-- BANCO DE DADOS
-- Observação: Execute este CREATE DATABASE separadamente se o banco não existir.
-- Após criar, mude a conexão do DataGrip para apontar para o CAcademic.
-- CREATE DATABASE "CAcademic";
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
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------
-- escola
-- ---------------------------------------------------------
CREATE TABLE escola (
    id_escola        SERIAL PRIMARY KEY,
    nome_escola      VARCHAR(150) NOT NULL,
    codigo_inep      VARCHAR(8)  UNIQUE,
    cnpj             VARCHAR(14) UNIQUE,
    endereco_escola  VARCHAR(200),
    telefone_escola  VARCHAR(13),
    email_escola     VARCHAR(100),
    criado_em        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_escola_upd BEFORE UPDATE ON escola
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- periodo
-- ---------------------------------------------------------
CREATE TABLE periodo (
    id_periodo       SERIAL PRIMARY KEY,
    ano              SMALLINT NOT NULL,
    nome_periodo     VARCHAR(30) NOT NULL,
    data_inicio      DATE NOT NULL,
    data_fim         DATE NOT NULL,
    situacao         VARCHAR(50) NOT NULL DEFAULT 'Ativo',
    criado_em        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_periodo_situacao CHECK (situacao IN ('Ativo','Encerrado')),
    CONSTRAINT chk_periodo_datas CHECK (data_fim > data_inicio)
);

CREATE TRIGGER trg_periodo_upd BEFORE UPDATE ON periodo
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- turma
-- ---------------------------------------------------------
CREATE TABLE turma (
    id_turma             SERIAL PRIMARY KEY,
    nome_turma           VARCHAR(30) NOT NULL,
    serie                VARCHAR(45),
    turno                VARCHAR(50) NOT NULL,
    capacidade           INTEGER,
    escola_id_escola     INTEGER NOT NULL,
    ano_letivo           SMALLINT NOT NULL,
    criado_em            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_turma_turno CHECK (turno IN ('Manha','Tarde','Noite','Integral')),
    CONSTRAINT chk_turma_capacidade CHECK (capacidade IS NULL OR capacidade > 0),
    CONSTRAINT fk_turma_escola FOREIGN KEY (escola_id_escola) REFERENCES escola(id_escola) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_turma_escola_ano ON turma (escola_id_escola, ano_letivo);

CREATE TRIGGER trg_turma_upd BEFORE UPDATE ON turma
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- aluno
-- ---------------------------------------------------------
CREATE TABLE aluno (
    id_aluno           SERIAL PRIMARY KEY,
    numero_matricula   VARCHAR(20) NOT NULL UNIQUE,
    nome_aluno         VARCHAR(100) NOT NULL,
    data_nascimento    DATE NOT NULL,
    cpf_aluno          VARCHAR(11) UNIQUE,
    telefone_aluno     VARCHAR(13),
    email_aluno        VARCHAR(100),
    cep_aluno          VARCHAR(8),
    endereco_aluno     VARCHAR(200),
    situacao           VARCHAR(50) NOT NULL DEFAULT 'Ativo',
    criado_em          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_aluno_situacao CHECK (situacao IN ('Ativo','Inativo','Transferido')),
    CONSTRAINT chk_cpf_aluno CHECK (cpf_aluno IS NULL OR cpf_aluno ~ '^[0-9]{11}$')
);

CREATE TRIGGER trg_aluno_upd BEFORE UPDATE ON aluno
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- responsavel
-- ---------------------------------------------------------
CREATE TABLE responsavel (
    id_responsavel   SERIAL PRIMARY KEY,
    nome_resp        VARCHAR(100) NOT NULL,
    cpf_resp         VARCHAR(11) UNIQUE,
    telefone_resp    VARCHAR(13),
    email_resp       VARCHAR(100),
    cep_resp         VARCHAR(8),
    endereco_resp    VARCHAR(200),
    criado_em        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cpf_resp CHECK (cpf_resp IS NULL OR cpf_resp ~ '^[0-9]{11}$')
);

CREATE TRIGGER trg_responsavel_upd BEFORE UPDATE ON responsavel
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- alunoresponsavel
-- ---------------------------------------------------------
CREATE TABLE alunoresponsavel (
    aluno_id_aluno               INTEGER NOT NULL,
    responsavel_id_responsavel   INTEGER NOT NULL,
    tipo_responsavel             VARCHAR(50) NOT NULL,
    responsavel_financeiro       BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (aluno_id_aluno, responsavel_id_responsavel),
    CONSTRAINT chk_ar_tipo CHECK (tipo_responsavel IN ('Pai','Mae','ResponsavelLegal','Outro')),
    CONSTRAINT fk_ar_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ar_responsavel FOREIGN KEY (responsavel_id_responsavel) REFERENCES responsavel(id_responsavel) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Triggers de Regras de Negócio: Responsável Financeiro Único
CREATE OR REPLACE FUNCTION func_ar_financeiro_unico_ins() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.responsavel_financeiro = TRUE THEN
        IF EXISTS (
            SELECT 1 FROM alunoresponsavel
            WHERE aluno_id_aluno = NEW.aluno_id_aluno
              AND responsavel_financeiro = TRUE
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
    IF NEW.responsavel_financeiro = TRUE THEN
        IF EXISTS (
            SELECT 1 FROM alunoresponsavel
            WHERE aluno_id_aluno = NEW.aluno_id_aluno
              AND responsavel_financeiro = TRUE
              AND responsavel_id_responsavel <> NEW.responsavel_id_responsavel
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
    id_matricula     SERIAL PRIMARY KEY,
    aluno_id_aluno   INTEGER NOT NULL,
    turma_id_turma   INTEGER NOT NULL,
    data_matricula   DATE NOT NULL,
    situacao         VARCHAR(50) NOT NULL DEFAULT 'Ativa',
    criado_em        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_matricula_situacao CHECK (situacao IN ('Ativa','Cancelada','Transferida','Concluida')),
    CONSTRAINT fk_matricula_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_matricula_turma FOREIGN KEY (turma_id_turma) REFERENCES turma(id_turma) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_matricula_aluno_situacao ON matricula (aluno_id_aluno, situacao);

CREATE TRIGGER trg_matricula_upd BEFORE UPDATE ON matricula
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- Triggers de Regras de Negócio: Matrícula Única Ativa
CREATE OR REPLACE FUNCTION func_matricula_unica_ativa_ins() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.situacao = 'Ativa' THEN
        IF EXISTS (
            SELECT 1 FROM matricula
            WHERE aluno_id_aluno = NEW.aluno_id_aluno
              AND situacao = 'Ativa'
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
    IF NEW.situacao = 'Ativa' THEN
        IF EXISTS (
            SELECT 1 FROM matricula
            WHERE aluno_id_aluno = NEW.aluno_id_aluno
              AND situacao = 'Ativa'
              AND id_matricula <> NEW.id_matricula
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
    id_professor     SERIAL PRIMARY KEY,
    nome_prof        VARCHAR(100) NOT NULL,
    cpf_prof         VARCHAR(11) UNIQUE,
    telefone_prof    VARCHAR(13),
    email_prof       VARCHAR(100),
    cep_prof         VARCHAR(8),
    endereco_prof    VARCHAR(200),
    situacao         VARCHAR(50) NOT NULL DEFAULT 'Ativo',
    escola_id_escola INTEGER NOT NULL,
    criado_em        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_prof_situacao CHECK (situacao IN ('Ativo','Inativo')),
    CONSTRAINT chk_cpf_prof CHECK (cpf_prof IS NULL OR cpf_prof ~ '^[0-9]{11}$'),
    CONSTRAINT fk_professor_escola FOREIGN KEY (escola_id_escola) REFERENCES escola(id_escola) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TRIGGER trg_professor_upd BEFORE UPDATE ON professor
FOR EACH ROW EXECUTE FUNCTION atualiza_timestamp();

-- ---------------------------------------------------------
-- materia
-- ---------------------------------------------------------
CREATE TABLE materia (
    id_materia      SERIAL PRIMARY KEY,
    nome_materia    VARCHAR(80) NOT NULL,
    carga_horaria   INTEGER,
    CONSTRAINT uq_materia_nome UNIQUE (nome_materia),
    CONSTRAINT chk_materia_carga CHECK (carga_horaria IS NULL OR carga_horaria > 0)
);

-- ---------------------------------------------------------
-- grade_curricular
-- ---------------------------------------------------------
CREATE TABLE grade_curricular (
    id_grade                SERIAL PRIMARY KEY,
    turma_id_turma          INTEGER NOT NULL,
    materia_id_materia      INTEGER NOT NULL,
    professor_id_professor  INTEGER NOT NULL,
    CONSTRAINT fk_grade_turma FOREIGN KEY (turma_id_turma) REFERENCES turma(id_turma) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_grade_materia FOREIGN KEY (materia_id_materia) REFERENCES materia(id_materia) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_grade_professor FOREIGN KEY (professor_id_professor) REFERENCES professor(id_professor) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_turma_materia UNIQUE (turma_id_turma, materia_id_materia)
);

-- ---------------------------------------------------------
-- avaliacao
-- ---------------------------------------------------------
CREATE TABLE avaliacao (
    id_avaliacao        SERIAL PRIMARY KEY,
    grade_id_grade      INTEGER NOT NULL,
    periodo_id_periodo  INTEGER NOT NULL,
    tipo                VARCHAR(50) NOT NULL,
    nome_avaliacao      VARCHAR(100) NOT NULL,
    data_avaliacao      DATE NOT NULL,
    peso                DECIMAL(4,2) NOT NULL DEFAULT 1.00,
    CONSTRAINT chk_avaliacao_tipo CHECK (tipo IN ('Prova','Trabalho','Projeto','Recuperacao')),
    CONSTRAINT chk_avaliacao_peso CHECK (peso > 0),
    CONSTRAINT fk_avaliacao_grade FOREIGN KEY (grade_id_grade) REFERENCES grade_curricular(id_grade) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_avaliacao_periodo FOREIGN KEY (periodo_id_periodo) REFERENCES periodo(id_periodo) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_avaliacao_grade_periodo ON avaliacao (grade_id_grade, periodo_id_periodo);

-- ---------------------------------------------------------
-- nota
-- ---------------------------------------------------------
CREATE TABLE nota (
    id_nota                 SERIAL PRIMARY KEY,
    avaliacao_id_avaliacao  INTEGER NOT NULL,
    aluno_id_aluno          INTEGER NOT NULL,
    valor_nota              DECIMAL(4,2) NOT NULL,
    CONSTRAINT chk_nota_valor CHECK (valor_nota BETWEEN 0 AND 10),
    CONSTRAINT fk_nota_avaliacao FOREIGN KEY (avaliacao_id_avaliacao) REFERENCES avaliacao(id_avaliacao) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_nota_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_nota_avaliacao_aluno UNIQUE (avaliacao_id_avaliacao, aluno_id_aluno)
);

CREATE INDEX idx_nota_aluno ON nota (aluno_id_aluno);

-- ---------------------------------------------------------
-- frequencia
-- ---------------------------------------------------------
CREATE TABLE frequencia (
    id_frequencia    SERIAL PRIMARY KEY,
    grade_id_grade   INTEGER NOT NULL,
    aluno_id_aluno   INTEGER NOT NULL,
    data_frequencia  DATE NOT NULL,
    situacao         VARCHAR(50) NOT NULL,
    CONSTRAINT chk_freq_situacao CHECK (situacao IN ('Presente','Falta','FaltaJustificada')),
    CONSTRAINT fk_frequencia_grade FOREIGN KEY (grade_id_grade) REFERENCES grade_curricular(id_grade) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_frequencia_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_freq_aluno_grade_data UNIQUE (grade_id_grade, aluno_id_aluno, data_frequencia)
);

CREATE INDEX idx_frequencia_aluno_data ON frequencia (aluno_id_aluno, data_frequencia);

-- ---------------------------------------------------------
-- boletim
-- ---------------------------------------------------------
CREATE TABLE boletim (
    id_boletim          SERIAL PRIMARY KEY,
    aluno_id_aluno      INTEGER NOT NULL,
    periodo_id_periodo  INTEGER NOT NULL,
    materia_id_materia  INTEGER NOT NULL,
    media_final         DECIMAL(4,2) NOT NULL,
    situacao            VARCHAR(50) NOT NULL DEFAULT 'Aberto',
    CONSTRAINT chk_boletim_situacao CHECK (situacao IN ('Aberto','Fechado')),
    CONSTRAINT fk_boletim_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_boletim_periodo FOREIGN KEY (periodo_id_periodo) REFERENCES periodo(id_periodo) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_boletim_materia FOREIGN KEY (materia_id_materia) REFERENCES materia(id_materia) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_boletim_aluno_periodo_materia UNIQUE (aluno_id_aluno, periodo_id_periodo, materia_id_materia)
);

-- ---------------------------------------------------------
-- boleto
-- ---------------------------------------------------------
CREATE TABLE boleto (
    id_boleto          SERIAL PRIMARY KEY,
    numero_boleto      VARCHAR(50) NOT NULL UNIQUE,
    aluno_id_aluno     INTEGER NOT NULL,
    competencia        CHAR(7) NOT NULL,
    valor_mensalidade  DECIMAL(10,2) NOT NULL,
    data_vencimento    DATE NOT NULL,
    data_pagamento     DATE,
    situacao           VARCHAR(50) NOT NULL DEFAULT 'Pendente',
    CONSTRAINT chk_boleto_situacao CHECK (situacao IN ('Pendente','Pago','Atrasado','Cancelado')),
    CONSTRAINT chk_boleto_competencia CHECK (competencia ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    CONSTRAINT chk_boleto_valor CHECK (valor_mensalidade > 0),
    CONSTRAINT chk_boleto_pagamento CHECK (
        (situacao = 'Pago' AND data_pagamento IS NOT NULL) OR (situacao <> 'Pago')
    ),
    CONSTRAINT fk_boleto_aluno FOREIGN KEY (aluno_id_aluno) REFERENCES aluno(id_aluno) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_boleto_situacao_vencimento ON boleto (situacao, data_vencimento);

-- =========================================================
-- Views
-- =========================================================

CREATE OR REPLACE VIEW vw_aluno_escola_atual AS
SELECT
    a.id_aluno,
    e.id_escola,
    e.nome_escola
FROM aluno a
JOIN matricula m ON m.aluno_id_aluno = a.id_aluno AND m.situacao = 'Ativa'
JOIN turma t ON t.id_turma = m.turma_id_turma
JOIN escola e ON e.id_escola = t.escola_id_escola;

CREATE OR REPLACE VIEW vw_aluno_responsavel_financeiro AS
SELECT
    ar.aluno_id_aluno,
    r.id_responsavel,
    r.nome_resp,
    r.email_resp,
    r.telefone_resp
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
GROUP BY
    n.aluno_id_aluno,
    a.periodo_id_periodo,
    g.materia_id_materia;