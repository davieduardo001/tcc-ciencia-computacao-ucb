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
