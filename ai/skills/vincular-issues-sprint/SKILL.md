---
name: vincular-issues-sprint
description: Vincula issues filhas à sprint corrente.
---

# Vincular Issues Filhas à Sprint — Movecity

Esta skill lista issues sem milestone e permite adicioná-las à sprint corrente.

## Fluxo

### 1. Listar Issues sem Milestone

```bash
gh issue list --state open --json number,title,milestone,labels \
  --jq '.[] | select(.milestone == null) | "\(.number) | \(.title) | \([.labels[].name] | join(", "))"'
```

### 2. Perguntar quais Adicionar

Para cada issue sem milestone, perguntar:
```
Adicionar issue #<NUMERO> à Sprint 0? (sim/não)
```

### 3. Adicionar à Sprint

```bash
gh issue edit <NUMERO> --milestone "Sprint 0"
```

### 4. Vincular Issues Filhas (Opcional)

Se a issue for uma "sub-issue" de outra issue, vincular usando:

**Opção 1: Via GitHub UI**
1. Abrir a issue pai
2. Sidebar → "Sub-issues" → "Add"
3. Selecionar a issue filha

**Opção 2: Via CLI**
```bash
# Não há comando CLI direto para sub-issues
# Usar GitHub UI para vincular
```

## Funcionalidades

| Comando | Descrição |
|---------|-----------|
| `--listar-pendentes` | Listar issues sem milestone |
| `--adicionar <NUMERO>` | Adicionar issue à sprint |
| `--adicionar-todas` | Adicionar todas as issues sem milestone |
| `--vincular-filhas` | Vincular issues filhas (via UI) |

## Exemplos

### Listar issues pendentes

```bash
gh issue list --state open --json number,title,milestone \
  --jq '.[] | select(.milestone == null) | "\(.number) \(.title)"'
```

### Adicionar issue específica

```bash
gh issue edit 42 --milestone "Sprint 0"
```

### Adicionar todas as issues sem milestone

```bash
# Listar números das issues sem milestone
ISSUES=$(gh issue list --state open --json number,milestone \
  --jq '.[] | select(.milestone == null) | .number')

# Adicionar cada uma à sprint
for ISSUE in $ISSUES; do
  gh issue edit $ISSUE --milestone "Sprint 0"
  echo "Issue #$ISSUE adicionada à Sprint 0"
done
```

## Vinculação de Sub-Issues

### O que são Sub-Issues

Sub-issues são issues que dependem de uma issue pai. Exemplo:

```
Issue #31: [US] Gerenciar Ciclo de Vida da Sessão
├── Issue #56: feat: implementar middleware JWT
├── Issue #57: fix: adicionar python-jose
└── Issue #58: fix: health check
```

### Como Vincular

1. Abrir a issue pai no GitHub
2. Na sidebar, encontrar "Sub-issues"
3. Clicar em "Add" e selecionar as issues filhas

## Referências

- Guia de contribuição: `docs/guia-contribuicao.md`
- Skills relacionadas: `criar-issue-sprint`, `gerenciar-sprint`
