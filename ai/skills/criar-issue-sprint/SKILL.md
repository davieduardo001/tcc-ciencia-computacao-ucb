---
name: criar-issue-sprint
description: Cria uma issue e opcionalmente a vincula à sprint corrente.
---

# Criar Issue com Sprint — Movecity

Esta skill cria uma issue e pergunta se ela deve ser adicionada à sprint corrente.

## Fluxo

### 1. Criar a Issue

```bash
gh issue create \
  --title "<título>" \
  --body "<descrição>" \
  --label "<label>" \
  --assignee "<usuario>"
```

### 2. Perguntar sobre Sprint

Após criar a issue, perguntar ao usuário:

```
Adicionar à Sprint 0? (sim/não)
```

### 3. Adicionar Milestone (se sim)

```bash
gh issue edit <NUMERO> --milestone "Sprint 0"
```

## Parâmetros

| Parâmetro | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `--title` | ✅ | Título da issue |
| `--body` | ✅ | Descrição/corpo da issue |
| `--label` | ✅ | Label (enhancement, bug, etc.) |
| `--assignee` | ❌ | Usuário responsável |
| `--sprint` | ❌ | "sim" ou "não" (padrão: perguntar) |

## Exemplos

### Criar issue e perguntar sobre sprint

```bash
gh issue create \
  --title "feat: adicionar filtro de linhas" \
  --body "Como usuário, quero filtrar linhas por horário..." \
  --label "enhancement" \
  --assignee "davieduardo001"
```

### Criar issue já com sprint

```bash
gh issue create \
  --title "fix: corrigir cálculo de rota" \
  --body "O cálculo de rota está retornando valor incorreto..." \
  --label "bug" \
  --milestone "Sprint 0"
```

## Labels Recomendadas

| Tipo | Label |
|------|-------|
| Feature | `enhancement` |
| Bug | `bug` |
| Correção | `correção` |
| Documentação | `documentation` |
| Chore | `chore` |
| US | `User Story` |

## Fluxo Completo

```
1. Criar issue
   └─ gh issue create --title ... --body ... --label ...

2. Perguntar sobre sprint
   └─ "Adicionar à Sprint 0?"

3. Se sim
   └─ gh issue edit <NUMERO> --milestone "Sprint 0"

4. Se não
   └─ Issue criada sem milestone
```

## Referências

- Guia de contribuição: `docs/guia-contribuicao.md`
- Skills relacionadas: `gerenciar-sprint`, `vincular-issues-sprint`
