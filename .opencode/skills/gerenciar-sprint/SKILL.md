---
name: gerenciar-sprint
description: Gerencia sprints: listar issues, verificar andamento e sugerir objetivos.
---

# Gerenciar Sprint — Movecity

Esta skill gerencia sprints, listando issues, verificando andamento e sugerindo objetivos.

## Funcionalidades

### 1. Listar Issues da Sprint

```bash
# Listar issues abertas
gh issue list --milestone "Sprint 0" --state open

# Listar issues fechadas
gh issue list --milestone "Sprint 0" --state closed

# Listar todas
gh issue list --milestone "Sprint 0" --state all
```

### 2. Status da Sprint

```bash
# Contar issues abertas
gh issue list --milestone "Sprint 0" --state open --json number | jq length

# Contar issues fechadas
gh issue list --milestone "Sprint 0" --state closed --json number | jq length

# Calcular progresso
TOTAL=$(gh issue list --milestone "Sprint 0" --state all --json number | jq length)
FECHADAS=$(gh issue list --milestone "Sprint 0" --state closed --json number | jq length)
echo "Progresso: $FECHADAS/$TOTAL"
```

### 3. Detalhes das Issues

```bash
# Listar com detalhes
gh issue list --milestone "Sprint 0" --state all \
  --json number,title,state,labels,assignees \
  --jq '.[] | "\(.number) | \(.title) | \(.state) | \([.labels[].name] | join(", ")) | \([.assignees[].login] | join(", "))"'
```

### 4. Sugerir Objetivos

Análise automática baseada em:
- Issues abertas sem assignee
- Issues prioritárias (labels `high priority`)
- Issues bloqueantes

```bash
# Issues sem assignee
gh issue list --milestone "Sprint 0" --state open \
  --json number,title,assignees \
  --jq '.[] | select(.assignees | length == 0) | "\(.number) \(.title)"'

# Issues com label high priority
gh issue list --milestone "Sprint 0" --state open \
  --json number,title,labels \
  --jq '.[] | select(.labels[] | .name == "high priority") | "\(.number) \(.title)"'
```

### 5. Relatório de Sprint

```bash
# Gerar relatório completo
echo "=== Relatório Sprint 0 ==="
echo ""
echo "Issues abertas:"
gh issue list --milestone "Sprint 0" --state open --json number,title,assignees \
  --jq '.[] | "  #\(.number) \(.title) (\([.assignees[].login] | join(", ")))"'
echo ""
echo "Issues fechadas:"
gh issue list --milestone "Sprint 0" --state closed --json number,title \
  --jq '.[] | "  #\(.number) \(.title)"'
echo ""
echo "Progresso:"
TOTAL=$(gh issue list --milestone "Sprint 0" --state all --json number | jq length)
FECHADAS=$(gh issue list --milestone "Sprint 0" --state closed --json number | jq length)
echo "  $FECHADAS/$TOTAL issues fechadas"
```

## Comandos Rápidos

| Comando | Descrição |
|---------|-----------|
| `--listar` | Listar issues da sprint |
| `--status` | Mostrar status (abertas/fechadas) |
| `--detalhes` | Listar com detalhes completos |
| `--relatorio` | Gerar relatório completo |
| `--sugerir` | Sugerir objetivos para próxima sprint |

## Exemplo de Uso

```bash
# Listar issues da Sprint 0
gh issue list --milestone "Sprint 0" --state open

# Ver progresso
TOTAL=$(gh issue list --milestone "Sprint 0" --state all --json number | jq length)
FECHADAS=$(gh issue list --milestone "Sprint 0" --state closed --json number | jq length)
echo "Progresso: $FECHADAS/$TOTAL"
```

## Referências

- Guia de contribuição: `docs/guia-contribuicao.md`
- Skills relacionadas: `criar-issue-sprint`, `vincular-issues-sprint`
