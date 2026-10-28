# QA e Relatórios de Teste — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/README.md>

Esta pasta reúne o esquema de testes no estilo QA do Movecity: o plano, os casos de teste manuais por User Story entregue e os relatórios de testes unitários, de integração, de cobertura e de defeitos. Nasce da issue [#151](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/151).

> **Fotografia datada.** Todos os números foram medidos em **16/10/2026**, no commit `07c9edc` da branch `homolog` (merge do PR #194). Eles não se atualizam sozinhos: ao fim de cada sprint, o procedimento da seção "Como regerar" refaz as medições.

## Documentos

| Documento | Para que serve |
|---|---|
| [`plano-de-testes.md`](plano-de-testes.md) | Ambientes, pré-requisitos, critérios de entrada e saída, escala de severidade e regressão mínima |
| [`matriz-rastreabilidade.md`](matriz-rastreabilidade.md) | US → cenários BDD → casos de teste manuais → PRs → testes automatizados |
| [`casos-de-teste.md`](casos-de-teste.md) | Os casos manuais, com pré-condição, passos, resultado esperado, severidade e estado |
| [`relatorio-testes-unitarios.md`](relatorio-testes-unitarios.md) | Execução real das suítes e os testes de cada PR mergeado desde a Sprint 2 |
| [`relatorio-testes-integracao.md`](relatorio-testes-integracao.md) | O que existe de teste de integração, as lacunas e um plano priorizado |
| [`execucao-casos-p1.md`](execucao-casos-p1.md) | Execução dos 49 casos de teste manuais em produção (27 e 28/10/2026): passos, resultado, evidência em [`evidencias/`](evidencias/), quadro geral por estado e defeitos encontrados |
| [`avaliacao-usabilidade-nielsen.md`](avaliacao-usabilidade-nielsen.md) | Avaliação de usabilidade pelas 10 heurísticas de Nielsen (teste 4.3 do roteiro), com severidade e limites do método |
| [`relatorio-cobertura-e-defeitos.md`](relatorio-cobertura-e-defeitos.md) | Cobertura medida, defeitos encontrados e como foram detectados, histórico de CI e dívida de testes |
| [`resumo-executivo.md`](resumo-executivo.md) | Uma página, para a review e para a defesa |

## Números principais

| Medida | Valor | Fonte |
|---|---|---|
| Testes automatizados (backend + frontend) | **1.640**, 0 falhas (844 backend, 796 frontend) | log do CI em 28/10/2026, execução `40689632241`, `48483be`. Em 16/10 eram **1.260** (`07c9edc`) |
| Backend (pytest, Postgres 16 + migrations) | 671 testes em 56 arquivos, 65 s | idem |
| Frontend (Jest) | 589 testes em 33 suítes, 36 s | idem |
| Cobertura do código de produção do backend | 93,7% das instruções | `pytest --cov`, ver o relatório |
| Cobertura do frontend | 89,1% das instruções dos arquivos importados | `jest --coverage`, ver o relatório |
| PRs `feat`/`fix` mergeados desde 22/09 com arquivo de teste | 27 de 27 | `gh pr view --json files` |
| CI verde desde a Sprint 3 (05/10) | 33 de 35 execuções concluídas | `gh run list` |

## Regras destes documentos

1. **Todo número tem fonte** (comando e SHA, run do CI ou PR).
2. **O que não foi executado é dito como tal**, com o motivo.
3. **"Entregue" é o que está mergeado** em `homolog` ou `main`. A coluna do projeto e o estado da issue são só indícios.

## Como regerar

```bash
# 1. Checkout limpo da homolog
git worktree add --detach /tmp/qa-homolog origin/homolog && cd /tmp/qa-homolog

# 2. Backend: Postgres 16 temporário + migrations + pytest com cobertura
cd src/backend && pip install -r requirements.txt pytest-cov
export DATABASE_URL=postgresql://movecity@localhost:5432/movecity_test \
       JWT_SECRET=test-secret-for-ci-only JWT_ALGORITHM=HS256 JWT_EXPIRATION_MINUTES=60 ENVIRONMENT=test
alembic upgrade head
pytest -q --cov=auth --cov=colaboracao --cov=gateway --cov=mobilidade --cov=shared --cov-report=term

# 3. Frontend
cd ../frontend && npm ci && npx jest --coverage --silent

# 4. PRs e CI
gh pr list --state merged --search "merged:>=2026-09-22" --limit 100 --json number,title,author,mergedAt
gh run list --limit 1000 --json databaseId,workflowName,conclusion,createdAt,updatedAt,headBranch
```
