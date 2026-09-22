# Guia de Contribuição — Movecity

Boas-vindas ao repositório do Movecity! Este guia define as convenções de branches e commits que toda a equipe deve seguir para manter o histórico organizado e o fluxo de desenvolvimento previsível.

> Procurando o passo a passo prático de ponta a ponta (branch → PR → review → deploy)? Veja `docs/workflow-passo-a-passo.md`.

---

## Fluxo de Branches

Adotamos um modelo de **3 níveis**, inspirado no Git Flow, adaptado para o tamanho da equipe:

```
feat/nome-da-feature   ──► homolog ──► main
fix/nome-da-correcao   ──► homolog ──► main
docs/atualizacao               ──────► main  (direto)
chore/configuracao             ──────► main  (direto)
```

### Regras

| Tipo de branch | Base de criação | Merge em |
|---|---|---|
| `feat/*` | `homolog` | `homolog` → `main` |
| `fix/*` | `homolog` | `homolog` → `main` |
| `docs/*` | `main` | `main` (direto) |
| `chore/*` | `main` | `main` (direto) |

- **`feat/` e `fix/`** passam por `homolog` antes de `main` — qualquer coisa que altere comportamento funcional precisa de validação no ambiente de staging.
- **`docs/` e `chore/`** vão direto para `main` — sem risco de quebrar o sistema.
- **Nunca** fazer merge de `feat/` ou `fix/` direto em `main`.
- **Nunca** commitar diretamente em `main` ou `homolog`.

### Passo a passo: nova feature ou correção

```bash
# 1. Partir de homolog atualizado
git checkout homolog
git pull origin homolog
git checkout -b feat/nome-da-feature

# 2. Desenvolver e commitar (ver seção de commits abaixo)
git add <arquivos>
git commit -m "feat: descrição da mudança"

# 3. Subir branch e abrir PR para homolog
git push -u origin feat/nome-da-feature
# → abrir Pull Request: feat/nome-da-feature → homolog

# 4. Após aprovação e testes em homolog, abrir PR para main
# → abrir Pull Request: homolog → main
```

### Passo a passo: documentação ou configuração

```bash
# 1. Partir de main atualizado
git checkout main
git pull origin main
git checkout -b docs/nome-da-atualizacao

# 2. Commitar
git add <arquivos>
git commit -m "docs: descrição da mudança"

# 3. Merge direto para main
git push -u origin docs/nome-da-atualizacao
# → abrir Pull Request: docs/nome-da-atualizacao → main
```

---

## Nomeclatura de Branches

Use sempre **kebab-case** (letras minúsculas, palavras separadas por hífen):

| Tipo | Exemplo |
|---|---|
| Nova funcionalidade | `feat/mapa-tempo-real` |
| Correção de bug | `fix/calculo-rota-incorreto` |
| Documentação | `docs/atualizar-readme` |
| Configuração / build | `chore/configurar-github-actions` |
| Refatoração | `refactor/modulo-autenticacao` |
| Performance | `perf/otimizar-query-paradas` |

---

## Conventional Commits

Todas as mensagens de commit seguem o padrão [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>: <descrição curta no imperativo>
```

### Tipos disponíveis

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat: adicionar filtro de linhas por horário` |
| `fix` | Correção de bug | `fix: corrigir posição do marcador no mapa` |
| `docs` | Apenas documentação | `docs: atualizar guia de contribuição` |
| `style` | Formatação sem mudança de lógica | `style: aplicar prettier nos componentes` |
| `refactor` | Refatoração sem fix ou feat | `refactor: extrair lógica de geolocalização` |
| `chore` | Build, configs, dependências | `chore: atualizar versão do Next.js` |
| `perf` | Otimização de performance | `perf: cachear resposta da API de paradas` |
| `test` | Adicionar ou corrigir testes | `test: adicionar testes unitários do service de rotas` |

### Regras para a mensagem

- **Descrição curta:** imperativo, presente, sem ponto final — "adicionar" não "adicionado", "corrigir" não "corrigido"
- **Limite:** primeira linha com no máximo 72 caracteres
- **Separação docs/src:** mudanças em `docs/` e `src/` devem ser commits separados, salvo dependência estrita
- **Granularidade:** um commit = uma intenção. Prefira vários commits pequenos a um commit gigante

### Exemplos reais

```bash
# Bom ✅
git commit -m "feat: exibir tempo estimado de chegada na parada"
git commit -m "fix: tratar erro 404 na API do GDF"
git commit -m "docs: adicionar diagrama de sequência do caso de uso UC14"
git commit -m "chore: configurar eslint e prettier"

# Ruim ❌
git commit -m "update"
git commit -m "várias correções e melhorias"
git commit -m "WIP"
git commit -m "fixes"
```

---

## Autoria e Identidade

- **Nunca** incluir `Co-Authored-By` ou qualquer referência a ferramentas de IA (Claude, Gemini, etc.) nas mensagens de commit ou PRs.
- O commit deve aparecer somente no nome do desenvolvedor responsável pela alteração.
- Use sempre o usuário autenticado no `gh` CLI para operações no GitHub.

---

## Resumo Rápido (TL;DR)

```
nova feature/fix   →  git checkout homolog && git checkout -b feat/nome
                       desenvolver → commitar → PR para homolog → PR para main

docs/configuração  →  git checkout main && git checkout -b docs/nome
                       commitar → PR direto para main

commit             →  tipo: descrição curta no imperativo (max 72 chars)
```

---

## Boas Práticas Adicionais

### Antes de abrir PR

1. **Rebase em homolog** antes de subir:
   ```bash
   git fetch origin homolog
   git rebase origin/homolog
   ```

2. **Verificar se testes passam** localmente:
   ```bash
   # Backend
   cd src/backend && pytest -v
   
   # Frontend
   cd src/frontend && npm test
   ```

3. **Usar o PR template** — o GitHub preenche automaticamente ao criar o PR

### Regras de Merge

| Regra | Detalhe |
|-------|---------|
| **1 approval mínimo** | Branch `main` e `homolog` requerem 1 aprovação |
| **Status checks** | CI deve passar (testes + lint) |
| **Squash merge** | Para `feat/*` e `fix/*` — mantém histórico limpo |
| **Delete branch** | Branches feature são deletadas após merge |
| **No force push** | Nunca fazer force push em branches protegidas |

> **Atenção:** um comentário de texto no PR (ex.: "revisado", "ok pra mim") **não é aprovação**. Só conta o que for submetido via botão **"Review changes" → "Approve"**, na aba "Files changed". Verifique com `gh pr view <N> --json reviewDecision` antes de considerar um PR aprovado.

### Fluxo Completo

```
1. git checkout homolog && git pull
2. git checkout -b feat/issue-XX-nome
3. Desenvolver + testar
4. git add . && git commit -m "feat: descricao"
5. git fetch origin homolog && git rebase origin/homolog
6. git push -u origin feat/issue-XX-nome
7. Abrir PR: feat/XX → homolog
8. Aguardar review + CI passar
9. Merge (squash) → homolog
10. Abrir PR: homolog → main
11. Merge → main → deploy automático
```

### O que NÃO fazer

| ❌ Não faça | ✅ Faça isso |
|-------------|--------------|
| Commit direto em `main` | Sempre criar branch |
| Merge sem approval | Aguardar 1 reviewer aprovar |
| Force push em branch protegida | Usar commits normais |
| Incluir `Co-Authored-By` | Apenas seu nome |
| PR gigante com tudo junto | PRs pequenos e atômicos |
| Branch desatualizada | Rebase antes de subir |

---

## Vinculação de PRs a Issues

Toda Pull Request **deve** estar vinculada a uma Issue. Isso garante rastreabilidade e organização.

### Regras

| Regra | Descrição |
|-------|-----------|
| **Toda PR deve ter uma issue** | Se a issue não existir, criar antes de abrir o PR |
| **Vincular no "Development"** | Usar a seção "Linked issues" na sidebar do PR |
| **Correções sem issue** | Criar uma issue primeiro com label `bug` ou `correção` |

### Quando criar uma Issue

| Cenário | Ação |
|---------|------|
| Nova feature (feat) | Criar issue com label `enhancement` |
| Correção de bug (fix) | Criar issue com label `bug` |
| Chore/configuração | Não precisa de issue |
| Documentação | Não precisa de issue |

### Como Vincular via GitHub UI

1. Abrir o **PR** no GitHub
2. Na sidebar direita, clicar em **"Linked issues"** → **"Add"**
3. Selecionar a issue correspondente

### Como Vincular via CLI (GraphQL)

```bash
# 1. Obter node IDs
gh api graphql -f query='
{
  repository(owner: "davieduardo001", name: "tcc-ciencia-computacao-ucb") {
    issue(number: <NUMERO_ISSUE>) { id }
    pullRequest(number: <NUMERO_PR>) { id }
  }
}'

# 2. Vincular
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

### Exemplo

```bash
# Vincular PR #56 à issue #31
gh api graphql -f query='
{
  repository(owner: "davieduardo001", name: "tcc-ciencia-computacao-ucb") {
    issue(number: 31) { id }
    pullRequest(number: 56) { id }
  }
}'

gh api graphql -f query='
mutation {
  addCloseIssueReferences(input: {
    issueId: "I_kwDORgtye88AAAABD0k_dA", 
    pullRequestIds: ["PR_kwDORgtye88AAAABBdokvw"]
  }) {
    clientMutationId
  }
}'
```

### Fluxo Completo

```
1. Criar issue (se não existir)
2. Criar branch feat/* ou fix/*
3. Desenvolver + commitar
4. Abrir PR
5. Vincular PR à issue (UI ou CLI)
6. Aguardar review + CI
7. Merge
```

---

## Gerenciamento de Sprints

### Regras

| Regra | Descrição |
|-------|-----------|
| **Toda issue deve ter milestone** | Issue sem milestone é issue perdida |
| **Sprint = Milestone** | Cada sprint é uma milestone no GitHub |
| **Vincular issues filhas** | Sub-issues devem estar na mesma sprint |

### Skills de Sprint

| Skill | Descrição |
|-------|-----------|
| `criar-issue-sprint` | Cria issue e pergunta se adiciona à sprint |
| `gerenciar-sprint` | Lista issues, mostra status, sugere objetivos |
| `vincular-issues-sprint` | Vincula issues filhas à sprint |

### Criar Issue com Sprint

```bash
# Criar issue e perguntar sobre sprint
gh issue create \
  --title "feat: adicionar filtro de linhas" \
  --body "Como usuário, quero filtrar linhas por horário..." \
  --label "enhancement"

# Criar issue já com milestone
gh issue create \
  --title "fix: corrigir cálculo de rota" \
  --body "O cálculo de rota está retornando valor incorreto..." \
  --label "bug" \
  --milestone "Sprint 0"
```

### Listar Issues da Sprint

```bash
# Listar issues abertas
gh issue list --milestone "Sprint 0" --state open

# Listar issues fechadas
gh issue list --milestone "Sprint 0" --state closed

# Ver progresso
TOTAL=$(gh issue list --milestone "Sprint 0" --state all --json number | jq length)
FECHADAS=$(gh issue list --milestone "Sprint 0" --state closed --json number | jq length)
echo "Progresso: $FECHADAS/$TOTAL"
```

### Adicionar Issue à Sprint

```bash
# Adicionar issue específica
gh issue edit <NUMERO> --milestone "Sprint 0"

# Adicionar todas as issues sem milestone
ISSUES=$(gh issue list --state open --json number,milestone \
  --jq '.[] | select(.milestone == null) | .number')

for ISSUE in $ISSUES; do
  gh issue edit $ISSUE --milestone "Sprint 0"
  echo "Issue #$ISSUE adicionada à Sprint 0"
done
```

### Vincular Sub-Issues

1. Abrir a issue pai no GitHub
2. Na sidebar, encontrar "Sub-issues"
3. Clicar em "Add" e selecionar as issues filhas

### Fluxo Completo de Sprint

```
1. Criar sprint (milestone)
   └─ Criar milestone no GitHub

2. Criar issues
   └─ Usar criar-issue-sprint

3. Vincular issues à sprint
   └─ Usar vincular-issues-sprint

4. Acompanhar andamento
   └─ Usar gerenciar-sprint

5. Fechar sprint
   └─ Fechar milestone
```
