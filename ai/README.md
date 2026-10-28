# ai/ — agentes de IA do Movecity

Esta pasta é a **fonte única** de tudo que configura agentes de IA no projeto: regras, workflow, skills, agentes e configurações de cada ferramenta. O repositório não versiona mais `.claude/`, `.opencode/`, `.gemini/` nem `opencode.json`; essas pastas são geradas localmente a partir daqui.

```
CLAUDE.md  ──►  AGENT.md  ──►  ai/
(Claude Code)   (entrada       regras.md     regras de operação (branches, commits, PRs, diagramas, Gateway)
                 comum)        workflow.md   ciclo de sprint, DoR e DoD
                               skills/       15 skills, um SKILL.md por pasta
                               agents/       5 agentes especializados (formato OpenCode)
                               claude/       launch.json (servidor de desenvolvimento do frontend)
                               gemini/       settings.json.example (servidor MCP do GitHub)
                               opencode/     opencode.json (agentes, permissões e modos)
                               instalar.sh   cria os atalhos que cada ferramenta espera
```

## Como usar depois de clonar

```bash
./ai/instalar.sh            # cria .claude/, .opencode/, .gemini/ e opencode.json como links para ai/
./ai/instalar.sh --remover  # desfaz os links
```

Os links ficam no `.gitignore`. Cada ferramenta lê a mesma pasta `ai/skills/`:

| Ferramenta | O que lê | Como |
|---|---|---|
| **Claude Code** | `CLAUDE.md` → `AGENT.md` → `ai/regras.md`; skills como comandos `/nome` | `.claude/skills` aponta para `ai/skills` |
| **OpenCode** | `opencode.json`, skills e agentes | `opencode.json`, `.opencode/skills` e `.opencode/agents` apontam para `ai/` |
| **Gemini CLI** | skills; configuração do servidor MCP | `.gemini/skills` aponta para `ai/skills`; copie `ai/gemini/settings.json.example` para `.gemini/settings.json` e coloque o seu token (o arquivo real fica fora do Git) |

Os **agentes** (`ai/agents/`) estão no formato do OpenCode (`mode: subagent`) e por isso só o OpenCode os usa; o formato de subagente do Claude Code é outro.

## Skills

| Skill | Para que serve |
|---|---|
| [`criar-diagrama`](skills/criar-diagrama/SKILL.md) | Guia para criar e validar diagramas de sequência PlantUML no projeto Movecity, seguindo os padrões do CLAUDE.md. |
| [`criar-issue-sprint`](skills/criar-issue-sprint/SKILL.md) | Cria uma issue e opcionalmente a vincula à sprint corrente. |
| [`criar-testes`](skills/criar-testes/SKILL.md) | Guia para criar testes unitários com pytest (backend) e testes de componentes (frontend) no projeto Movecity. |
| [`desenvolver-us-backend`](skills/desenvolver-us-backend/SKILL.md) | Guia completo para desenvolver uma User Story no backend FastAPI, seguindo o workflow do projeto Movecity. |
| [`desenvolver-us-frontend`](skills/desenvolver-us-frontend/SKILL.md) | Guia completo para desenvolver uma User Story no frontend Next.js, seguindo o workflow do projeto Movecity. |
| [`gerar-diagrama-sequencia`](skills/gerar-diagrama-sequencia/SKILL.md) | Gera diagramas de sequência UML em PlantUML seguindo a arquitetura real do Movecity — microserviços com API Gateway (US #31) entre frontend e backend. |
| [`gerenciar-branches`](skills/gerenciar-branches/SKILL.md) | Garante que o projeto utilize o fluxo correto por tipo de branch — feat/fix passam por homolog antes de main; docs/chore vão direto para main. |
| [`gerenciar-commits`](skills/gerenciar-commits/SKILL.md) | Garante que os commits do projeto sejam atômicos, sigam o padrão Conventional Commits e se encaixem no fluxo correto — feat/fix via homolog, docs/c... |
| [`gerenciar-sprint`](skills/gerenciar-sprint/SKILL.md) | Gerencia sprints: listar issues, verificar andamento e sugerir objetivos. |
| [`gh-create-issue`](skills/gh-create-issue/SKILL.md) | Formaliza uma User Story como issue do GitHub com o gh CLI. |
| [`resumir-documentacao`](skills/resumir-documentacao/SKILL.md) | Esta skill permite ao agente de IA ler, analisar e resumir a documentação existente do projeto (docs/ e AGENT.md), fornecendo uma visão geral clara... |
| [`review-pr`](skills/review-pr/SKILL.md) | Checklist e fluxo para revisar Pull Requests no projeto Movecity. |
| [`verificar-deploy`](skills/verificar-deploy/SKILL.md) | Verifica se o código está pronto para deploy antes de subir. |
| [`vincular-issues-sprint`](skills/vincular-issues-sprint/SKILL.md) | Vincula issues filhas à sprint corrente. |
| [`vincular-pr-issue`](skills/vincular-pr-issue/SKILL.md) | Guia para vincular Pull Requests a Issues no projeto Movecity. |

## Agentes

| Agente | Papel |
|---|---|
| [`backend`](agents/backend.md) | Agente especializado em desenvolvimento backend com FastAPI para o projeto Movecity. |
| [`dev-environment`](agents/dev-environment.md) | Gerencia infraestrutura local: Docker, migrations, dependências. NÃO edita código. |
| [`frontend`](agents/frontend.md) | Agente especializado em desenvolvimento frontend com Next.js para o projeto Movecity. |
| [`reviewer`](agents/reviewer.md) | Agente de review de código — apenas analisa e comenta, NUNCA faz alterações ou merge. |
| [`tester`](agents/tester.md) | Agente especializado em criar e rodar testes unitários para o projeto Movecity. |

## Como criar ou alterar uma skill

1. Crie `ai/skills/<nome>/SKILL.md` com o cabeçalho `name` (igual ao nome da pasta) e `description` (uma ou duas frases dizendo **quando** usar).
2. Escreva em português (PT-BR). Arquivos de apoio vão em `ai/skills/<nome>/assets/`.
3. Registre a skill na tabela acima.
4. Mudanças em `ai/` são `chore/` (vão direto para `main`, conforme [`regras.md`](regras.md)).

## Regras que valem para todos

- Nunca incluir `Co-Authored-By` ou assinatura de IA em commits, PRs ou comentários de issue.
- Nunca fazer commit direto em `main` ou `homolog`, nem merge de PR, sem confirmar com a pessoa responsável.
- Todo PR está ligado a uma issue (`Closes #N`).
- Toda afirmação de que algo funciona vem de ter rodado e lido o resultado, não de suposição.

O texto completo está em [`regras.md`](regras.md) e em [`docs/boas-praticas-ia.md`](../docs/boas-praticas-ia.md).
