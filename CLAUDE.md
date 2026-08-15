# CLAUDE.md

Este arquivo fornece orientação ao Claude Code ao trabalhar com este repositório.

## Sobre o Projeto

**Movecity** — Aplicativo web de mobilidade urbana colaborativa para o DF (projeto-piloto em Taguatinga/Ceilândia). TCC do Grupo Segurança na UCB. Combina dados GPS do GDF com reportes crowdsourced para mitigar o "ônibus fantasma" e riscos de segurança.

**Fonte de verdade:** `AGENT.md` — stack, time, arquitetura, próximos passos.

## Idioma

Todo o conteúdo em **Português (PT-BR)**. Commits podem ser em inglês ou PT-BR (Conventional Commits).

## Regras Obrigatórias

- **NUNCA** commitar direto em `main` ou `homolog` sem confirmar com o usuário.
- **NUNCA** incluir `Co-Authored-By` ou assinatura de agente/IA nos commits.
- Mudanças em `docs/` e `src/` devem ser commits separados, salvo interdependência estrita.

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

## Skills do Agente

| Skill | Caminho | Quando usar |
|---|---|---|
| `resumir-documentacao` | `.claude/commands/resumir-documentacao.md` | Iniciar tarefas complexas |
| `gerenciar-branches` | `.claude/commands/gerenciar-branches.md` | Antes de qualquer commit |
| `gerenciar-commits` | `.claude/commands/gerenciar-commits.md` | Organizar commits atômicos |
| `gh-create-issue` | `.claude/commands/gh-create-issue.md` | Formalizar USs como issues |
| `gerar-diagrama-sequencia` | `.claude/commands/gerar-diagrama-sequencia.md` | Gerar diagramas UML PlantUML |

## Arquitetura de Diagramas de Sequência

- **`:GatewayAPI <<servico gateway>>`** entre frontend e backend — nunca ignorar
- Gateway valida JWT localmente (sem round-trip ao Auth Service)
- Serviços de domínio não conhecem sessão — recebem `identidadeUsuario` já validado
- Estereótipos: `<<interface usuario>>`, `<<servico gateway>>`, `<<servico autenticacao>>`, `<<servico [dominio]>>`, `<<modelo>>`
- Referência: `docs/diagramas/sequencia/` — UC14 a UC26

## Documentação de Contexto (carregada automaticamente)

@AGENT.md
@docs/distribuicao_us.md
@docs/documento_visao.md
