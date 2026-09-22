# Boas Práticas de Uso de IA no Workflow — Movecity

Este documento define como agentes de IA (Claude Code, OpenCode, Gemini ou qualquer outro) devem operar dentro do workflow de desenvolvimento do Movecity. Ele não substitui o `docs/guia-contribuicao.md` (gitflow e commits) nem o `AGENT.md` (arquitetura e workflow de sprint) — complementa os dois com regras específicas de quando e como a IA pode agir, nascidas de casos reais que aconteceram no projeto.

Vale para qualquer ferramenta de IA usada no repositório, não só uma específica.

---

## Princípio geral

A IA é ferramenta, o desenvolvedor é responsável. Toda ação que a IA executa no repositório — commit, PR, comentário em issue, deploy, mudança de configuração — é feita **em nome de quem está conduzindo a sessão**, não da ferramenta. Isso tem consequências práticas nas seções abaixo.

---

## Autoria e atribuição

- **Nunca** incluir `Co-Authored-By` ou qualquer referência a ferramentas de IA (Claude, Gemini, OpenCode, etc.) em commits, PRs ou comentários de issue.
- Nunca comentar em issues ou PRs do GitHub dizendo que uma IA ajudou, gerou ou implementou algo — o histórico deve registrar apenas o trabalho, não a ferramenta usada para chegar lá.
- Isso já era regra no `CLAUDE.md`; este documento só reforça o motivo: o repositório é acadêmico (TCC) e a autoria do trabalho é do time.

---

## O que a IA pode fazer sem perguntar

Ações reversíveis, dentro do escopo já combinado com o usuário na conversa:

- Ler código, rodar testes localmente, investigar bugs, rodar `git status`/`git log`/`git diff`
- Criar/editar arquivos de código, docs e configuração
- Criar branches, commitar, dar push em branches **não-protegidas**
- Rodar `flyctl deploy`, `alembic upgrade`, instalar dependências, gerar secrets (tokens de escopo mínimo, nunca reaproveitar token pessoal de acesso total)

## O que precisa de confirmação explícita antes de agir

- **Deletar recursos em produção** (apps, bancos, branches protegidas) — mesmo que reversível via recriação, tem custo/risco real
- **Merge de PR** — sempre perguntar antes, mesmo com CI verde
- **Bypass de branch protection** — ver seção dedicada abaixo
- **Editar issues/PRs de terceiros** ou mencionar pessoas do time
- Qualquer ação fora do que foi pedido na conversa atual (não generalizar uma aprovação anterior para uma ação nova)

---

## Bypass de branch protection: quando e como

`main` e `homolog` são protegidas por design — 1 aprovação obrigatória, CI obrigatório. Isso **não muda** por a IA estar conduzindo a sessão.

Só existe uma situação em que um merge sem aprovação é aceitável: quando o próprio objetivo do trabalho é testar o workflow/CI/CD em si (como foi o caso da issue #35). Mesmo aí:

1. O bypass é decisão do usuário, nunca da IA por conta própria.
2. **Todo bypass precisa ser registrado explicitamente** — comentário na issue relevante, dizendo que houve bypass, por quê, e que normalmente isso bloquearia o merge. Rastreabilidade em primeiro lugar; não existe "bypass silencioso".
3. Fora de um teste de workflow deliberado, bypass de branch protection não deve acontecer — nem em cenários de urgência. Se há urgência real, isso é conversa para o time, não uma decisão unilateral tomada durante a sessão.

---

## O que conta como aprovação de PR

Lição aprendida na prática durante a issue #35: um **comentário** de texto na conversa do PR (ex.: "Revisado.", "ok pra mim") **não é uma aprovação formal** e não satisfaz a branch protection do GitHub. A única coisa que conta é um review submetido pelo botão **"Review changes" → "Approve"**, na aba **"Files changed"** do PR.

Se a IA estiver aguardando aprovação e vir um comentário de texto na PR, não deve interpretar isso como sinal verde para merge — precisa confirmar se foi um review formal (`reviewDecision: APPROVED` via `gh pr view`) antes de prosseguir.

---

## Verificação antes de declarar algo pronto

Nunca afirmar que testes passam, CI está verde, ou deploy funcionou sem checar de fato:

- Rodar o comando e ler o output, não assumir pelo histórico da conversa
- Depois de um push/merge, checar o resultado real do CI/CD (`gh run watch`, `gh pr checks`), não só assumir que vai passar porque passou local
- Depois de um deploy, validar o endpoint de verdade (`curl`), não só confiar na saída do `flyctl deploy`

Isso vale mesmo sob pressão de "roda logo" / "mete marcha" do usuário — velocidade não substitui verificação, só evita perguntas desnecessárias no meio do caminho.

---

## Documentar lacunas em vez de escondê-las

Quando uma simplificação consciente é feita pra viabilizar um prazo (ex.: backend sem separação de ambiente homolog/produção, decisão registrada na issue #42), ela deve ser:

1. Documentada no lugar certo (`docs/deploy-plan.md` ou equivalente), não só mencionada de passagem na conversa
2. Registrada como issue de acompanhamento, se representar um risco antes de dados reais de usuário estarem envolvidos
3. Comunicada ao usuário no momento em que a decisão é tomada, não descoberta depois

Débito técnico invisível é pior que débito técnico registrado.

---

## Divergência entre plano e código

Quando um plano de arquitetura/deploy (seja escrito por outra sessão de IA ou por uma pessoa) diverge do que o código realmente faz, a IA não deve silenciosamente escolher um lado. Deve expor a divergência ao usuário e deixar a decisão explícita: seguir o código (mais simples, já testado) ou seguir o plano (mais fiel à intenção original, mais trabalho). Foi o que aconteceu no refactor pra 4 microservices da issue #35 — o plano previa 4 apps separados, o código era um monolito; a decisão de refatorar em vez de simplificar o plano foi do usuário.

---

## Referências

- `docs/workflow-passo-a-passo.md` — o "como fazer" na prática, checklist do ciclo completo
- `docs/guia-contribuicao.md` — gitflow e Conventional Commits
- `AGENT.md` — arquitetura e workflow de sprint
- `docs/relato-deploy-sprint0.md` — estudo de caso completo de onde essas regras vieram
- `docs/boas-praticas-opencode.md` — uso específico do OpenCode (plan/build mode, agentes, skills)
