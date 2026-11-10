# projeto.md

Contrato do projeto, lido pelos agentes de `ai/agents/` e pelas skills. O formato segue o `projeto.model.md` do [friday](https://github.com/davieduardo001/friday).

```yaml
platform: github
repo: davieduardo001/tcc-ciencia-computacao-ucb
fluxo_branch: homolog-main        # feat/fix -> homolog -> main; docs/chore -> main
current_sprint: "Sprint 4"
teste:
  backend: "cd src/backend && pytest -q"
  frontend: "cd src/frontend && npm test"
arquitetura: docs/documento_arquitetura.md
templates_us: docs/templates/Template_User_Stories.md
prd_dir: docs/prd
spec_dir: docs/specs
```

## Notas

- `homolog` publica direto na produção (Vercel e Fly.io). Não há ambiente de homologação separado.
- `main` é protegida: exige 1 aprovação formal. Quem abre o PR não aprova o próprio; o bypass com `--admin` segue [`docs/boas-praticas-ia.md`](docs/boas-praticas-ia.md) e é registrado na issue.
- Regras de operação dos agentes: [`ai/regras.md`](ai/regras.md). Ciclo de sprint e DoD: [`ai/workflow.md`](ai/workflow.md).
