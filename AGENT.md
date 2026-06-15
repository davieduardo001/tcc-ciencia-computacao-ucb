# AGENT.md — Movecity

Manual de bordo do projeto. Fonte de verdade para stack, time, arquitetura e próximos passos.
As regras de workflow (branches, commits, skills) estão em `CLAUDE.md`.

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
    │
    ▼
[Next.js — Frontend]
    │  Leaflet JS + OSM tiles + GPS GDF (GeoJSON)
    ▼
[API Gateway]
    │  Valida JWT localmente (US #31)
    ├──► [FastAPI — Serviços de Domínio] ──► [PostgreSQL — Neon]
    └──► [Auth Service] ──► [ModeloSessao]
```

**Decisões registradas:**
- Gateway valida JWT localmente — sem round-trip ao Auth Service
- Leaflet + OSM evita custos de mapa em apresentações
- Fly.io para deploy simples via Docker
- Neon free tier suficiente para escala do TCC

---

## Próximos Passos

1. Adicionar @gualbertonathalia como colaboradora no repositório
2. Atualizar assignees das issues #22, #27–29, #32, #33 para @gualbertonathalia
3. Adicionar @Vitoria-Albuquerque e @gualbertonathalia como assignees na #33 (protótipo)
4. Modelar banco de dados (entidades: Usuário, Linha, Parada, Reporte)
5. Configurar pipeline CI/CD no GitHub Actions
