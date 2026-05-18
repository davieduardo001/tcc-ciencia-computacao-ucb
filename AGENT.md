# AGENT.md - TCC Ciência da Computação UCB (Movecity)

Este arquivo é a fonte única de verdade (Single Source of Truth) para agentes de IA que colaboram neste projeto. Ele consolida as diretrizes de desenvolvimento, regras acadêmicas e o fluxo de trabalho agêntico.

## 📋 Resumo do Projeto
- **Título:** Movecity - Mobilidade Urbana Colaborativa no DF
- **Objetivo:** Mitigar falhas de comunicação no transporte público do DF através de uma plataforma web colaborativa (GPS + Reporte Humano).
- **Autor:** @doritos (Grupo Segurança no Transporte)
- **Status:** Fase de Planejamento e Especificação.

## 🛠️ Stack Tecnológica (Preliminar)
- **Metodologia:** Agentic Workflow & Lean Inception.
- **Frontend:** Aplicativo Web (Tecnologias a definir: React/Angular).
- **Dados:** Integração GPS (GDF) + Crowdsourcing.
- **Ambiente:** Linux (Fedora via Gemini CLI).

## 🧩 Habilidades Ativas (Skills)
- **resumir-documentacao:** Lê e sintetiza a documentação em `docs/` e `AGENT.md`. **Sempre use esta skill ao iniciar tarefas complexas.**
- **gerenciar-branches:** Garante o uso organizado de branches. **Obrigatório:** Listar branches e perguntar ao usuário antes de qualquer commit.
- **gerenciar-commits:** Executa commits atômicos (Conventional Commits) integrados à verificação de branch.
- **gh-create-issue:** Cria issues no GitHub com formato completo (User Story, SPEC e PRD) utilizando a ferramenta de linha de comando `gh`.

## 📏 Diretrizes Gerais e Regras de Atuação
1. **Idioma:** O idioma oficial é **Português (PT-BR)** para documentação, comentários e interações.
2. **Proatividade Agêntica:** O agente deve atuar como um colaborador sênior, sugerindo arquiteturas, temas de pesquisa e metodologias alinhadas ao estado da arte.
3. **Sincronização de Contexto:** Sempre utilize os modelos em `docs/templates/` para manter a consistência acadêmica exigida pela UCB.
4. **Confirmação de Branch:** NUNCA faça um commit direto sem antes validar a estratégia de branch com o usuário.
5. **Rigor Acadêmico:** As sugestões e o código devem seguir padrões científicos e de engenharia de software de alto nível.
6. **Documentação Contínua:** Este arquivo deve ser atualizado periodicamente para refletir o estado real do projeto.

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

## 🚀 Próximos Passos
1. Realizar brainstorming de temas potenciais para o TCC.
2. Definir a stack tecnológica final.
3. Iniciar a estrutura de documentação acadêmica baseada nos templates.

---
*Atualizado conforme as novas diretrizes de consolidação de contexto.*
