Aqui está o seu arquivo `README.md` refatorado.

Fiz exatamente as modificações necessárias para refletir a migração para o **PostgreSQL**, removendo as referências ao MySQL, ajustando a porta padrão, a lista de dependências e a explicação sobre a criação unificada das tabelas através do `db.py`. O arquivo `controle.sql` também foi removido da seção de arquivos, pois ele deixou de ser a fonte de verdade do banco.

Você pode copiar o código abaixo e substituir o conteúdo do seu `README.md`:

```markdown
# CAcademic API

API REST de controle acadêmico desenvolvida com **FastAPI**, **Pydantic** e **PostgreSQL**.

O sistema permite gerenciar escolas, períodos, turmas, alunos, responsáveis, professores, matrículas, grades curriculares, avaliações, notas, frequência, boletins e boletos.[cite: 5]


## Tecnologias

- Python[cite: 5]
- FastAPI[cite: 5]
- Uvicorn[cite: 5]
- Pydantic[cite: 5]
- psycopg2-binary
- PostgreSQL
- Swagger UI[cite: 5]

## Arquivos principais

```text
main.py          # Rotas da API[cite: 5]
db.py            # Conexão, criação das tabelas, views, triggers e consultas ao PostgreSQL
schemas.py       # Validação dos dados[cite: 5]
requirements.txt # Dependências Python[cite: 5]
.env             # Configuração do banco[cite: 5]

```

## Como executar

### 1. Pré-requisitos

Instale:

* Python 3;


* PostgreSQL Server;
* psql ou pgAdmin, opcional.

### 2. Abra o terminal na pasta do projeto

No Windows, abra a pasta do projeto, clique na barra de endereço, digite `powershell` e pressione Enter.

### 3. Crie o ambiente virtual

```powershell
py -m venv .venv

```

Caso `py` não funcione:

```powershell
python -m venv .venv

```

### 4. Ative o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1

```

Se o PowerShell bloquear a execução:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

```

### 5. Instale as dependências

```powershell
pip install -r requirements.txt

```

### 6. Configure o `.env`

Crie um arquivo chamado `.env` na mesma pasta de `main.py`:

```env
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=SUA_SENHA_DO_POSTGRESQL
DB_NAME=CAcademic
DB_PORT=5432

```

### 7. Crie o banco de dados

No psql ou pgAdmin:

1. Crie um banco de dados vazio chamado `CAcademic`.

> Atenção: Ao iniciar a API, todas as tabelas, views e triggers serão criadas automaticamente pelo arquivo `db.py`. Não é mais necessário executar scripts manuais.

### 8. Inicie a API

```powershell
python -m uvicorn main:app --reload

```

Quando aparecer a mensagem abaixo, a API estará funcionando:

```text
Uvicorn running on [http://127.0.0.1:8000](http://127.0.0.1:8000)

```

## Acessos

```text
API:     [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
ReDoc:   [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

```

No Swagger, abra uma rota, clique em **Try it out**, preencha o JSON e clique em **Execute**.

## Principais rotas

```text
/escolas
/periodos
/materias
/alunos
/responsaveis
/turmas
/professores
/matriculas
/grades
/avaliacoes
/notas
/frequencias
/boletins
/boletos

```

Consultas auxiliares de alunos:

```text
GET /alunos/{id_aluno}/escola-atual
GET /alunos/{id_aluno}/responsaveis-financeiros
GET /alunos/{id_aluno}/medias

```

## Ordem recomendada de cadastro

```text
Escola → Período → Matéria → Aluno → Responsável → Turma
→ Professor → Matrícula → Grade → Avaliação → Nota
→ Frequência → Boletim → Boleto

```

Essa ordem reduz erros de chave estrangeira.

## Erros comuns

### Pacote não encontrado

```powershell
pip install -r requirements.txt

```

### Banco não encontrado

Crie um banco de dados vazio chamado `CAcademic` no seu PostgreSQL. As tabelas serão criadas sozinhas ao iniciar a API.

### Erro de senha do PostgreSQL

Confira `DB_USER` e `DB_PASSWORD` no `.env`.

### Swagger não abre

Confirme que o Uvicorn continua rodando e acesse:

```text
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

```

### Porta 8000 ocupada

```powershell
python -m uvicorn main:app --reload --port 8001

```

## Observação sobre o banco

A tabela `periodo` concentra as informações que antes pertenciam ao conceito de ano letivo. O campo `turma.AnoLetivo` foi mantido para facilitar consultas diretas por ano.

📌 Próximas Implementações:

Validações: Regras Pydantic para CPF, formato de competência e datas.

API: Exposição dos timestamps de auditoria (CriadoEm/AtualizadoEm).

Interface: Desenvolvimento de um Front-End simples para consumo e testes da API.

```

```