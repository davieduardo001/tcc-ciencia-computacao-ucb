# Regras para agentes de IA — Movecity

Regras de operação válidas para **qualquer** agente de IA no repositório (Claude Code, OpenCode, Gemini ou outro). O ponto de entrada é o [`AGENT.md`](../AGENT.md); as regras de como a IA deve agir no ciclo de sprint estão em [`docs/boas-praticas-ia.md`](../docs/boas-praticas-ia.md) e o ciclo completo, em [`workflow.md`](workflow.md).

## Idioma

Todo o conteúdo em **Português (PT-BR)**. Commits podem ser em inglês ou PT-BR (Conventional Commits).

## Regras Obrigatórias

- **NUNCA** commitar direto em `main` ou `homolog` sem confirmar com o usuário.
- **NUNCA** incluir `Co-Authored-By` ou assinatura de agente/IA nos commits, PRs ou comentários de issue.
- Mudanças em `docs/` e `src/` devem ser commits separados, salvo interdependência estrita.
- Regras completas de como a IA deve operar no workflow (bypass de branch protection, o que conta como aprovação de PR, verificação antes de declarar algo pronto): `docs/boas-praticas-ia.md`.

## Delegação por agente

Toda tarefa que mexe no repositório ou na plataforma (criar issue, implementar, testar, revisar, documentar) é executada por um **agente** de [`ai/agents/`](agents/). A conversa principal só **orquestra**: entende o pedido, escolhe o agente, delega e reporta o resultado.

| Tipo de tarefa | Agente |
|---|---|
| Escrever US, critérios de aceite, escopo; abrir e consultar issues e sprint | `analista` |
| Implementar uma issue de ponta a ponta, corrigir bug, branch, commits e PR | `dev` |
| Trabalho só no backend (FastAPI, modelos, migrations) | `backend` |
| Trabalho só no frontend (Next.js, mapa, telas) | `frontend` |
| Escrever e rodar testes, validar o comando de `teste` do `projeto.md` | `tester` |
| Revisar código e PR, validar o DoD (somente leitura) | `reviewer` |
| Documentação: DRS, arquitetura, QA, diagramas, PRD e SPEC | `redator` |
| Docker, migrations e dependências locais (não edita código) | `dev-environment` |

- **Uma tarefa, um agente.** Se cruza papéis (implementar e testar), divida em etapas na ordem `issue → PR → review → DoD`.
- **Passe o contexto completo:** o pedido original, o [`projeto.md`](../projeto.md), a issue e os arquivos relevantes. O agente não herda a conversa.
- **Exceção:** perguntas, explicações e ajustes triviais (ler um arquivo, corrigir uma linha) não precisam de agente.
- Em ferramenta sem subagentes, assuma o papel carregando `ai/agents/<nome>.md` e siga as regras dele na própria conversa.

### Precedência das regras

1. [`projeto.md`](../projeto.md): o contrato do projeto, o mais específico.
2. Este arquivo (`ai/regras.md`): vale sobre qualquer skill.
3. A skill ou o agente em uso.

## Vinculação de PRs a Issues

- **Toda PR** deve estar vinculada a uma Issue
- Se não existir issue, criar antes de abrir o PR
- Usar `Closes #<NUMERO>` no corpo do PR para auto-close
- Vincular na seção "Linked issues" da sidebar do PR

### Comando para vincular via CLI

```bash
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

## Fluxo de Branches

```
feat/* e fix/*   →  homolog  →  main
docs/* e chore/* →  main (direto)
```

- `feat/` e `fix/` são criadas a partir de `homolog`.
- `docs/` e `chore/` são criadas a partir de `main`.
- Detalhes completos: `docs/guia-contribuicao.md`

## Conventional Commits

| Tipo | Quando usar |
|---|---|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Apenas documentação |
| `style:` | Formatação sem mudança de lógica |
| `refactor:` | Refatoração sem fix/feat |
| `chore:` | Build, configurações |
| `perf:` | Otimização de performance |

## Arquitetura de Diagramas de Sequência

- **`:GatewayAPI <<servico gateway>>`** entre frontend e backend — nunca ignorar
- Gateway valida JWT localmente (sem round-trip ao Auth Service)
- Serviços de domínio não conhecem sessão — recebem `identidadeUsuario` já validado
- Estereótipos: `<<interface usuario>>`, `<<servico gateway>>`, `<<servico autenticacao>>`, `<<servico [dominio]>>`, `<<modelo>>`
- Referência: `docs/diagramas/sequencia/` — UC14 a UC26

## Gateway como Proxy (US #31)

O Gateway é o **ponto único de entrada** para todas as requisições do frontend.

### Regras de Proxy

| Regra | Detalhe |
|-------|---------|
| **Ponto único de entrada** | Todas as requisições passam pelo Gateway |
| **Frontend só fala com o Gateway** | Os serviços de domínio acessam o banco; o Gateway não |
| **Cookies httpOnly** | Gateway seta/limpa cookies de autenticação |
| **Roteamento por path** | `/api/auth/*` → Auth, `/api/mobilidade/*` → Mobilidade, `/api/colaboracao/*` → Colaboracao |

### Endpoints de Proxy

| Endpoint | Método | Destino |
|----------|--------|---------|
| `/api/auth/login` | POST | Auth Service |
| `/api/auth/registrar` | POST | Auth Service |
| `/api/auth/refresh` | POST | Auth Service |
| `/api/auth/logout` | POST | Auth Service |
| `/api/mobilidade/*` | GET/POST/PUT/DELETE | Mobilidade Service |
| `/api/colaboracao/*` | GET/POST/PUT/DELETE | Colaboracao Service |

### Arquivos do Gateway

| Arquivo | Responsabilidade |
|---------|------------------|
| `middleware.py` | Valida JWT do cookie em cada request |
| `jwt_validator.py` | Decodifica e valida tokens JWT |
| `dependencies.py` | `get_usuario_atual` para endpoints protegidos |
| `proxy.py` | Proxy genérico para serviços backend |
| `cookies.py` | Helper para setar/limpar cookies httpOnly |
| `config.py` | Configuração das URLs dos serviços |
| `routes.py` | Endpoints de proxy (auth, mobilidade, colaboracao) |
