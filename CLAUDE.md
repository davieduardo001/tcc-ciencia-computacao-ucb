# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Sobre o Projeto

**Movecity** — Aplicativo web de mobilidade urbana colaborativa para o DF (projeto-piloto em Taguatinga/Ceilândia). TCC do grupo Segurança no Transporte na UCB. Combina dados GPS do GDF com reportes crowdsourced para mitigar o "ônibus fantasma" e riscos de segurança em paradas.

Stack preliminar: frontend web (React ou Angular, a definir), integração GPS via API do GDF, backend a definir. O `src/` ainda está vazio — o projeto está na fase de especificação.

## Idioma

Todo o conteúdo produzido — documentação, comentários, mensagens de interação — deve estar em **Português (PT-BR)**. Mensagens de commit podem ser em inglês ou PT-BR, mas seguindo Conventional Commits (ver abaixo).

## Fluxo de Branches (obrigatório)

```
feat/nome-da-feature   ──► homolog ──► main
fix/nome-da-correcao   ──► homolog ──► main
docs/atualizacao               ──────► main  (direto)
chore/configuracao             ──────► main  (direto)
```

- Branches `feat/` e `fix/` passam obrigatoriamente por `homolog` antes de `main` — risco de quebrar comportamento funcional.
- Branches `docs/` e `chore/` vão diretamente para `main` — sem risco funcional.
- Novas branches `feat/` e `fix/` são criadas a partir de `homolog`.
- **NUNCA** commitar ou fazer merge de `feat/` ou `fix/` direto em `main`.

## Comandos Git

```bash
# Verificar estado antes de qualquer commit
git status && git diff

# Listar branches ativas antes de commitar
git branch

# feat/ e fix/ — criadas a partir de homolog
git checkout homolog
git checkout -b feat/nome-da-feature
git checkout -b fix/correcao-bug

# docs/ e chore/ — criadas a partir de main (vão direto)
git checkout main
git checkout -b docs/atualizacao-doc
git checkout -b chore/configuracao

# Merge feat/fix: homolog primeiro, depois main
git checkout homolog && git merge feat/nome-da-feature
git checkout main && git merge homolog

# Merge docs/chore: direto para main
git checkout main && git merge docs/atualizacao-doc

# Criar issue no GitHub (requer gh CLI)
gh issue create --title "[US] Título" --body "$(cat arquivo_body.md)"
gh issue comment "$ISSUE_URL" --body "$(cat prd_comment.md)"
gh issue comment "$ISSUE_URL" --body "$(cat spec_comment.md)"
```

## Regra de Branch e Commit

**NUNCA** faça commit direto em `main` ou `homolog` sem confirmar com o usuário. Fluxo obrigatório:

1. `git branch` → apresentar branches ativas ao usuário
2. Perguntar: nova branch, branch existente, ou branch atual?
3. Só commitar após definição da branch
4. Merge: `feat/*` e `fix/*` → `homolog` → `main`; `docs/*` e `chore/*` → direto em `main`

**Autoria de commits:** Nunca incluir `Co-Authored-By` nem qualquer assinatura de agente/IA. O commit deve aparecer somente no nome do desenvolvedor.

**Conventional Commits obrigatórios:**
- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` apenas documentação
- `style:` formatação sem mudança de lógica
- `refactor:` refatoração sem fix/feat
- `chore:` build, configurações
- `perf:` otimização de performance

Mudanças em `docs/` e `src/` devem ser commits separados, salvo interdependência estrita.

## Estrutura de Documentação

```
docs/
├── documento_visao.md       # Documento de Visão do Movecity (fonte de verdade)
├── brainstorming.md         # Ideias de tema para o TCC
└── templates/
    ├── README.md            # Como usar os templates
    └── Template_User_Stories.md  # Template BDD para User Stories
```

Ao criar ou atualizar documentos acadêmicos, usar os templates em `docs/templates/` para manter conformidade com as normas da UCB. Documentos Word (`.dotx`) devem ser espelhados em Markdown em `docs/` para leitura por agentes.

## User Stories

Usar o template BDD em `docs/templates/Template_User_Stories.md`. Cada US deve ser atômica — ex: "Login", "Criação de Conta" e "Login Social" são três USs separadas, não uma US de "Autenticação".

Ao formalizar uma US como issue no GitHub, o corpo da issue contém apenas a US (formato As a.../I want.../So that... + cenários BDD). PRD e SPEC vão como comentários separados na mesma issue.

## Skills do Agente

As skills estão disponíveis em dois formatos:
- **Gemini CLI:** `.gemini/skills/<nome>/SKILL.md`
- **Claude Code:** `.claude/commands/<nome>.md` (invocar com `/nome`)

| Skill | Quando usar |
|---|---|
| `resumir-documentacao` | Ao iniciar tarefas complexas — lê e sintetiza `docs/` + `AGENT.md` |
| `gerenciar-branches` | Antes de qualquer commit |
| `gerenciar-commits` | Para organizar e executar commits atômicos |
| `gh-create-issue` | Para formalizar USs como issues no GitHub |
| `gerar-diagrama-sequencia` | Para gerar diagramas de sequência UML MVC em PlantUML |

## Arquitetura de Diagramas de Sequência

Todo diagrama de sequência do Movecity segue a arquitetura de microserviços com API Gateway. Regras invioláveis:

- **`:GatewayAPI <<servico gateway>>`** fica entre o frontend e qualquer serviço de backend — nunca ignorar
- **O Gateway valida o JWT localmente** (sem round-trip ao Auth Service) e decide: encaminhar, renovar sessão ou retornar 401
- **Serviços de domínio não conhecem sessão** — recebem apenas a requisição já autenticada com `identidadeUsuario`
- **Fluxo de renovação (US #31):** token expirado → Gateway chama `:ControladorAutenticacao` → `:ModeloSessao` → novo token → reencaminha requisição original (transparente)
- **Estereótipos:** `<<interface usuario>>` (View), `<<servico gateway>>` (Gateway), `<<servico autenticacao>>` (Auth), `<<servico [dominio]>>` (serviços), `<<modelo>>` (dados)
- **Fonte de verdade:** issues #11 (padrão de diagrama com Gateway) e #31 (SPEC do ciclo de sessão)
- **Referência de implementação:** `docs/diagramas/sequencia/` — UC14 a UC21 seguem este padrão

## Documentação de Contexto

Os arquivos abaixo são carregados automaticamente em toda sessão:

@AGENT.md
@docs/distribuicao_us.md
@docs/documento_visao.md
