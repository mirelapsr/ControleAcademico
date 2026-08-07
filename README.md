# CAcademic API

API REST de controle acadêmico desenvolvida com **FastAPI**, **Pydantic** e **MySQL**.

O sistema permite gerenciar escolas, períodos, turmas, alunos, responsáveis, professores, matrículas, grades curriculares, avaliações, notas, frequência, boletins e boletos.


## Tecnologias

- Python
- FastAPI
- Uvicorn
- Pydantic
- PyMySQL
- MySQL
- Swagger UI

## Arquivos principais

```text
main.py          # Rotas da API
db.py            # Conexão e consultas ao MySQL(tabelas simples)
schemas.py       # Validação dos dados
controle.sql     # Desenvolvimento mais recente da estrutura do banco
requirements.txt # Dependências Python
.env             # Configuração do banco
```

## Como executar

### 1. Pré-requisitos

Instale:

- Python 3;
- MySQL Server;
- MySQL Workbench, opcional.

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
DB_USER=root
DB_PASSWORD=SUA_SENHA_DO_MYSQL
DB_NAME=CAcademic
DB_PORT=3306
```

### 7. Crie o banco de dados

No MySQL Workbench:

1. Abra o arquivo `controle.sql`.
2. Execute todo o script.
3. Confirme que o banco `CAcademic` foi criado.

> Atenção: o script usa `DROP TABLE` e apaga os dados existentes quando é executado novamente.

### 8. Inicie a API

```powershell
python -m uvicorn main:app --reload
```

Quando aparecer a mensagem abaixo, a API estará funcionando:

```text
Uvicorn running on http://127.0.0.1:8000
```

## Acessos

```text
API:     http://127.0.0.1:8000/
Swagger: http://127.0.0.1:8000/docs
ReDoc:   http://127.0.0.1:8000/redoc
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

Execute o arquivo `controle.sql` no MySQL Workbench.

### Erro de senha do MySQL

Confira `DB_USER` e `DB_PASSWORD` no `.env`.

### Swagger não abre

Confirme que o Uvicorn continua rodando e acesse:

```text
http://127.0.0.1:8000/docs
```

### Porta 8000 ocupada

```powershell
python -m uvicorn main:app --reload --port 8001
```

## Observação sobre o banco

A tabela `periodo` concentra as informações que antes pertenciam ao conceito de ano letivo. O campo `turma.AnoLetivo` foi mantido para facilitar consultas diretas por ano.


📌 Próximas Implementações:

Backend & Exceções: Tratamento de OperationalError (Triggers e CHECKs do MySQL).

Validações: Regras Pydantic para CPF, formato de competência e datas.

Banco de Dados: Sincronização do script criar_tabelas() com o DDL oficial.

API: Exposição dos timestamps de auditoria (CriadoEm/AtualizadoEm).

Interface: Desenvolvimento de um Front-End simples para consumo e testes da API.