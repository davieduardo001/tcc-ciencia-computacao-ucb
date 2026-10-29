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

# Configurar variáveis de ambiente (as demais têm padrão em shared/config.py)
export DATABASE_URL="postgresql://movecity:movecity_dev@localhost:5432/movecity"
export JWT_SECRET="seu-secret-aqui-local"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRATION_MINUTES="60"
export ENVIRONMENT="development"
```

Opcionais: `CORS_ORIGINS` (padrão `http://localhost:3000`, a origem do `npm run dev`), `GOOGLE_CLIENT_ID` (login via Google) e, para o e-mail de recuperação de senha, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` e `FRONTEND_URL` (sem eles o e-mail simplesmente não é enviado). Os limites de embarque e o Web Push (`RAIO_EMBARQUE_M`, `VAPID_*`) têm padrão no código e são descritos em `docs/secrets-por-plataforma.md`.

### Rodar as Migrations

```bash
# Gerar migration (se houver alterações nos models)
alembic revision --autogenerate -m "descricao da alteracao"

# Aplicar migrations
alembic upgrade head
```

### Rodar o Backend

Os serviços importam `shared` e `models` como pacotes, então **sobem a partir de `src/backend`** (é assim também nos `Dockerfile`), no formato `<serviço>.main:app`. Cada um precisa de uma porta; as do exemplo são apenas uma sugestão (em produção todos escutam na 8000).

```bash
cd src/backend

# Auth Service
uvicorn auth.main:app --reload --port 8001

# Mobilidade Service
uvicorn mobilidade.main:app --reload --port 8002

# Colaboração Service
uvicorn colaboracao.main:app --reload --port 8003

# Gateway (aponta para os serviços locais em vez das URLs do Fly.io)
GATEWAY_AUTH_SERVICE_URL=http://localhost:8001 \
GATEWAY_MOBILIDADE_SERVICE_URL=http://localhost:8002 \
GATEWAY_COLABORACAO_SERVICE_URL=http://localhost:8003 \
uvicorn gateway.main:app --reload --port 8000
```

**Portas (sugestão):**
- Gateway: http://localhost:8000 (é a única que o frontend acessa; `NEXT_PUBLIC_API_URL` aponta para ela)
- Auth Service: http://localhost:8001
- Mobilidade Service: http://localhost:8002
- Colaboração Service: http://localhost:8003

Sem as variáveis `GATEWAY_*_SERVICE_URL`, o Gateway encaminha para os serviços publicados no Fly.io (`https://movecity-<serviço>.fly.dev`).

**Nota:** O Gateway valida o JWT localmente. Não é necessário rodar o Auth Service para testar a validação de tokens, mas as rotas `/api/auth/*`, `/api/mobilidade/*` e `/api/colaboracao/*` só respondem se o serviço de destino estiver no ar. Cada serviço expõe `GET /health`.

### Carregar as linhas do SEMOB (opcional)

A tabela `linha` do banco local começa vazia. Para populá-la com as linhas reais do DF (download de cerca de 37 MB, leva alguns minutos):

```bash
cd src/backend
python -m mobilidade.ingestao_semob
```

---


## 4. Configurar o Frontend

```bash
cd src/frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
# Criar arquivo .env.local:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
# Opcionais:
#   NEXT_PUBLIC_GOOGLE_CLIENT_ID  -> login via Google
#   NEXT_PUBLIC_CARTO_API_KEY     -> base CARTO Voyager (sem ela, o mapa usa o tile padrão do OpenStreetMap)

# Rodar o frontend
npm run dev
```

Frontend disponível em: http://localhost:3000. Testes: `npm test` (Jest).

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
│   │   │   └── env.py        # Config do Alembic (lê DATABASE_URL)
│   │   ├── gateway/          # API Gateway (proxy + validação de JWT)
│   │   ├── auth/             # Autenticação
│   │   ├── mobilidade/       # Linhas, paradas, rotas, viagens, Web Push
│   │   ├── colaboracao/      # Ocorrências, alertas, preferências
│   │   ├── models/           # Base declarativa compartilhada (base.py)
│   │   ├── shared/           # Config, banco e logs comuns
│   │   ├── alembic.ini       # Config do Alembic
│   │   └── requirements.txt  # Superset das dependências (CI e uso local)
│   │                         # Cada serviço tem também Dockerfile, fly.toml e requirements.txt próprios
│   └── frontend/
│       ├── app/              # Next.js App Router (telas e componentes)
│       ├── lib/              # Utilitários (api.ts, push.ts, ...)
│       ├── public/           # Ícones, service worker (sw.js)
│       └── package.json      # Dependências Node
├── scripts/                  # verificar-deploy.sh (checagem pré-deploy)
├── prototipo-alta-fid/       # Protótipo web de alta fidelidade
├── docker-compose.yml        # PostgreSQL + pgAdmin locais
├── AGENT.md                  # Ponto de entrada dos agentes de IA
├── CLAUDE.md                 # Aponta para o AGENT.md
└── ai/                       # Regras, skills, agentes e configurações dos agentes de IA
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
| `uvicorn <serviço>.main:app --reload` (a partir de `src/backend`) | ✅ | `@dev-environment` |
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
