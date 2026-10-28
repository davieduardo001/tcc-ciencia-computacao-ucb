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
- Instalar dependências, gerar secrets (tokens de escopo mínimo, nunca reaproveitar token pessoal de acesso total) e rodar `alembic upgrade` contra um banco **local**
- Consultar produção só para leitura (logs do Fly, `printenv` via `flyctl ssh console`, `curl` de endpoint), como foi feito nas issues #213 e #216

## O que precisa de confirmação explícita antes de agir

- **Deletar recursos em produção** (apps, bancos, branches protegidas) — mesmo que reversível via recriação, tem custo/risco real
- **Alterar produção**: `flyctl deploy` manual, `flyctl secrets set` (reinicia o serviço) ou migrations contra o Neon. Homologação e produção compartilham apps e banco, e o push em `homolog` já publica (ver `docs/deploy-plan.md`), então não existe "ambiente de teste" para essas ações. Exemplo: o valor de `RAIO_EMBARQUE_M` em produção (100 km) é decisão do grupo, registrada na issue #216, e não algo que a IA ajusta por conta própria
- **Merge de PR** — sempre perguntar antes, mesmo com CI verde
- **Bypass de branch protection** — ver seção dedicada abaixo
- **Editar issues/PRs de terceiros** ou mencionar pessoas do time
- Qualquer ação fora do que foi pedido na conversa atual (não generalizar uma aprovação anterior para uma ação nova)

---

## Bypass de branch protection: quando e como

`main` e `homolog` são protegidas por design — 1 aprovação obrigatória, CI obrigatório. Isso **não muda** por a IA estar conduzindo a sessão.

Só existe uma situação em que um merge sem aprovação é aceitável: quando o próprio objetivo do trabalho é testar o workflow/CI/CD em si (como foi o caso da issue #35). Mesmo aí:

1. O bypass é decisão do usuário, nunca da IA por conta própria. Tecnicamente ele é possível: o GitHub não aplica as regras de proteção a administradores (`enforce_admins` desligado em `main` e `homolog`), por isso a regra é de conduta, não só de ferramenta.
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

Quando a IA **não pôde** rodar nada (por exemplo, a sessão foi orientada a não executar suítes), o relato precisa dizer isso com todas as letras: "testes escritos, não executados; validação pelo CI". Foi o formato do PR #219. Afirmar "passa" nesse caso é afirmar sem fonte; o que vale é o resultado do CI lido com `gh pr checks`.

---

## Lições de diagnóstico (issues #213 e #216, outubro/2026)

Três casos recentes mostram como a verificação evita um diagnóstico errado ser dado como resolvido:

1. **Diagnóstico por leitura de código que não bateu com a produção (#213).** O PR #218 atribuiu o 500 nas preferências de notificação a uma violação de chave estrangeira no `commit` (usuário inexistente). Os logs do `movecity-colaboracao` no Fly mostraram outra causa: `NoReferencedTableError`, porque o serviço de Colaboração não carrega o modelo `Usuario` e a FK para `usuarios` não resolvia, **para qualquer usuário**. Os testes passavam porque o `conftest` importa todos os modelos juntos, enquanto em produção cada serviço sobe isolado. Regra: bug visto em produção se diagnostica com o **log de produção**, não só com o código; e um teste que carrega mais do que o serviço real carrega não prova que o serviço funciona (é por isso que existe o job `Contêiner do serviço` no CI).
2. **A causa era configuração, não código (#216).** O embarque aceito de longe levou a uma correção de código (PR #219) e a testes de regressão (PR #225), mas a causa real era a variável `RAIO_EMBARQUE_M` em produção valendo `100000` (100 km), lida com `flyctl ssh console -a movecity-mobilidade -C "printenv RAIO_EMBARQUE_M"`. Antes de mexer no código de um comportamento que depende de limite, ler o valor efetivo no ambiente. O grupo decidiu manter os 100 km até a defesa (só para demonstração) e a decisão ficou registrada na issue como limite conhecido.
3. **Hipótese declarada como hipótese.** O PR #219 marca a causa de #216 como "hipótese não confirmada" e usa `Refs #216` em vez de `Closes`. Quando a causa não foi confirmada, o PR não fecha a issue.

---

## Documentar lacunas em vez de escondê-las

Quando uma simplificação consciente é feita pra viabilizar um prazo (ex.: backend sem separação de ambiente homolog/produção, decisão registrada na issue #42, fechada em 14/10/2026 sem a separação ter sido implementada; o risco ficou aceito e documentado em `docs/deploy-plan.md`), ela deve ser:

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
- `docs/deploy-plan.md` e `docs/secrets-por-plataforma.md` — o que está em produção e onde cada segredo vive
- `docs/relato-deploy-sprint0.md` — estudo de caso completo de onde essas regras vieram
- `docs/boas-praticas-opencode.md` — uso específico do OpenCode (plan/build mode, agentes, skills)
