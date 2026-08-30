# AGENT.md — Movecity

Manual de bordo do projeto. Fonte de verdade para stack, time, arquitetura e próximos passos.
As regras de workflow (branches, commits, skills) estão em `CLAUDE.md`.

## Leitura Obrigatória no Início de Cada Sessão

Antes de qualquer resposta, leia os arquivos abaixo para ter contexto completo do projeto:

- `docs/documento_visao.md` — visão geral do produto, objetivos e requisitos
- `docs/distribuicao_us.md` — quem é responsável por cada User Story e GitHub de cada membro

---

---

## Projeto

- **Nome:** Movecity — Mobilidade Urbana Colaborativa no DF
- **Objetivo:** Mitigar o "ônibus fantasma" e riscos de segurança em paradas via GPS do GDF + reportes crowdsourced.
- **Contexto:** TCC do Grupo Segurança no Transporte — UCB. Projeto-piloto em Taguatinga/Ceilândia.
- **Status:** Fase de Especificação e Planejamento.

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

**Regra:** Nenhum serviço acessa o banco diretamente. Tudo passa pelo Gateway.

**Decisões registradas:**
- Gateway é o **ponto único de entrada** para todas as requisições
- Gateway valida JWT localmente — sem round-trip ao Auth Service
- Gateway seta cookies httpOnly (access + refresh) — proteção contra XSS
- Gateway roteia requests para serviços backend via proxy
- Tokens em httpOnly cookies (access + refresh) — proteção contra XSS
- Leaflet + OSM evita custos de mapa em apresentações
- Fly.io para deploy simples via Docker
- Neon free tier suficiente para escala do TCC

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

---

## Workflow de Desenvolvimento (Sprint)

### Fluxo Completo

```
1. Planning       →  Selecionar USs do Sprint Backlog (1 US por pessoa mín.)
       ↓
2. Desenvolvimento →  Usar opencode (skills + agentes)
       ↓
3. PR              →  Abrir PR com testes + checklist preenchido
       ↓
4. Review          →  1 reviewer aprova (OBRIGATÓRIO)
       ↓
5. Homologação     →  Merge para homolog → deploy automático (Vercel)
       ↓
6. Produção        →  Merge homolog → main → deploy (Vercel + Fly.io)
```

### Regras Críticas

| Regra | Detalhe |
|-------|---------|
| **PR requer aprovação** | 1 reviewer mínimo antes do merge. Sem exceção. |
| **Nunca commitar direto** | `main` e `homolog` são protegidos |
| **Conventional Commits** | `feat:`, `fix:`, `docs:`, `test:`, etc. |
| **Sem Co-Authored-By** | Commits são apenas do desenvolvedor |
| **1 US por pessoa** | Cada membro pega 1 US por sprint |

### Critérios DOR (Definitivamente Pronto para Desenvolvimento)

- [ ] PRD e SPEC documentados
- [ ] Critérios de aceite definidos
- [ ] Estimativa de complexidade
- [ ] Dependências mapeadas
- [ ] Diagrama de sequência disponível

### Agentes e Skills (opencode)

| Agente | Uso |
|--------|-----|
| `build` | Desenvolvimento padrão (todas as ferramentas) |
| `plan` | Planejamento e análise (sem alterações) |
| `backend` | FastAPI, modelos, endpoints |
| `frontend` | Next.js, React, telas |
| `reviewer` | Review de código (read-only) |
| `tester` | Testes unitários (pytest/Jest) |
| `dev-environment` | Infra local: Docker, migrations, dependências |

| Skill | Uso |
|-------|-----|
| `desenvolver-us-backend` | Guia completo para dev backend |
| `desenvolver-us-frontend` | Guia completo para dev frontend |
| `criar-testes` | Criar testes unitários |
| `review-pr` | Checklist de review de PR |
| `criar-diagrama` | Criar diagramas PlantUML |
| `criar-issue-sprint` | Criar issue com sprint |
| `gerenciar-sprint` | Gerenciar andamento da sprint |
| `vincular-issues-sprint` | Vincular issues filhas à sprint |
| `vincular-pr-issue` | Vincular PRs a issues |

Documentação completa: `docs/boas-praticas-opencode.md`

---

## Próximos Passos

1. Adicionar @gualbertonathalia como colaboradora no repositório
2. Atualizar assignees das issues #22, #27–29, #32, #33 para @gualbertonathalia
3. Adicionar @Vitoria-Albuquerque e @gualbertonathalia como assignees na #33 (protótipo)
4. Modelar banco de dados (entidades: Usuário, Linha, Parada, Reporte)
5. Configurar pipeline CI/CD no GitHub Actions
