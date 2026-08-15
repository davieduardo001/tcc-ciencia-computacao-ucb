# Workflow Movecity — Passo a Passo (com Agente de IA)

Manual prático de como executar o ciclo completo de desenvolvimento no Movecity **usando um agente de IA** (Claude Code ou OpenCode) — do clone do repositório até a US rodando em produção. O trabalho é agêntico: você não digita `git`/`gh` na mão, você diz pro agente o que precisa e confere o que ele fez.

As regras e o porquê de cada uma estão em `docs/guia-contribuicao.md` (gitflow/commits) e `docs/boas-praticas-ia.md` (o que o agente pode fazer sozinho vs. precisa de confirmação sua). Um estudo de caso real disso tudo acontecendo está em `docs/relato-deploy-sprint0.md`.

---

## 0. Clonar o repositório e abrir o agente

```bash
git clone https://github.com/davieduardo001/tcc-ciencia-computacao-ucb.git
cd tcc-ciencia-computacao-ucb
```

Abra o agente **de dentro dessa pasta** — o contexto do projeto (`CLAUDE.md`/`AGENT.md` pro Claude Code, `opencode.json`/`.opencode/` pro OpenCode) é carregado automaticamente porque ele lê os arquivos do repositório.

| Ferramenta | Como abrir |
|---|---|
| Claude Code | `claude` no terminal |
| OpenCode | `opencode` no terminal |

Na primeira mensagem, o agente já sabe: quem é o time, qual sua US (se você disser o número), a arquitetura, as regras de commit/branch. Não precisa colar contexto — só pedir.

---

## 1. Pegar uma US

Fale com o agente:

> "Lê a issue #23 e me explica o que precisa ser feito."

Ele vai buscar a issue no GitHub (`gh issue view`), ler o diagrama de sequência correspondente em `docs/diagramas/sequencia/` e te devolver um resumo. É o momento de tirar dúvida antes de qualquer código ser escrito — no Claude Code, isso normalmente entra em modo de planejamento; no OpenCode, é o **Plan Mode**.

---

## 2. Criar a branch

> "Cria a branch pra US #23."

O que o agente executa por baixo:

```bash
git checkout homolog && git pull origin homolog
git checkout -b feat/issue-23-reportar-ocorrencia
```

Confirme que o nome da branch bate com o padrão (`feat/issue-[numero]-[nome-curto]`) antes de seguir.

---

## 3. Implementar

> "Implementa a US #23 seguindo o diagrama de sequência."

O agente vai criar/editar os arquivos necessários (endpoints, models, componentes). **Revise o que ele fez antes de aprovar** — peça pra ele te mostrar o diff (`git diff`) ou explicar as mudanças se algo não ficou claro. Você é quem confirma que o código faz sentido, não só que "rodou".

---

## 4. Testar

> "Roda os testes."

O agente executa `pytest -v` (backend) e/ou `npm test` (frontend) e te mostra o resultado real — não aceite um "deve estar passando", peça o output.

Se algo falhar, peça pra ele investigar e corrigir antes de seguir pro commit.

---

## 5. Commitar

> "Commita seguindo Conventional Commits."

O agente monta a mensagem (`feat:`, `fix:`, etc.), separa `docs/` de `src/` se for o caso, e **nunca** inclui `Co-Authored-By` ou menção a ferramenta de IA — isso é regra fixa, não precisa pedir.

---

## 6. Abrir o PR

> "Sobe a branch e abre o PR pra homolog."

```bash
git push -u origin feat/issue-23-reportar-ocorrencia
gh pr create --base homolog --title "..." --body "..."
```

O agente preenche o template do PR e referencia a issue (`Closes #23`).

[anexar imagem: tela de abertura de PR no GitHub com o template preenchido]

---

## 7. Acompanhar o CI

> "Acompanha o CI do PR e me avisa se passar ou falhar."

O agente roda `gh pr checks`/`gh run watch` e reporta o resultado real, não assume. Se falhar, ele investiga a causa antes de propor correção — não sai chutando fix.

[anexar imagem: aba "Checks" do PR com os 3 jobs verdes]

---

## 8. Pedir review (humano) e confirmar aprovação

Review é etapa humana — peça pra 1 pessoa do time revisar o PR. Passe esse caminho pra quem for aprovar:

1. Abrir o PR → aba **"Files changed"** (não "Conversation")
2. Rolar até o fim → **"Review changes"** → **"Approve"** → **"Submit review"**

Um comentário de texto ("revisado", "ok") **não conta**. Depois, peça pro agente confirmar de verdade:

> "Confirma se o PR #23 já foi aprovado formalmente."

Ele checa `reviewDecision` via `gh pr view` — só segue se vier `APPROVED`.

[anexar imagem: aba Files changed com o botão "Review changes" em destaque]

---

## 9. Merge para homolog

> "Pode mergear o PR #23."

O agente **deve confirmar com você antes de mergear**, mesmo com CI verde e aprovação — isso é regra (`docs/boas-praticas-ia.md`). Ele nunca decide sozinho bypassar a branch protection; se isso for necessário, é decisão sua, explícita, registrada na issue.

O merge dispara o deploy automático de homologação (Vercel + Fly.io, se tocou em `src/backend/**`).

[anexar imagem: workflow de deploy rodando após o merge]

---

## 10. Validar em homolog

> "Confirma que os endpoints da US #23 estão respondendo em homolog."

O agente valida de verdade (`curl`, não só "o deploy deve ter funcionado"). Para telas, use a URL de preview que a Vercel gera por branch.

---

## 11. PR homolog → main e produção

Mesmo ciclo dos passos 6 a 10, trocando a base do PR pra `main`:

> "Abre o PR de homolog pra main."

Mesmas regras: CI verde, aprovação formal, confirmação sua antes do merge.

[anexar imagem: os serviços respondendo em produção após o merge]

---

## 12. Fechar o ciclo

> "Comenta na issue #23 que foi pra produção."

O agente comenta o resultado na issue (sem mencionar que uma IA fez o trabalho — só o resultado). Se a issue não fechou sozinha via "Closes #23", peça pra fechar manualmente.

---

## Checklist rápido

- [ ] Repositório clonado, agente aberto de dentro da pasta
- [ ] Issue e diagrama de sequência lidos antes de codar
- [ ] Branch criada a partir da base certa
- [ ] Código revisado por você, não só "rodou"
- [ ] Testes passando local (output real, não suposição)
- [ ] Commits seguem Conventional Commits, sem menção a IA
- [ ] PR aberto com template preenchido
- [ ] CI verde
- [ ] Review **formal** (`reviewDecision: APPROVED`), não só comentário
- [ ] Agente pediu sua confirmação antes de cada merge
- [ ] Validado em homolog e em produção de verdade (curl/tela), não por suposição
- [ ] Issue comentada/fechada
