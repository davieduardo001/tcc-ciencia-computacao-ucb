# Criar Issue no GitHub (gh-create-issue)

Formaliza uma User Story (US) como GitHub Issue, mantendo o corpo principal focado no valor do usuário e detalhes técnicos/produto em comentários separados.

## Instruções

1. **Granularidade atômica:** garanta que a US seja atômica. Ex: em vez de uma US "Autenticação", use USs separadas para "Login", "Criação de Conta" e "Login Social".

2. **Rascunhe o conteúdo:**
   - **Corpo principal (US):** formato padrão (As a... / I want... / So that...) + cenários BDD.
   - **Comentário PRD:** objetivos de negócio, mudanças de UI e regras de negócio.
   - **Comentário SPEC:** arquitetura, modelos de dados, APIs e performance.

3. **Execute em sequência:**
   ```bash
   ISSUE_URL=$(gh issue create --title "[US] Título" --body "$(cat body_us.md)")
   gh issue comment "$ISSUE_URL" --body "$(cat prd.md)"
   gh issue comment "$ISSUE_URL" --body "$(cat spec.md)"
   ```

4. Sempre use **Português (PT-BR)** e siga os templates em `docs/templates/`.

## Referências

- Template: `docs/templates/Template_User_Stories.md`
- Documento de Visão: `docs/documento_visao.md`

---

**Uso:** `/gh-create-issue [descrição da US]`
