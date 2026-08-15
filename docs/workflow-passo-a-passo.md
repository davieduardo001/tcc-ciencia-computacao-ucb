# Workflow Movecity — Passo a Passo

Manual prático de como executar o ciclo completo de desenvolvimento no Movecity, do início de uma User Story até ela estar rodando em produção. É o "como fazer" — as regras e o porquê de cada uma estão em `docs/guia-contribuicao.md` (gitflow/commits) e `docs/boas-praticas-ia.md` (uso de IA no processo). Um estudo de caso real disso tudo acontecendo está em `docs/relato-deploy-sprint0.md`.

Use este documento como checklist toda vez que for pegar uma US ou corrigir um bug.

---

## Visão geral do ciclo

```
1. Criar branch (a partir de homolog, pra feat/fix)
2. Desenvolver + testar local
3. Commit (Conventional Commits)
4. Push + abrir PR para homolog
5. CI roda automaticamente
6. Pedir review → aprovação formal
7. Merge para homolog → deploy automático de homologação
8. Validar em homolog
9. Abrir PR homolog → main
10. Review + merge → deploy automático de produção
11. Validar em produção + comentar na issue
```

---

## 1. Criar a branch

Sempre a partir de `homolog` atualizado (`feat/`, `fix/`) ou `main` atualizado (`docs/`, `chore/`):

```bash
git checkout homolog
git pull origin homolog
git checkout -b feat/issue-[numero]-[nome-curto]
```

Nomeação: kebab-case, sempre prefixado pelo tipo (`feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`). Detalhes: `docs/guia-contribuicao.md`.

---

## 2. Desenvolver e testar localmente

- Leia a issue da US e o diagrama de sequência correspondente antes de codar.
- Implemente seguindo a estrutura de pastas do projeto.
- Rode os testes **antes** de commitar:

```bash
# Backend
cd src/backend && pytest -v

# Frontend
cd src/frontend && npm test
```

Não abra PR com teste falhando local — o CI vai reprovar do mesmo jeito, só que mais devagar.

---

## 3. Commitar

```bash
git add <arquivos>
git commit -m "feat: descricao curta no imperativo"
```

- Um commit = uma intenção.
- Máximo 72 caracteres na primeira linha.
- Mudanças em `docs/` e `src/` em commits separados.
- **Nunca** `Co-Authored-By` ou menção a ferramenta de IA.

---

## 4. Push e abrir o PR

```bash
git push -u origin feat/issue-[numero]-[nome-curto]
gh pr create --base homolog --title "..." --body "..."
```

Preencha o template do PR (checklist + "Closes #[numero]" se a US for fechada por esse PR).

[anexar imagem: tela de abertura de PR no GitHub com o template preenchido]

---

## 5. Acompanhar o CI

O CI (`ci.yml`) dispara sozinho no PR: lint de commits, pytest, Jest. Acompanhe com:

```bash
gh pr checks <numero>
# ou, pra assistir em tempo real:
gh run watch <run-id>
```

Se algo falhar, corrija e dê push de novo na mesma branch — o CI roda de novo automaticamente.

[anexar imagem: aba "Checks" do PR com os 3 jobs verdes]

---

## 6. Pedir review e obter aprovação formal

Peça review a 1 pessoa do time (`gh pr edit <numero> --add-reviewer <usuario>` ajuda a formalizar o pedido).

**Importante:** só conta como aprovação o que for submetido pelo botão certo. Um comentário de texto ("revisado", "ok pra mim") não desbloqueia o merge.

Caminho pra quem for aprovar:
1. Abrir o PR
2. Ir na aba **"Files changed"** (não em "Conversation")
3. Rolar até o fim da página
4. Clicar em **"Review changes"**
5. Selecionar **"Approve"** → **"Submit review"**

[anexar imagem: aba Files changed com o botão "Review changes" em destaque]

[anexar imagem: dialog de review com a opção "Approve" selecionada]

Confirme a aprovação formal antes de mergear:

```bash
gh pr view <numero> --json reviewDecision -q .reviewDecision
# precisa retornar: APPROVED
```

---

## 7. Merge para homolog

Com CI verde e `reviewDecision: APPROVED`, mergeie (squash, pra manter o histórico limpo):

```bash
gh pr merge <numero> --squash
```

Isso dispara o deploy automático de homologação (frontend na Vercel, backend no Fly.io — se o PR tocou em `src/backend/**`).

[anexar imagem: workflow de deploy rodando após o merge]

---

## 8. Validar em homolog

Confirme que o que subiu funciona de verdade antes de prosseguir pra produção:

```bash
curl https://movecity-gateway.fly.dev/health
# e os endpoints relevantes da sua US
```

Para o frontend, a Vercel gera uma URL de preview própria por branch — use ela pra validar visualmente.

---

## 9. Abrir PR homolog → main

Quando o conjunto de mudanças em `homolog` estiver validado e pronto pra ir pra produção:

```bash
gh pr create --base main --head homolog --title "..." --body "..."
```

Mesmas regras do passo 6: precisa de aprovação formal, CI precisa passar.

---

## 10. Merge para main

```bash
gh pr merge <numero> --squash
```

Dispara o deploy automático de produção.

[anexar imagem: os serviços respondendo em produção após o merge]

---

## 11. Validar e fechar o ciclo

- Confirme os endpoints/telas em produção.
- Comente na issue da US com o resultado (`"PR mergeado: [link]. Rodando em produção."`).
- Se a issue não fechou automaticamente via "Closes #XX", feche manualmente.

---

## Checklist rápido

- [ ] Branch criada a partir da base certa
- [ ] Testes passando local antes do commit
- [ ] Commits seguem Conventional Commits, sem menção a IA
- [ ] PR aberto com template preenchido
- [ ] CI verde
- [ ] Review **formal** (`reviewDecision: APPROVED`), não só comentário
- [ ] Merge → validado em homolog
- [ ] PR homolog → main → validado em produção
- [ ] Issue comentada/fechada
