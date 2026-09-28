# Plano de Deploy — Microservices Fly.io + Neon

**Última atualização:** 2026-08-15
**Issue:** #35
**Branches:** `feat/issue-35-hello-world` → `fix/issue-35-split-microservices` → `homolog` → `main`

Este documento descreve o que foi **efetivamente implementado e deployado** para o hello-world da issue #35. Ele substitui a versão inicial do plano (mais ambiciosa, com schemas por serviço e serviços internos) por um retrato fiel do que está rodando em produção hoje, incluindo as simplificações e lacunas conscientes que ficaram para trás.

---

## Arquitetura atual

```
[Frontend - Vercel]  movecity-frontend.vercel.app
    │
    ▼
[Gateway - Fly.io]   movecity-gateway.fly.dev
    │
    ├──► movecity-auth.fly.dev
    ├──► movecity-mobilidade.fly.dev
    └──► movecity-colaboracao.fly.dev
              │
              ▼
         [Neon PostgreSQL]  (schema público único)
```

Os 4 serviços são apps independentes no Fly.io, cada um com seu próprio código, `Dockerfile`, `fly.toml` e `requirements.txt`. Nenhum deles ainda chama o outro (o gateway não faz proxy real — cada endpoint `/hello` é isolado). Todos são públicos.

---

## Apps Fly.io

| App | Porta | Região |
|-----|-------|--------|
| `movecity-gateway` | 8000 | gru |
| `movecity-auth` | 8000 | gru |
| `movecity-mobilidade` | 8000 | gru |
| `movecity-colaboracao` | 8000 | gru |

---

## Banco de dados

Tudo roda no schema `public` do projeto `movecity` no Neon (região `sa-east-1`), sem separação por serviço:

| Tabela | Serviço dono (por convenção) |
|--------|-------------------------------|
| `test_user` | auth |
| `test_linha` | mobilidade |
| `test_reporte` | colaboracao |
| `test_log` | gateway |

Migrations via Alembic, centralizadas em `src/backend/alembic/` — rodadas manualmente contra o Neon, não dentro dos containers do Fly.io.

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

## Estrutura de código

```
src/backend/
├── shared/
│   ├── __init__.py
│   └── config.py          # Settings comuns aos 4 serviços
│
├── gateway/ auth/ mobilidade/ colaboracao/
│   ├── Dockerfile
│   ├── fly.toml
│   ├── requirements.txt
│   ├── main.py
│   ├── routes.py
│   ├── models/             # usados só pelo Alembic, não embarcados na imagem
│   └── tests/
│
├── models/base.py          # DeclarativeBase compartilhado (uso local/Alembic)
├── alembic/                # migrations centralizadas
└── requirements.txt        # superset, usado pelo CI e pelo Alembic local
```

## CI/CD

- **CI** (`.github/workflows/ci.yml`): lint de Conventional Commits + pytest + Jest, roda em todo PR para `homolog`/`main`.
- **CD** (`.github/workflows/deploy-fly.yml`): dispara `flyctl deploy` dos 4 serviços a cada push em `homolog` ou `main` que toque `src/backend/**`. `auth`, `mobilidade` e `colaboracao` deployam em paralelo; `gateway` espera os três (`needs:`).
- Tokens de deploy do Fly com escopo restrito a 1 app cada, guardados como secrets no repositório GitHub (`FLY_DEPLOY_TOKEN_<SERVIÇO>`).

---

## Limitações conhecidas (débito técnico consciente)

Simplificações feitas de propósito para viabilizar o hello-world dentro do prazo, documentadas aqui para não virarem surpresa depois:

1. **Sem separação de ambiente homolog/produção no backend.** `deploy-fly.yml` dispara para os *mesmos* 4 apps do Fly.io tanto em push para `homolog` quanto para `main` — não existe um conjunto de apps de homologação distinto do de produção. Um push em `homolog` sobrescreve o que está rodando em produção até o próximo push em `main`. O frontend não tem esse problema: a Vercel já gera uma URL de preview própria por branch.
2. **Sem separação de banco por ambiente.** Um único banco Neon (`movecity`, schema `public`) atende tanto os testes locais quanto homolog e produção.
3. **Sem separação por schema.** O plano original previa 1 schema Postgres por serviço (`auth`, `mobilidade`, `colaboracao`, `gateway`); o que existe hoje é 1 tabela de teste por serviço, todas no schema `public`.
4. **Gateway não faz proxy de verdade.** Cada serviço expõe seu próprio `/hello` publicamente; o gateway ainda não centraliza roteamento nem validação de JWT (isso é o que a arquitetura de diagramas de sequência do projeto prevê para as User Stories futuras).
5. **`auth`, `mobilidade` e `colaboracao` são públicos**, não internos — o plano original previa que só o `gateway` fosse exposto publicamente, com os demais acessíveis apenas via rede privada do Fly.io (`.internal`).
6. **Migrations não rodam no CD.** O passo de `flyctl ssh console -C "alembic upgrade head"` do plano original não foi automatizado; migrations são aplicadas manualmente contra o Neon quando necessário.

Nenhuma dessas lacunas bloqueia o objetivo da issue #35 (validar o workflow ponta a ponta), mas precisam ser endereçadas antes de qualquer User Story real tocar em dado de usuário.

---

## Comandos de referência

```bash
# Deploy manual de um serviço (a partir da raiz do repo)
flyctl deploy --config src/backend/<servico>/fly.toml \
  --dockerfile src/backend/<servico>/Dockerfile \
  --remote-only .

# Migrations (local, contra o Neon)
cd src/backend && alembic upgrade head

# Verificação
curl https://movecity-gateway.fly.dev/health
curl https://movecity-gateway.fly.dev/gateway/hello
curl https://movecity-auth.fly.dev/auth/hello
curl https://movecity-mobilidade.fly.dev/mobilidade/hello
curl https://movecity-colaboracao.fly.dev/colaboracao/hello
```
