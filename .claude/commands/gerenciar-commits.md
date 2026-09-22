# Gerenciar Commits Estruturados

Garante que os commits sejam atômicos, sigam Conventional Commits e se encaixem no fluxo correto por tipo de branch.

## Instruções

1. **Verificação de Branch (Skill: gerenciar-branches):** Antes de qualquer commit, utilize a skill `gerenciar-branches` para confirmar em qual branch as alterações devem ir e que o fluxo está correto.
2. **Análise de Alterações:** Execute `git status` e `git diff` para identificar todas as mudanças pendentes.
3. **Agrupamento Lógico:** Separe as mudanças em grupos lógicos.
   - Mudanças em `docs/` não devem estar no mesmo commit que mudanças em `src/`, salvo interdependência estrita.
   - Funcionalidades distintas devem ter commits distintos.
4. **Padrão Conventional Commits:** Utilize obrigatoriamente os prefixos:
   - `feat:` Novas funcionalidades ou adições importantes.
   - `fix:` Correções de bugs.
   - `docs:` Alterações apenas em documentação.
   - `style:` Formatação, pontos e vírgulas, etc. (sem alteração de lógica).
   - `refactor:` Mudança de código que não corrige bug nem adiciona feature.
   - `chore:` Atualização de tarefas de build, configurações de ferramentas, etc.
   - `perf:` Mudanças de código focadas em performance.
5. **Verificação de Segurança:** Garanta que arquivos ignorados (`.env`, `settings.local.json`) ou tokens não foram incluídos acidentalmente.
6. **Proposta de Estrutura:** Antes de executar os commits, apresente ao usuário um plano:
   - "Commit 1 (docs): Descrição..."
   - "Commit 2 (feat): Descrição..."
7. **Fluxo pós-commit:** Após os commits, oriente o merge conforme o tipo de branch:
   - `feat/` ou `fix/`: merge em `homolog` → depois `homolog` em `main`
   - `docs/` ou `chore/`: merge direto em `main`
   - Se a branch fecha uma US, lembre de comentar DoD-Sprint/DoD-Release na issue após cada merge (`AGENT.md`, seção "Critérios DOD").
8. **Idioma:** Mensagens de commit preferencialmente em inglês ou português (PT-BR), mas a interação com o usuário sempre em **Português (PT-BR)**.

## Comandos úteis

```bash
git status
git diff
git add <arquivo>
git commit -m "tipo: mensagem"
```

---

**Uso:** `/gerenciar-commits`
