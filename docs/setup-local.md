# Setup Local — Movecity

Guia passo a passo para rodar o projeto localmente.

---

## Pré-requisitos

| Ferramenta | Versão | Como verificar |
|------------|--------|----------------|
| Git | 2.40+ | `git --version` |
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| Docker | 24+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |

---

## 1. Clonar o Repositório

```bash
git clone https://github.com/davieduardo001/tcc-ciencia-computacao-ucb.git
cd tcc-ciencia-computacao-ucb
```

---

## 2. Subir o Banco de Dados Local

```bash
# Subir PostgreSQL + pgAdmin
docker compose up -d

# Verificar se está rodando
docker compose ps
```

**Credenciais do banco local:**

| Campo | Valor |
|-------|-------|
| Host | `localhost` |
| Port | `5432` |
| User | `movecity` |
| Password | `movecity_dev` |
| Database | `movecity` |

**pgAdmin (interface web):**
- Acesse: http://localhost:5050
- Email: `admin@movecity.com`
- Password: `admin`

---

## 3. Configurar o Backend

```bash
cd src/backend

# Criar virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variável de ambiente
export DATABASE_URL="postgresql://movecity:movecity_dev@localhost:5432/movecity"
export JWT_SECRET="seu-secret-aqui-local"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRATION_MINUTES="60"
export ENVIRONMENT="development"
```

### Rodar as Migrations

```bash
# Gerar migration (se houver alterações nos models)
alembic revision --autogenerate -m "descricao da alteracao"

# Aplicar migrations
alembic upgrade head
```

### Rodar o Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend disponível em: http://localhost:8000

---

## 4. Configurar o Frontend

```bash
cd src/frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
# Criar arquivo .env.local:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_MAP_TILES=https://tile.openstreetmap.org/{z}/{x}/{y}.png" >> .env.local
echo "NEXT_PUBLIC_APP_NAME=Movecity" >> .env.local

# Rodar o frontend
npm run dev
```

Frontend disponível em: http://localhost:3000

---

## 5. Workflow de Desenvolvimento

### Criar uma nova feature

```bash
# 1. Atualizar homolog
git checkout homolog
git pull origin homolog

# 2. Criar branch
git checkout -b feat/issue-[numero]-[nome]

# 3. Desenvolver (backend ou frontend)
# ...

# 4. Se alterou models, gerar migration
cd src/backend
alembic revision --autogenerate -m "feat: descricao"
alembic upgrade head

# 5. Commitar
git add .
git commit -m "feat: descricao"

# 6. Push e PR
git push -u origin feat/issue-[numero]-[nome]
# Abrir PR para homolog
```

### Sincronizar com o banco após pull

```bash
# Após puxar mudanças de branches
cd src/backend
alembic upgrade head
```

---

## 6. Estrutura de Diretórios

```
tcc-ciencia-computacao-ucb/
├── src/
│   ├── backend/
│   │   ├── alembic/           # Migrations do banco
│   │   │   ├── versions/     # Arquivos de migration
│   │   │   └── env.py        # Config do Alembic
│   │   ├── gateway/          # API Gateway
│   │   ├── auth/             # Autenticação
│   │   ├── mobilidade/       # Dados de mobilidade
│   │   ├── colaboracao/      # Reportes crowdsourced
│   │   ├── models/           # Modelos ORM (SQLAlchemy)
│   │   ├── core/             # Config, dependências
│   │   ├── alembic.ini       # Config do Alembic
│   │   ├── requirements.txt  # Dependências Python
│   │   ├── Dockerfile        # Deploy no Fly.io
│   │   └── fly.toml          # Config do Fly.io
│   └── frontend/
│       ├── app/              # Next.js App Router
│       ├── components/       # Componentes React
│       ├── lib/              # Utilitários, hooks
│       └── package.json      # Dependências Node
├── docker-compose.yml        # PostgreSQL local
├── opencode.json             # Config dos agentes
└── .opencode/                # Skills e agentes
```

---

## 7. Troubleshooting

### Erro: "relation does not exist"

```bash
# Rodar migrations
cd src/backend
alembic upgrade head
```

### Erro: "connection refused"

```bash
# Verificar se o Docker está rodando
docker compose ps

# Reiniciar se necessário
docker compose down
docker compose up -d
```

### Erro: "port already in use"

```bash
# Matar processo na porta 5432
lsof -ti:5432 | xargs kill -9

# Ou mudar a porta no docker-compose.yml
```

---

## 8. Usando os Agentes

O opencode possui agentes especializados que podem auxiliar no setup e desenvolvimento.

### Agentes disponíveis

| Agente | Função | Exemplo de uso |
|--------|--------|----------------|
| `@dev-environment` | Infra local (Docker, migrations, deps) | "Sobe o banco e roda as migrations" |
| `@backend` | Código backend (endpoints, models) | "Cria o endpoint de login seguindo o diagrama" |
| `@frontend` | Código frontend (telas, componentes) | "Cria a tela de login com o formulário" |
| `@tester` | Testes unitários | "Roda os testes do serviço de autenticação" |
| `@reviewer` | Review de código (read-only) | "Revise o PR #42" |

### Fluxos típicos

#### Setup inicial do projeto
```
Você: "@dev-environment, sobe o banco, instala as dependências e roda as migrations"

Agente executa:
1. docker compose up -d
2. pip install -r requirements.txt
3. npm install
4. alembic upgrade head

Agente reporta: "Banco rodando na porta 5432. Dependências instaladas. Migrations aplicadas."
```

#### Desenvolver uma feature
```
Você: "@backend, cria o endpoint de login seguindo o diagrama UC10"

Agente executa:
1. Cria o código do endpoint
2. Cria os testes
3. Gera migration (se necessário)
4. Faz commit

Agente reporta: "Endpoint criado em src/backend/auth/routes.py. Testes passando."
```

#### Rodar testes
```
Você: "@tester, roda todos os testes do backend"

Agente executa:
1. cd src/backend && pytest -v

Agente reporta: "12 testes passando. 0 falhas."
```

### Comandos manuais vs agentes

| Comando | Manual | Via agente |
|---------|--------|------------|
| `docker compose up -d` | ✅ | `@dev-environment` |
| `docker compose down` | ✅ | `@dev-environment` |
| `pip install -r requirements.txt` | ✅ | `@dev-environment` |
| `npm install` | ✅ | `@dev-environment` |
| `alembic upgrade head` | ✅ | `@dev-environment` ou `@backend` |
| `alembic revision --autogenerate` | ✅ | `@backend` |
| `uvicorn main:app --reload` | ✅ | `@dev-environment` |
| `pytest -v` | ✅ | `@tester` ou `@backend` |
| `npm test` | ✅ | `@tester` ou `@frontend` |

---

## 9. Comandos Úteis

| Comando | O que faz |
|---------|-----------|
| `docker compose up -d` | Sobe o banco em background |
| `docker compose down` | Para o banco |
| `docker compose logs postgres` | Vê logs do banco |
| `alembic upgrade head` | Aplica todas as migrations |
| `alembic downgrade -1` | Desfaz a última migration |
| `alembic history` | Lista todas as migrations |
| `alembic revision --autogenerate -m "msg"` | Gera migration a partir dos models |
