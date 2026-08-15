---
name: desenvolver-us-backend
description: Guia completo para desenvolver uma User Story no backend FastAPI, seguindo o workflow do projeto Movecity.
---

# Desenvolver User Story — Backend (FastAPI)

Esta skill orienta o desenvolvimento de uma US no backend, desde a leitura da spec até a abertura do PR.

## Pré-requisitos

- US aprovada no Sprint Backlog (critérios DOR atendidos)
- Branch `homolog` atualizada
- Diagrama de sequência correspondente em `docs/diagramas/sequencia/`
- Banco local rodando (usar `@dev-environment` ou `docker compose up -d`)

## Fluxo de Desenvolvimento

### 1. Preparação

```bash
# Atualizar homolog
git checkout homolog
git pull origin homolog

# Criar branch da feature
git checkout -b feat/issue-[numero]-[nome-curto]
```

**Setup local:** Se o banco não estiver rodando, usar `@dev-environment` ou rodar manualmente:
```bash
docker compose up -d
cd src/backend && alembic upgrade head
```

### 2. Estudar a US

- Ler a issue da US no GitHub (critérios de aceite)
- Ler o diagrama de sequência correspondente em `docs/diagramas/sequencia/`
- Identificar: atores, interface, gateway, serviços, modelos

### 3. Estrutura de Código

```
src/backend/
├── gateway/          # API Gateway (roteamento, rate limiting, proxy)
├── auth/             # Autenticação e autorização (JWT, login, registro)
├── mobilidade/       # Dados de mobilidade (GPS, linhas, paradas)
├── colaboracao/      # Reportes crowdsourced (ocorrências, notificações)
└── shared/           # Models, schemas, utilitários compartilhados
```

### 4. Desenvolver

- Seguir o diagrama de sequência fielmente
- Gateway sempre valida JWT localmente (sem round-trip ao Auth Service)
- Serviços de domínio recebem `identidadeUsuario` já validado
- Usar estereótipos: `<<servico gateway>>`, `<<servico [dominio]>>`, `<<modelo>>`

### 5. Migration (se alterou models)

```bash
cd src/backend

# Gerar migration a partir dos models
alembic revision --autogenerate -m "feat: descricao da alteracao"

# Aplicar migration localmente
alembic upgrade head

# Verificar migrations pendentes
alembic history
```

**NUNCA criar tabelas direto no Neon.** Sempre usar Alembic.

### 6. Testar

```bash
# Rodar testes do serviço específico
cd src/backend/[servico]
pytest
```

- Cada serviço deve ter pelo menos 1 teste passando
- Testar cenário principal e cenários alternativos (alt/else do diagrama)

### 7. Commitar

```bash
git add .
git commit -m "feat: [descrição curta no imperativo]"
```

- Seguir Conventional Commits
- Uma intenção por commit
- Max 72 caracteres na primeira linha

### 8. Abrir PR

```bash
git push -u origin feat/issue-[numero]-[nome-curto]
```

- Abrir PR: `feat/*` → `homolog`
- Preencher checklist do PR
- **NÃO fazer merge** — aguardar aprovação de 1 reviewer

### 9. Comentar na Issue

Comentar na issue da US:
> "PR aberto: [link do PR]. Aguardando review de [nome do reviewer]."

## Regras Obrigatórias

| Regra | Detalhe |
|-------|---------|
| Branch | `feat/issue-[numero]-[nome]` a partir de `homolog` |
| Commit | Conventional Commits (`feat:`, `fix:`, etc.) |
| Migrations | Sempre via Alembic — nunca criar tabelas direto |
| Testes | Pelo menos 1 teste passando por serviço |
| PR | Requires aprovação de 1 reviewer antes do merge |
| Merge | Só após aprovação + testes passando no CI |
| IA | Nunca incluir Co-Authored-By ou referência a ferramentas de IA |
