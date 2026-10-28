# Plano de Deploy — Microservices Fly.io + Neon

**Última atualização:** 2026-10-28
**Issue de origem:** #35 (hello-world). O documento foi revisado em 28/10/2026 para refletir o que está em `homolog`, a branch que alimenta a produção.
**Branches:** `feat/*` e `fix/*` → `homolog` → `main`; `docs/*` e `chore/*` → `main` (ver `docs/guia-contribuicao.md`)

Este documento descreve o que está **efetivamente implementado e deployado**. O plano inicial da issue #35 (mais ambicioso, com schemas por serviço e serviços internos) foi substituído por este retrato fiel, incluindo as simplificações e lacunas conscientes. A visão de implantação completa está em `docs/documento_arquitetura.md`, seção 7.

---

## Arquitetura atual

```
[Frontend - Vercel]  movecity-frontend.vercel.app
    │
    ▼
[Gateway - Fly.io]   movecity-gateway.fly.dev
    │   valida o JWT do cookie e encaminha com X-User-Id
    ├──► movecity-auth.fly.dev
    ├──► movecity-mobilidade.fly.dev
    └──► movecity-colaboracao.fly.dev
              │
              ▼
         [Neon PostgreSQL]  (schema público único, sem PostGIS)
```

Os 4 serviços são apps independentes no Fly.io, cada um com seu próprio código, `Dockerfile`, `fly.toml` e `requirements.txt`. O Gateway faz proxy de verdade (`gateway/routes.py` e `gateway/proxy.py`): rotas `/api/auth/*` explícitas, `/api/mobilidade/*` e `/api/colaboracao/*` genéricas. Ele usa as URLs públicas `https://movecity-<serviço>.fly.dev` (padrão em `gateway/config.py`, sobrescrevível por `GATEWAY_AUTH_SERVICE_URL`, `GATEWAY_MOBILIDADE_SERVICE_URL` e `GATEWAY_COLABORACAO_SERVICE_URL`). Todos os serviços são públicos.

---

## Apps Fly.io

| App | Porta interna | Região | Máquinas |
|-----|---------------|--------|----------|
| `movecity-gateway` | 8000 | gru | `auto_stop_machines = true`, `min_machines_running = 0` |
| `movecity-auth` | 8000 | gru | idem |
| `movecity-mobilidade` | 8000 | gru | idem |
| `movecity-colaboracao` | 8000 | gru | idem |

Sem tráfego, as máquinas desligam; a primeira requisição depois de um período ocioso paga a partida a frio.

---

## Frontend (Vercel)

Projeto `movecity-frontend`, publicado em `movecity-frontend.vercel.app`. O workflow `deploy-vercel.yml` dispara **somente em push para `homolog`** (caminhos `src/frontend/**`), faz `vercel build --prod` e `vercel deploy --prebuilt --prod`. Não existe deploy do frontend a partir da `main`: nesta fase, `homolog` **é** o ambiente público.

Variáveis de build injetadas pelo workflow a partir de secrets do GitHub: `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (secret `GOOGLE_CLIENT_ID`) e `NEXT_PUBLIC_CARTO_API_KEY` (secret `CARTO_API_KEY`; sem ela o mapa cai para o tile padrão do OpenStreetMap).

O protótipo de alta fidelidade (`prototipo-alta-fid/web`) é publicado no GitHub Pages por `deploy-pages.yml`, em push na `main`.

---

## Banco de dados

Um único projeto `movecity` no Neon (região `sa-east-1`), schema `public`, **sem PostGIS** (geometria em colunas JSON; decisão ADR-02 em `docs/documento_arquitetura.md`). Todos os serviços compartilham o mesmo banco; cada tabela pertence por convenção a um serviço (por exemplo `usuarios` e `tokens_reset_senha` ao auth, `linha`, `parada`, `rota` e `viagem` à mobilidade, `ocorrencia` e `preferencias_notificacao` à colaboração).

Migrations via Alembic, centralizadas em `src/backend/alembic/` e **executadas automaticamente** pelo job `migrate` do `deploy-fly.yml` (`alembic upgrade head`, com o secret `DATABASE_URL` do GitHub) antes do deploy dos serviços que usam banco.

Os dados de linhas do SEMOB entram por ingestão em lote (`ingestao-semob.yml`, todo dia 1º às 4h UTC e sob demanda), que popula a tabela `linha`. A posição dos veículos é lida ao vivo e nunca persistida.

---

## Secrets e variáveis por App

Detalhe e como configurar cada um: `docs/secrets-por-plataforma.md`.

| Variável | Gateway | Auth | Mobilidade | Colaboracao |
|----------|---------|------|------------|-------------|
| `DATABASE_URL` | não usa | sim | sim | sim |
| `JWT_SECRET` | sim | sim | não | não |
| `JWT_ALGORITHM` | sim | sim | não | não |
| `JWT_EXPIRATION_MINUTES` | sim | sim | não | não |
| `ENVIRONMENT` | sim | sim | sim | sim |
| `CORS_ORIGINS` (padrão `http://localhost:3000`) | sim (precisa da origem do frontend) | lê | lê | lê |
| `GOOGLE_CLIENT_ID` | não | sim (aplicado pelo job `deploy-auth`) | não | não |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `FRONTEND_URL` | não | sim (aplicados pelo job `deploy-auth`) | não | não |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | não | não | sim (aplicados pelo job `deploy-mobilidade`) | não |
| `RAIO_EMBARQUE_M` e demais limites de embarque | não | não | opcional | não |

Observações:

- O quadro mostra o que o código lê de cada serviço. O conjunto exato de secrets cadastrados no Fly não é verificável a partir do repositório; consulte com `fly secrets list --app <app>`.
- Os secrets SMTP (recuperação de senha, issue #237) e VAPID (Web Push, issue #200) só são aplicados se os quatro (SMTP) ou os três (VAPID) secrets correspondentes existirem no GitHub; do contrário o job registra que estão ausentes, segue o deploy e o recurso fica desligado.
- Em **produção, `RAIO_EMBARQUE_M` está em 100 km (`100000`)** por decisão do grupo (issue #216, 27/10/2026), apenas para demonstrar o embarque de qualquer lugar até a defesa. O padrão do código é 100 m. Com esse valor a regra de 100 m não é exercitada em produção (limite conhecido, ver "Limitações conhecidas").

---

## Estrutura de código

```
src/backend/
├── shared/                 # config.py, database.py, logs.py (comuns aos 4 serviços)
│
├── gateway/ auth/ mobilidade/ colaboracao/
│   ├── Dockerfile
│   ├── fly.toml
│   ├── requirements.txt
│   ├── main.py
│   ├── routes.py
│   ├── models/             # (nos serviços que têm tabelas)
│   └── tests/
│
├── models/base.py          # DeclarativeBase compartilhado
├── alembic/                # migrations centralizadas
├── alembic.ini
└── requirements.txt        # superset, usado pelo CI e pelo Alembic local
```

Os `Dockerfile` são construídos a partir da **raiz do repositório** (copiam `models/`, `shared/` e o pacote do serviço) e iniciam `uvicorn <serviço>.main:app` na porta 8000.

## CI/CD

- **CI** (`.github/workflows/ci.yml`): roda em todo PR para `homolog`/`main` (e manualmente). Jobs: `Testes Backend (pytest)` (Postgres de serviço, `alembic upgrade head`, health check do gateway e `pytest`), `Contêiner do serviço (gateway|auth|mobilidade|colaboracao)` (venv limpo só com o `requirements.txt` do serviço e import da aplicação), `Testes Frontend (Jest)` e `Lint e Conventional Commits` (valida o título do PR e os commits). Os sete são checks obrigatórios das branches `main` e `homolog`.
- **CD backend** (`.github/workflows/deploy-fly.yml`): dispara a cada push em `homolog` ou `main` que toque `src/backend/**` (ou o próprio workflow), e manualmente. Ordem: `migrate` → `deploy-auth`, `deploy-mobilidade`, `deploy-colaboracao` em paralelo; `deploy-gateway` é independente dos três. Cada deploy termina com um smoke test em `GET /health` (até 10 tentativas, 5 s de intervalo).
- **CD frontend** (`.github/workflows/deploy-vercel.yml`): somente em push para `homolog` (ver seção Frontend).
- Tokens de deploy do Fly têm escopo restrito a 1 app cada, guardados como secrets do repositório (`FLY_DEPLOY_TOKEN_GATEWAY`, `_AUTH`, `_MOBILIDADE`, `_COLABORACAO`).
- Verificação local antes do commit: `scripts/verificar-deploy.sh` (ver `docs/checklist-pre-commit.md`).

---

## Limitações conhecidas (débito técnico consciente)

1. **Sem separação de ambiente homolog/produção no backend (risco aceito).** `deploy-fly.yml` dispara para os *mesmos* 4 apps do Fly.io tanto em push para `homolog` quanto para `main`: **`homolog` publica diretamente na produção**. O frontend também: o deploy da Vercel sai de `homolog` em modo `--prod`. A issue #42 ("Separar ambientes homolog/produção no backend") foi fechada em 14/10/2026, mas a separação **não foi implementada**: `deploy-fly.yml` e `deploy-vercel.yml` seguem como descritos aqui. O grupo aceitou o risco.
2. **Sem separação de banco por ambiente.** Um único banco Neon (`movecity`, schema `public`) atende desenvolvimento remoto, homologação e produção.
3. **Sem separação por schema.** O plano original previa 1 schema Postgres por serviço; hoje tudo está em `public`. As tabelas `test_user`, `test_linha`, `test_reporte` e `test_log` do hello-world ainda existem nos modelos.
4. **`auth`, `mobilidade` e `colaboracao` são públicos**, não internos. O Gateway chama as URLs públicas `https://movecity-<serviço>.fly.dev` (a rede privada `.internal` do Fly é IPv6-only e causou instabilidade; comentário em `gateway/config.py`). Os serviços de domínio confiam no cabeçalho `X-User-Id` que o Gateway injeta; o Gateway descarta o `X-User-Id` enviado pelo cliente.
5. **`RAIO_EMBARQUE_M` em 100 km em produção** (decisão do grupo de 27/10/2026, issue #216), só para a demonstração; voltar a `100` com `flyctl secrets set RAIO_EMBARQUE_M=100 -a movecity-mobilidade` e retestar a recusa a mais de 100 m. Enquanto isso, a regra de proximidade não é exercitada em produção.
6. **Partida a frio.** Com `min_machines_running = 0`, a primeira requisição após período ocioso é lenta.

---

## Comandos de referência

```bash
# Deploy manual de um serviço (a partir da raiz do repo)
flyctl deploy --config src/backend/<servico>/fly.toml \
  --dockerfile src/backend/<servico>/Dockerfile \
  --remote-only .

# Migrations (local, contra o banco apontado por DATABASE_URL)
cd src/backend && alembic upgrade head

# Verificação (health de cada serviço)
curl https://movecity-gateway.fly.dev/health
curl https://movecity-auth.fly.dev/health
curl https://movecity-mobilidade.fly.dev/health
curl https://movecity-colaboracao.fly.dev/health

# Status agregado dos serviços, via Gateway
curl https://movecity-gateway.fly.dev/api/status
```
