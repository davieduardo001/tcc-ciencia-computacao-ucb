# Gerenciar Branches do Projeto

Garante que o desenvolvimento siga o fluxo correto por tipo de branch.

## Fluxo obrigatório

```
feat/nome-da-feature   ──► homolog ──► main
fix/nome-da-correcao   ──► homolog ──► main
docs/atualizacao               ──────► main  (direto)
chore/configuracao             ──────► main  (direto)
```

- `feat/` e `fix/` passam por `homolog` — risco de quebrar comportamento funcional.
- `docs/` e `chore/` vão direto para `main` — sem risco funcional.
- Novas branches `feat/` e `fix/` são criadas a partir de `homolog`.
- **NUNCA** mergear `feat/` ou `fix/` direto em `main`.

## Instruções

1. Execute `git branch` para listar as branches existentes e identificar a branch atual.
2. Apresente ao usuário a lista de branches ativas e pergunte:
   - "Deseja criar uma nova branch? Qual o tipo (feat/fix/docs/chore)?"
   - "Deseja commitar em uma das branches existentes? (Liste-as)"
   - "Deseja continuar na branch atual `[nome da branch]`?"
3. Se o usuário optar por uma nova branch, sugira um nome seguindo o padrão e crie a partir da base correta:
   - `feat/nome` ou `fix/nome` → base: `homolog`
   - `docs/nome` ou `chore/nome` → base: `main`
4. Só proceda com o commit após a definição da branch de destino.
5. Ao finalizar, oriente o merge conforme o tipo da branch.
6. Toda a interação deve ser em **Português (PT-BR)**.

## Comandos úteis

```bash
git branch

# feat/ e fix/ — a partir de homolog
git checkout homolog && git checkout -b feat/nome
git checkout homolog && git checkout -b fix/nome

# docs/ e chore/ — a partir de main
git checkout main && git checkout -b docs/nome
git checkout main && git checkout -b chore/nome

# Merge feat/fix → homolog → main
git checkout homolog && git merge feat/nome
git checkout main && git merge homolog

# Merge docs/chore → main (direto)
git checkout main && git merge docs/nome
```

---

**Uso:** `/gerenciar-branches`
