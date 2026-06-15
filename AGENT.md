# AGENT.md - TCC Ciência da Computação UCB (Movecity)

Este arquivo é a fonte única de verdade (Single Source of Truth) para agentes de IA que colaboram neste projeto. Ele consolida as diretrizes de desenvolvimento, regras acadêmicas e o fluxo de trabalho agêntico.

## 📋 Resumo do Projeto
- **Título:** Movecity - Mobilidade Urbana Colaborativa no DF
- **Objetivo:** Mitigar falhas de comunicação no transporte público do DF através de uma plataforma web colaborativa (GPS + Reporte Humano).
- **Autor:** @doritos (Grupo Segurança no Transporte)
- **Status:** Fase de Planejamento e Especificação.

## 🛠️ Stack Tecnológica

- **Metodologia:** Agentic Workflow & Lean Inception.
- **Frontend:** Next.js (React framework — App Router).
- **Mapa/GPS:** Leaflet JS + OpenStreetMap tiles (gratuito, open source). Integração com API GPS do GDF via GeoJSON.
- **Backend:** FastAPI (Python) — deploy no Fly.io.
- **Banco de Dados:** PostgreSQL gerenciado no Neon (serverless).
- **CI/CD:** GitHub Actions.
- **Dados:** Integração GPS (GDF) + Crowdsourcing colaborativo.
- **Ambiente:** Linux.

## 🧩 Habilidades Ativas (Skills)
- **resumir-documentacao:** Lê e sintetiza a documentação em `docs/` e `AGENT.md`. **Sempre use esta skill ao iniciar tarefas complexas.**
- **gerenciar-branches:** Garante o uso organizado de branches. **Obrigatório:** Listar branches e perguntar ao usuário antes de qualquer commit.
- **gerenciar-commits:** Executa commits atômicos (Conventional Commits) integrados à verificação de branch.
- **gh-create-issue:** Cria issues no GitHub com formato completo (User Story, SPEC e PRD) utilizando a ferramenta de linha de comando `gh`.
- **gerar-diagrama-sequencia:** Gera diagramas de sequência UML em PlantUML com arquitetura Gateway + validação de sessão (US #31).

## 🌿 Fluxo de Branches

```
feat/nome-da-feature   ──► homolog ──► main
fix/nome-da-correcao   ──► homolog ──► main
docs/atualizacao               ──────► main  (direto)
chore/configuracao             ──────► main  (direto)
```

- Branches `feat/` e `fix/` passam obrigatoriamente por `homolog` — risco de quebrar comportamento funcional.
- Branches `docs/` e `chore/` vão diretamente para `main` — sem risco funcional.
- Novas branches `feat/` e `fix/` são criadas a partir de `homolog`.
- **NUNCA** commitar ou fazer merge de `feat/` ou `fix/` direto em `main`.

## 📏 Diretrizes Gerais e Regras de Atuação
1. **Idioma:** O idioma oficial é **Português (PT-BR)** para documentação, comentários e interações.
2. **Proatividade Agêntica:** O agente deve atuar como um colaborador sênior, sugerindo arquiteturas, temas de pesquisa e metodologias alinhadas ao estado da arte.
3. **Sincronização de Contexto:** Sempre utilize os modelos em `docs/templates/` para manter a consistência acadêmica exigida pela UCB.
4. **Confirmação de Branch:** NUNCA faça um commit direto sem antes validar a estratégia de branch com o usuário. Fluxo: `feat/*` e `fix/*` → `homolog` → `main`; `docs/*` e `chore/*` → direto em `main`.
5. **Identidade nos Commits:** SEMPRE use o usuário autenticado no `gh` CLI (`davieduardo001`) para qualquer operação git/GitHub. NUNCA inclua co-autoria ou referência a ferramentas de IA (Claude, Gemini, etc.) nas mensagens de commit ou PRs.
6. **Rigor Acadêmico:** As sugestões e o código devem seguir padrões científicos e de engenharia de software de alto nível.
7. **Documentação Contínua:** Este arquivo deve ser atualizado periodicamente para refletir o estado real do projeto.

## 📁 Estrutura do Projeto
```text
tcc-ciencia-computacao-ucb/
├── .gemini/          # Configurações e Skills do Agente
├── AGENT.md          # Manual de bordo e diretrizes (Substitui GEMINI.md)
├── docs/             # Documentação acadêmica e técnica
│   ├── templates/    # Modelos da UCB (ESCDU, DRS, Visão, etc.)
│   └── documento_visao.md
└── src/              # Código fonte (em breve)
```

## 🏗️ Arquitetura da Aplicação

```
[Usuário - Browser]
      │
      ▼
[Frontend Web - React ou Angular]
      │  Leaflet JS + OSM tiles
      │  Dados GPS em tempo real (GeoJSON)
      ▼
[Backend - Fly.io]
      │
      ├──► API GPS GDF (integração externa)
      │
      └──► [PostgreSQL - Neon]
              └── Usuários, reportes colaborativos, rotas preferidas
```

**Decisões arquiteturais registradas:**
- Mapa via **Leaflet JS** (gratuito, sem risco de estourar free tier em apresentações)
- Tiles via **OpenStreetMap** (gratuito)
- Backend hospedado no **Fly.io** (deploy simples via Docker)
- Banco **PostgreSQL no Neon** (serverless, free tier generoso para TCC)
- **GitHub Actions** para pipeline CI/CD (testes, build, deploy automático)

## 🚀 Próximos Passos
1. Definir framework frontend (React ou Angular).
2. Modelar banco de dados (entidades: Usuário, Linha, Parada, Reporte).
3. Iniciar User Stories e issues no GitHub.
4. Configurar pipeline CI/CD no GitHub Actions.

---
*Atualizado conforme as novas diretrizes de consolidação de contexto.*
