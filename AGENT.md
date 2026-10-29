# AGENT.md — Movecity

Ponto de entrada comum a **todos os agentes de IA** do projeto (Claude Code, OpenCode, Gemini). Aqui estão os fatos do projeto: o que é, quem faz o quê, a stack e a arquitetura. Tudo que configura a atuação dos agentes (regras, workflow, skills, agentes e configurações de cada ferramenta) fica em [`ai/`](ai/README.md).

```
CLAUDE.md ──► AGENT.md ──► ai/   regras.md · workflow.md · skills/ · agents/ · instalar.sh
```

## Onde está cada coisa

| Preciso de... | Arquivo |
|---|---|
| Regras de branches, commits, PRs e diagramas | [`ai/regras.md`](ai/regras.md) |
| Ciclo de sprint, DoR e DoD (dois níveis) | [`ai/workflow.md`](ai/workflow.md) |
| Skills e agentes disponíveis, e como ativá-los na sua ferramenta | [`ai/README.md`](ai/README.md) |
| Como a IA deve agir no repositório (autoria, bypass, verificação) | [`docs/boas-praticas-ia.md`](docs/boas-praticas-ia.md) |
| Manual do ciclo, do backlog ao deploy | [`docs/manual-sprint.md`](docs/manual-sprint.md) |

## Leitura obrigatória no início de cada sessão

Antes de qualquer resposta, leia os arquivos abaixo para ter contexto completo do projeto. O Claude Code os carrega sozinho por meio das importações a seguir; as outras ferramentas devem abri-los.

@ai/regras.md
@docs/documento_visao.md
@docs/distribuicao_us.md

---

## Projeto

- **Nome:** Movecity — Mobilidade Urbana Colaborativa no DF
- **Objetivo:** Mitigar o "ônibus fantasma" e riscos de segurança em paradas via GPS do GDF + reportes crowdsourced.
- **Contexto:** TCC do Grupo Segurança no Transporte — UCB. Projeto-piloto em Taguatinga/Ceilândia.
- **Status:** Entrega final. Produto em produção em <https://movecity-frontend.vercel.app>; defesa em 13/11/2026.

---

## Time

| GitHub | Responsabilidade |
|---|---|
| @davieduardo001 | Orquestração, backlog, revisão de PRs, documentação arquitetural |
| @brenouchihar | Épico Autenticação (US #10–13, #31) |
| @Kelvin963 | Épico Mapa — Núcleo + Arquitetura inicial (US #9, #14–17) |
| @louisassis | Épico Mapa — Detalhes e Rotas (US #18–21) |
| @Vitoria-Albuquerque | Colaboração (Reporte) + Protótipo (US #23–26, #30, #33) |
| @gualbertonathalia | Colaboração (Alertas) + Termos + Protótipo (US #22, #27–29, #32, #33) |

---

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js (App Router) |
| Mapa / GPS | Leaflet JS + OpenStreetMap + API GPS GDF (GeoJSON) |
| Backend | FastAPI (Python) — Fly.io |
| Banco de Dados | PostgreSQL — Neon (serverless) |
| CI/CD | GitHub Actions |
| Metodologia | Agentic Workflow + Lean Inception |

---

## Arquitetura

```
[Browser]
    │  cookies: access_token + refresh_token
    ▼
[Next.js Frontend]
    │  envia cookies automaticamente
    ▼
[API Gateway — Ponto Único de Entrada]
    │  lê access_token do cookie
    │  valida JWT localmente
    │  extrai identidadeUsuario
    │  roteia para serviços backend
    ├──► [Auth Service] ──► [PostgreSQL]
    ├──► [Mobilidade Service] ──► [PostgreSQL]
    └──► [Colaboracao Service] ──► [PostgreSQL]
```

**Regra:** o frontend só fala com o Gateway. Os serviços de domínio acessam o PostgreSQL (Neon); o Gateway não acessa o banco.

**Decisões registradas:**
- Gateway é o **ponto único de entrada** para todas as requisições
- Gateway valida JWT localmente — sem round-trip ao Auth Service
- Gateway seta cookies httpOnly (access + refresh) — proteção contra XSS
- Gateway roteia requests para serviços backend via proxy
- Tokens em httpOnly cookies (access + refresh) — proteção contra XSS. Limitação conhecida (#253): o frontend também grava os tokens no `localStorage`, o que reduz essa proteção até a correção
- Cookies com `SameSite=None` + `Secure`: frontend (Vercel) e Gateway (Fly) são cross-site
- Leaflet com base CARTO Voyager, recuando pro tile padrão do OSM sem a chave
- Fly.io com **4 apps independentes** (gateway, auth, mobilidade, colaboracao)
- Neon free tier suficiente para escala do TCC — **sem PostGIS**: geometria em colunas JSON
- SEMOB copiado pro banco por ingestão em lote (GitHub Action mensal); posição lida ao vivo, nunca persistida
- Integrações externas atrás de `typing.Protocol` (provider mock + real)
- Registro completo das decisões da sprint: `docs/documento_arquitetura.md`, seção 10

**Endpoints do Gateway:**

| Endpoint | Método | Destino |
|----------|--------|---------|
| `/api/auth/login` | POST | Auth Service |
| `/api/auth/registrar` | POST | Auth Service |
| `/api/auth/refresh` | POST | Auth Service |
| `/api/auth/logout` | POST | Auth Service |
| `/api/mobilidade/*` | GET/POST/PUT/DELETE | Mobilidade Service |
| `/api/colaboracao/*` | GET/POST/PUT/DELETE | Colaboracao Service |

**Fluxo de Autenticação (US #31):**
- Gateway lê `access_token` do cookie httpOnly
- Valida JWT localmente (verifica assinatura e expiração)
- Extrai `identidadeUsuario` e passa via `request.state`
- Serviços de domínio recebem `identidadeUsuario` já validado
- Documentação completa: `docs/gateway-auth-flow.md`
