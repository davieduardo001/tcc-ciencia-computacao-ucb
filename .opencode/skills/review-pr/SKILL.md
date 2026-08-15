---
name: review-pr
description: Checklist e fluxo para revisar Pull Requests no projeto Movecity. O reviewer NÃO faz merge — apenas comenta e aprova.
---

# Review de Pull Request

Esta skill define o fluxo de review de PRs no projeto Movecity.

## Fluxo de Review

### 1. Receber Notificação

- Verificar PRs pendentes em `homolog` ou `main`
- Ler a descrição do PR e os commits incluídos

### 2. Analisar o Código

Usar o checklist abaixo para guiar a revisão.

### 3. Comentar na PR

- Comentar achados (positivos e negativos)
- Sugerir melhorias quando aplicável
- Aprovar ou solicitar alterações

### 4. Comentar na Issue

Comentar na issue da US:
> "Review realizado: [aprovado/solicitar alterações]. PR: [link]. Comentários: [resumo]."

## Checklist de Review

### Código

- [ ] Código segue a estrutura de pastas do projeto
- [ ] Funções/métodos são coesos (uma responsabilidade)
- [ ] Nomes são descritivos (variáveis, funções, componentes)
- [ ] Não há código duplicado desnecessário
- [ ] Tratamento de erros está presente

### Workflow

- [ ] Branch nomeada corretamente (`feat/issue-[numero]-[nome]`)
- [ ] Commits seguem Conventional Commits
- [ ] PR aponta para a branch correta (`homolog` para feat/fix)
- [ ] Descrição do PR está completa

### Testes

- [ ] Testes unitários estão presentes
- [ ] Testes passam localmente
- [ ] Cobertura mínima atendida (1 teste por serviço/componente)

### Segurança

- [ ] Não há senhas ou chaves expostas
- [ ] Não há referências a IA nas mensagens de commit
- [ ] Dados sensíveis não são logados

### Arquitetura

- [ ] Gateway valida JWT localmente (sem round-trip)
- [ ] Serviços de domínio recebem `identidadeUsuario` já validado
- [ ] Diagrama de sequência foi seguido

## Regras de Aprovação

| Aprovação | Quando |
|-----------|--------|
| **Approved** | Todos os itens do checklist atendidos |
| **Approved with suggestions** | Maioria atendida, melhorias pontuais |
| **Rejected** | Problemas críticos que impedem o merge |

## Importante

- **Reviewer NÃO faz merge** — apenas comenta e aprova
- Merge é feito após aprovação + testes passando no CI
- PR requer **1 reviewer** no mínimo
- **Squash merge** para `feat/*` e `fix/*`
- Branch feature é **deletada** após merge

## Branch Protection

As branches `main` e `homolog` estão protegidas:

| Regra | Status |
|-------|--------|
| Require 1 approval | ✅ Ativo |
| Require status checks (CI) | ✅ Ativo |
| Dismiss stale reviews | ✅ Ativo |
| Require conversation resolution | ✅ Ativo |
| Block force pushes | ✅ Ativo |
| Block deletions | ✅ Ativo |

**Implicações:**
- PR sem approval não pode ser mergeado
- CI precisa passar antes do merge
- Force push é bloqueado
- Branches protegidas não podem ser deletadas
