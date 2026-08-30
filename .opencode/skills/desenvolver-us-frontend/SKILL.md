---
name: desenvolver-us-frontend
description: Guia completo para desenvolver uma User Story no frontend Next.js, seguindo o workflow do projeto Movecity.
---

# Desenvolver User Story — Frontend (Next.js)

Esta skill orienta o desenvolvimento de uma US no frontend, desde a leitura da spec até a abertura do PR.

## Pré-requisitos

- US aprovada no Sprint Backlog (critérios DOR atendidos)
- Branch `homolog` atualizada
- Diagrama de sequência correspondente em `docs/diagramas/sequencia/`
- Dependências instaladas (usar `@dev-environment` ou `npm install`)

## Fluxo de Desenvolvimento

### 1. Preparação

```bash
# Atualizar homolog
git checkout homolog
git pull origin homolog

# Criar branch da feature
git checkout -b feat/issue-[numero]-[nome-curto]
```

**Setup local:** Se as dependências não estiverem instaladas, usar `@dev-environment` ou rodar manualmente:
```bash
cd src/frontend && npm install
```

### 2. Estudar a US

- Ler a issue da US no GitHub (critérios de aceite)
- Ler o diagrama de sequência correspondente em `docs/diagramas/sequencia/`
- Identificar: interface (telas), componentes, chamadas à API

### 3. Estrutura de Código

```
src/frontend/
├── app/                # App Router (Next.js 13+)
│   ├── (routes)/       # Groups de rotas
│   └── layout.tsx      # Layout raiz
├── components/         # Componentes React
│   ├── ui/             # Componentes de UI (botões, inputs, etc.)
│   └── features/       # Componentes de funcionalidades
├── lib/                # Utilitários, hooks, services
│   ├── api.ts          # Chamadas à API
│   └── hooks/          # Custom hooks
└── styles/             # Estilos globais
```

### 4. Desenvolver

- Seguir o diagrama de sequência para a interface
- View recebe input do usuário e valida formato localmente
- Chamar o Gateway API para operações autenticadas
- Usar Leaflet JS + OpenStreetMap para componentes de mapa
- Tratar cenários alternativos (alt/else do diagrama)

### 5. Testar

```bash
cd src/frontend
npm test
```

- Testar componentes principais
- Testar interações do usuário
- Verificar responsividade

### 6. Commitar

```bash
git add .
git commit -m "feat: [descrição curta no imperativo]"
```

- Seguir Conventional Commits
- Uma intenção por commit
- Max 72 caracteres na primeira linha

### 7. Abrir PR

```bash
git push -u origin feat/issue-[numero]-[nome-curto]
```

- Abrir PR: `feat/*` → `homolog`
- Preencher checklist do PR
- **NÃO fazer merge** — aguardar aprovação de 1 reviewer

### 8. Comentar na Issue

Comentar na issue da US:
> "PR aberto: [link do PR]. Aguardando review de [nome do reviewer]."

### 9. Fechar o ciclo (DoD)

Não é responsabilidade só do reviewer — quem desenvolveu acompanha até o fim:

- Após o merge em `homolog`, validar os critérios de aceite lá e comentar na issue: **"DoD-Sprint atendido: PR mergeado em homolog ([link]), critérios de aceite validados."**
- Quando o PR `homolog` → `main` for mergeado, validar em produção e comentar: **"DoD-Release atendido: em produção ([link/URL]). Issue fechada."** — e fechar a issue se não tiver fechado sozinha via "Closes #XX".

Critérios completos: `AGENT.md`, seção "Critérios DOD".

## Regras Obrigatórias

| Regra | Detalhe |
|-------|---------|
| Branch | `feat/issue-[numero]-[nome]` a partir de `homolog` |
| Commit | Conventional Commits (`feat:`, `fix:`, etc.) |
| Testes | Pelo menos 1 teste passando por componente principal |
| PR | Requires aprovação de 1 reviewer antes do merge |
| Merge | Só após aprovação + testes passando no CI |
| IA | Nunca incluir Co-Authored-By ou referência a ferramentas de IA |
