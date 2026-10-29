# Workflow de Desenvolvimento (Sprint)

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
| **Aprovação = botão Approve** | Comentário no PR não conta — só review formal via "Review changes" |

Regras de como agentes de IA devem operar nesse workflow (bypass, verificação, autoria): `docs/boas-praticas-ia.md`. Regras gerais (branches, commits, PRs): [`regras.md`](regras.md).

### Critérios DOR (Definitivamente Pronto para Desenvolvimento)

- [ ] PRD e SPEC documentados
- [ ] Critérios de aceite definidos
- [ ] Estimativa de complexidade
- [ ] Dependências mapeadas
- [ ] Diagrama de sequência disponível

### Critérios DOD (Definition of Done) — obrigatório, 2 níveis

Uma US **não fecha** sem passar pelos dois níveis. Promoção pra `main` pode acontecer em lote (várias USs de uma vez), então o nível de sprint é o que garante que a US está genuinamente terminada antes do release.

**DoD-Sprint** (conta como feita na sprint):
- [ ] PR mergeado em `homolog` (aprovação formal + CI verde)
- [ ] Critérios de aceite (cenários BDD) validados em homolog
- [ ] Comentário na issue com o resultado

**DoD-Release** (conta como entregue de verdade):
- [ ] PR homolog → main aprovado e mergeado
- [ ] Validado em produção (endpoint/tela real, não suposição)
- [ ] Issue fechada
- [ ] Documentação atualizada, se a US alterou algo documentado (arquitetura, setup, etc.)

### Agentes e skills

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

As skills e os agentes ficam em [`ai/skills/`](skills/) e [`ai/agents/`](agents/); o índice está no [`README.md`](README.md) desta pasta.
