# Gerenciar Commits Estruturados

Garante que os commits sejam atômicos, sigam Conventional Commits e se encaixem no fluxo correto por tipo de branch.

## Instruções

1. **Verificar branch primeiro** — use `/gerenciar-branches` para confirmar em qual branch as alterações devem ir e que o fluxo está correto.
2. Execute `git status` e `git diff` para identificar todas as mudanças pendentes.
3. **Agrupe logicamente:** mudanças em `docs/` e `src/` devem ser commits separados, salvo interdependência estrita.
4. **Conventional Commits obrigatório:**
   - `feat:` nova funcionalidade
   - `fix:` correção de bug
   - `docs:` apenas documentação
   - `style:` formatação sem mudança de lógica
   - `refactor:` refatoração sem fix/feat
   - `chore:` build, configurações
   - `perf:` otimização de performance
5. **Segurança:** verifique que arquivos ignorados (`.env`, `settings.local.json`) ou tokens não foram incluídos acidentalmente.
6. Antes de executar, apresente o plano ao usuário:
   - "Commit 1 (docs): Descrição..."
   - "Commit 2 (feat): Descrição..."
7. Mensagens de commit em inglês ou PT-BR; interação com o usuário sempre em **Português (PT-BR)**.

## Fluxo pós-commit

```
feat/ ou fix/  →  git checkout homolog && git merge feat/nome
                  git checkout main && git merge homolog

docs/ ou chore/  →  git checkout main && git merge docs/nome  (direto)
```

## Comandos úteis

```bash
git status
git diff
git add <arquivo>
git commit -m "tipo: mensagem"
```

---

**Uso:** `/gerenciar-commits`
