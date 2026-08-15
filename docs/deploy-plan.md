# Plano de Deploy — Microserviços Fly.io + Neon

**Data:** 2026-08-15
**Issue:** #35
**Branch:** feat/issue-35-hello-world

---

## Arquitetura

```
[Frontend - Vercel]  movecity-frontend.vercel.app
    │
    ▼
[Gateway - Fly.io]   movecity-gateway.fly.dev  ← único público
    │  httpx proxy + JWT validation
    │
    ├──► movecity-auth.internal:8001         (schema: auth)
    ├──► movecity-mobilidade.internal:8002   (schema: mobilidade)
    └──► movecity-colaboracao.internal:8003  (schema: colaboracao)
              │
              ▼
         [Neon PostgreSQL]  (4 schemas no mesmo banco)
```

---

## Apps Fly.io

| App | Tipo | Porta | Região | Schema |
|-----|------|-------|--------|--------|
| `movecity-gateway` | público | 8000 | gru | gateway |
| `movecity-auth` | interno | 8001 | gru | auth |
| `movecity-mobilidade` | interno | 8002 | gru | mobilidade |
| `movecity-colaboracao` | interno | 8003 | gru | colaboracao |

---

## Schemas PostgreSQL

| Schema | Tabela | Serviço |
|--------|--------|---------|
| `auth` | `test_user` | auth |
| `mobilidade` | `test_linha` | mobilidade |
| `colaboracao` | `test_reporte` | colaboracao |
| `gateway` | `test_log` | gateway |

---

## Secrets por App

| Secret | Gateway | Auth | Mobilidade | Colaboracao |
|--------|---------|------|------------|-------------|
| `DATABASE_URL` | ❌ | ✅ | ✅ | ✅ |
| `JWT_SECRET` | ✅ | ✅ | ❌ | ❌ |
| `JWT_ALGORITHM` | ✅ | ✅ | ❌ | ❌ |
| `JWT_EXPIRATION_MINUTES` | ✅ | ✅ | ❌ | ❌ |
| `ENVIRONMENT` | ✅ | ✅ | ✅ | ✅ |
| `SERVICE_NAME` | gateway | auth | mobilidade | colaboracao |

---

## Estrutura de Código

```
src/backend/
├── shared/
│   ├── __init__.py
│   ├── config.py          # Settings compartilhadas
│   ├── database.py        # Engine + session factory
│   └── models/
│       ├── __init__.py
│       ├── base.py        # DeclarativeBase
│       ├── auth.py        # TestUser (schema="auth")
│       ├── mobilidade.py  # TestLinha (schema="mobilidade")
│       ├── colaboracao.py # TestReporte (schema="colaboracao")
│       └── gateway.py     # TestLog (schema="gateway")
│
├── gateway/
│   ├── Dockerfile
│   ├── fly.toml
│   ├── requirements.txt
│   ├── main.py
│   └── tests/
│
├── auth/
│   ├── Dockerfile
│   ├── fly.toml
│   ├── requirements.txt
│   ├── main.py
│   └── tests/
│
├── mobilidade/
│   ├── Dockerfile
│   ├── fly.toml
│   ├── requirements.txt
│   ├── main.py
│   └── tests/
│
├── colaboracao/
│   ├── Dockerfile
│   ├── fly.toml
│   ├── requirements.txt
│   ├── main.py
│   └── tests/
│
└── docker-compose.yml     # Para rodar localmente
```

---

## Comandos de Deploy

```bash
# 1. Deletar app antigo
flyctl apps destroy movecity-backend --yes

# 2. Criar apps novos
flyctl apps create movecity-gateway
flyctl apps create movecity-auth
flyctl apps create movecity-mobilidade
flyctl apps create movecity-colaboracao

# 3. Configurar secrets (gateway)
flyctl secrets set JWT_SECRET=... JWT_ALGORITHM=... JWT_EXPIRATION_MINUTES=... ENVIRONMENT=production SERVICE_NAME=gateway --app movecity-gateway

# 4. Configurar secrets (auth)
flyctl secrets set DATABASE_URL=... JWT_SECRET=... JWT_ALGORITHM=... JWT_EXPIRATION_MINUTES=... ENVIRONMENT=production SERVICE_NAME=auth --app movecity-auth

# 5. Configurar secrets (mobilidade)
flyctl secrets set DATABASE_URL=... ENVIRONMENT=production SERVICE_NAME=mobilidade --app movecity-mobilidade

# 6. Configurar secrets (colaboracao)
flyctl secrets set DATABASE_URL=... ENVIRONMENT=production SERVICE_NAME=colaboracao --app movecity-colaboracao

# 7. Deploy (serviços primeiro, gateway depois)
cd src/backend/auth && flyctl deploy --app movecity-auth
cd src/backend/mobilidade && flyctl deploy --app movecity-mobilidade
cd src/backend/colaboracao && flyctl deploy --app movecity-colaboracao
cd src/backend/gateway && flyctl deploy --app movecity-gateway

# 8. Rodar migrations
flyctl ssh console --app movecity-auth -C "alembic upgrade head"
flyctl ssh console --app movecity-mobilidade -C "alembic upgrade head"
flyctl ssh console --app movecity-colaboracao -C "alembic upgrade head"
flyctl ssh console --app movecity-gateway -C "alembic upgrade head"
```

---

## Verificação Final

```bash
curl https://movecity-gateway.fly.dev/health
curl https://movecity-gateway.fly.dev/auth/hello
curl https://movecity-gateway.fly.dev/mobilidade/hello
curl https://movecity-gateway.fly.dev/colaboracao/hello
```

---

## Documentação Atualizada

- `AGENT.md`: Stack → Fly.io (4 microservices), não Render
- `docs/setup-local.md`: Instruções para rodar 4 serviços localmente
- `docs/deploy-plan.md`: Este arquivo
