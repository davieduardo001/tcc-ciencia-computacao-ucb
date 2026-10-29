---
name: vincular-pr-issue
description: Guia para vincular Pull Requests a Issues no projeto Movecity.
---

# Vincular PR a Issue — Movecity

## Regra

Toda Pull Request **deve** estar vinculada a uma Issue.

## Fluxo

### 1. Verificar se a Issue existe

```bash
gh issue list --search "<palavra-chave>"
```

### 2. Criar Issue (se não existir)

```bash
gh issue create --title "<título>" --body "<descrição>" --label "<label>"
```

### 3. Vincular PR à Issue

**Opção 1: Via GitHub UI**
1. Abrir o PR
2. Sidebar → "Linked issues" → "Add"
3. Selecionar a issue

**Opção 2: Via CLI (GraphQL)**

```bash
# Obter node IDs
gh api graphql -f query='
{
  repository(owner: "davieduardo001", name: "tcc-ciencia-computacao-ucb") {
    issue(number: <NUMERO_ISSUE>) { id }
    pullRequest(number: <NUMERO_PR>) { id }
  }
}'

# Vincular
gh api graphql -f query='
mutation {
  addCloseIssueReferences(input: {
    issueId: "<NODE_ID_ISSUE>", 
    pullRequestIds: ["<NODE_ID_PR>"]
  }) {
    clientMutationId
  }
}'
```

### 4. Adicionar keyword no corpo do PR

No corpo do PR, adicionar:
```
Closes #<NUMERO_ISSUE>
```

Isso garante auto-close quando o PR for mergeado.

## Labels Recomendadas

| Tipo | Label |
|------|-------|
| Feature | `enhancement` |
| Bug | `bug` |
| Correção | `correção` |
| Documentação | `documentation` |
| Chore | `chore` |

## Referências

- Guia de contribuição: `docs/guia-contribuicao.md`
- GraphQL API: https://docs.github.com/en/graphql
