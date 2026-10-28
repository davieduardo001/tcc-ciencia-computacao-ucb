# Guia da Apresentação Final — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/guia-apresentacao.md>

Guia de quem fala o quê na defesa de **13/11/2026**, com a tese central, os números que sustentam cada fala e as perguntas que a banca provavelmente fará. Desdobra o roteiro da issue [#205](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/205).

> **Tempo:** limite de **30 min no máximo**. O plano abaixo soma **23 min** de fala, deixando ~7 min de folga para troca de apresentador, imprevistos da demo e perguntas. Os números foram coletados em **27/10/2026** (`gh` + `git`) e os de qualidade em **16/10/2026** (`docs/qa/`). **Regerar tudo na véspera** (ver seção 6).

---

## 1. A tese

> **Todo o código do Movecity foi gerado por agentes de IA, conduzidos por seis estudantes que especificaram, revisaram e aprovaram. Dentro de um processo com travas (issue → BDD → PR → CI → review → homolog → main), isso entregou um produto funcional e testado em ~10 semanas. A IA escreveu; o processo e as pessoas garantiram a qualidade, e onde o processo falhou, os defeitos apareceram.**

Três ideias que toda fala deve reforçar:

1. **Velocidade com rastreabilidade:** tudo nasceu de uma issue, virou PR, passou por CI.
2. **A IA escreve, a pessoa decide:** merge, bypass e deploy em produção sempre passaram por uma pessoa (`docs/boas-praticas-ia.md`).
3. **Honestidade sobre os limites:** mostramos o que não foi validado (campo, casos manuais, ambiente de homologação). É isso que dá credibilidade à tese.

---

## 2. Quem fala o quê

Cada pessoa fala do que **entregou**, para saber responder às perguntas.

| # | Quem | Bloco | Tempo | Conteúdo | Material de apoio |
|---|---|---|---|---|---|
| 1 | **Nathália** (@gualbertonathalia) | **Problema e visão** | 2 min | Ônibus fantasma, insegurança nas paradas, assimetria de informação; Taguatinga/Ceilândia; 33,3% usam ônibus (IPEDF 2022); benchmarking (DF no Ponto, Moovit); termos de uso e LGPD (#32) | `docs/documento_visao.md` |
| 2 | **Davi** (@davieduardo001) | **Solução, arquitetura e stack** | 3 min | GPS oficial SEMOB + reporte colaborativo; Gateway único com JWT em cookie httpOnly, 3 serviços (auth, mobilidade, colaboração); Next.js + Leaflet, FastAPI no Fly.io, Neon, Vercel, GitHub Actions; decisões que **contrariaram** o plano inicial (sem PostGIS, ingestão em lote do SEMOB, 4 apps no Fly) | `docs/documento_arquitetura.md` §10 |
| 3 | **Kelvin** (@Kelvin963) | **Demo 1: mapa, ônibus e ETA** | 3 min | Localização (#14), busca de linha (#15), ônibus em tempo real (#16), ETA até a minha parada (#19); alerta de cancelamento / ônibus fantasma (#28, se entregue) | App ao vivo |
| 4 | **Luis** (@louisassis) | **Demo 2: parada, rota e viagem** | 3 min | Detalhes da parada (#18), rota com baldeação (#20), busca por endereço (#21), pegar o ônibus e alerta de proximidade (#171/#172), push (#207, se entregue) | App ao vivo |
| 5 | **Vitória** (@Vitoria-Albuquerque) | **Colaboração e experiência** | 2 min | Reportar e ver ocorrências (#23/#24), rota favorita (#25), tutorial (#30), protótipo de alta fidelidade (#33) e alinhamento de UX (#208). Coordena os slides (#205) | `prototipo-alta-fid/` |
| 6 | **Breno** (@brenouchihar) | **Segurança e qualidade** | 3 min | Login, cadastro, recuperação de senha (#10, #11, #13); sessão e Gateway; bug do `X-User-Id` (#188) como caso de segurança; 1.260 testes, cobertura, CI; os 23 defeitos e como foram achados | `docs/qa/` |
| 7 | **Davi** | **A tese: desenvolvimento com agentes de IA** | 5 min | Como trabalhamos (skills, comandos, regras), as travas, métricas de issues/PRs/bugs, o que a IA errou, lições | seção 3 deste guia |
| 8 | **Nathália** (fecha) | **Limites, trabalho futuro e conclusão** | 2 min | O que ficou fora (#115 motor GTFS/RAPTOR, #118 horários), validação em campo, ambiente de homologação separado; agradecimento | seção 5 |

> **Por que o Davi aparece duas vezes:** arquitetura e tese são os dois temas que mais exigem contexto. Se o tempo apertar na hora, **cortar o bloco 5 para 1 min e o bloco 8 para 1 min** antes de mexer nos blocos 2 e 7.
>
> **Perguntas:** qualquer um responde sobre a US que entregou (cenário 4 da #205). Quem não souber, passa para o responsável do bloco.

---

## 3. A tese em números (bloco 7 e apoio dos blocos 6 e 8)

Todos coletados de `gh issue/pr list` e `git log` em 27/10/2026, salvo indicação.

### 3.1 Volume

| Métrica | Valor | Observação |
|---|---|---|
| Issues criadas | **84** (71 fechadas, 13 abertas) | 7 com label `bug` |
| USs/épicos fechados | **31 de 38** | issues com label `Epico …` |
| Pull Requests | **126** (114 mergeados, 11 fechados sem merge, 1 aberto) | |
| PRs por destino | 102 → `homolog`, 21 → `main` | o resto são branches de feature empilhadas |
| PRs por tipo de branch | 61 `feat`, 37 `fix`, 9 `chore`, 9 `docs` | |
| Commits | **138** | `feat` 35, `fix` 28, `docs` 26, `chore` 24 (Conventional Commits) |
| Período | 15/08 a 27/10/2026 | ~10 semanas; pico de 20+ PRs/semana nas semanas 36–38 e 42 |
| Autores de PR | Davi 71, Vitória 29, Kelvin 11, Breno 7, Nathália 5, Luis 3 | **desigual**: dizer isso com naturalidade e explicar (Davi também orquestra, infra e correções) |

### 3.2 Revisão: aprovados e não aprovados

| Métrica | Valor | Como apresentar |
|---|---|---|
| PRs mergeados | 114 | |
| Com aprovação formal registrada | **50 de 114** | Os 64 restantes: **59 são PRs do próprio Davi**, que o GitHub não deixa aprovar (autor não aprova o próprio PR). Ver 3.4 |
| Aprovações (reviews `APPROVED`) | 53 (Davi 40, Vitória 13) | |
| Pedido de alterações | 1 (#176, rota favorita) | exemplo de review que **barrou** e voltou ajustado |
| Reviews dispensados e reaprovados | 3 (#183, #184, #185) | cadeia do card #179 |
| PRs fechados sem merge | **11** | 3 são testes deliberados de workflow (#67, #68, #71); 3 são tentativas de recuperação de senha (#73, #74, #86) refeitas no #87/#153; 3 do tutorial (#155–#157) consolidados no #158; #165 consolidado no #166; #88 sync cancelado. **Nenhum foi "rejeitado por qualidade"**: foram retrabalho e consolidação. |
| Tempo criação → merge | mediana **17 min**; média 6,3 h; 79 de 114 em menos de 1 h | mostra fluxo rápido; a banca vai perguntar se a revisão foi profunda |

### 3.3 Qualidade (de `docs/qa/`, 16/10/2026)

| Métrica | Valor |
|---|---|
| Testes automatizados | **1.260**, 0 falhas (671 backend com Postgres 16, 589 frontend); eram **297** no registro original da #151 |
| Cobertura | backend **93,7%**, frontend **89,1%** (piso otimista: 3 arquivos fora da medição) |
| PRs `feat`/`fix` com teste | **27 de 27** desde 22/09 |
| CI de PR verde | 74% no total → 79% (Sprint 2) → **94%** (Sprint 3) |
| Defeitos catalogados | **23** (13 até 16/10 + 10 achados em 27 e 28/10): 10 de conexão entre as peças e 13 de regra, dado ou interface. Fonte: `docs/qa/relatorio-cobertura-e-defeitos.md` |
| Onde foram detectados | produção 4 · CI 2 · teste manual, execução de casos ou uso real 13 · auditoria/medição 3 · não registrado 1 |
| Deploys | backend e frontend sem falha desde 22/09 |

**Frase-síntese do bloco 6:** *"os defeitos relevantes são de conexão, não de regra de negócio, e o CI pegou os que estavam ao seu alcance; os que escaparam só apareceram com dado real."*

### 3.4 O que a banca vai cobrar (e a resposta honesta)

| Pergunta provável | Resposta que temos | Pendência antes de 13/11 |
|---|---|---|
| "Quanto do código foi escrito pela IA?" | **Todo.** O código foi gerado por agentes de IA; as pessoas especificaram (issue, BDD, diagrama de sequência), revisaram e aprovaram. Por regra de autoria (`boas-praticas-ia.md`) os commits não levam assinatura de ferramenta, então o repositório não mostra isso; a declaração é do grupo. | Dizer explicitamente no slide e na fala. Não usar "% de código" (seria 100% e não mede esforço); falar do que a pessoa fez. |
| "Por que só 50 de 114 PRs têm aprovação formal?" | Dos 64 sem aprovação, **59 são PRs do Davi**, que é quem aprova os do grupo e não pode aprovar o próprio (regra do GitHub). Dos outros 5, 4 são do Breno/Nathália (#152, #153, #176, #209) e 1 da Vitória (#103, branch empilhada). | **Conferir os 5** (#103, #152, #153, #176, #209) e os 59 de Davi: como foram mergeados (bypass de admin?) e se estão registrados em comentário, conforme `boas-praticas-ia.md`. Ponto de atenção: PRs do Davi dependem de bypass ou de um segundo revisor. |
| "Mediana de 17 min até o merge não é revisão superficial?" | Por tipo: `feat` **25 min**, `fix` **8 min**, `docs` 14 min, `chore` 4 min. PRs pequenos e o CI cobre o mecânico, mas é um risco real: um único revisor. | Reconhecer o risco do revisor único como limite. |
| "Os casos de teste manuais foram executados?" | Em 27/10 executamos os 18 casos P1 (API e navegador, desktop e celular; `docs/qa/execucao-casos-p1.md`): **4 reprovados**, que viraram defeitos (cadastro sem aceite dos termos, `/auth/refresh` inexistente, seção "Chegando nesta parada" ausente). Os P2/P3 foram executados até 28/10 (32 aprovados, 11 em parte ou com ressalva, 1 reprovado por configuração); 3 não são verificáveis hoje (NOT-02, VIA-07, VIA-08) e 2 ficam para execução à mão (MAP-03, ETA-03). Quadro em `docs/qa/execucao-casos-p1.md`. | Fazer à mão MAP-03 e ETA-03 (DevTools Sensors); levar VIA-07 e VIA-08 para o ensaio. |
| "Existe ambiente de homologação?" | **Não separado, por decisão de custo**: `homolog` publica na produção da Vercel; backend e banco compartilham apps e Neon (free tier). Risco aceito e documentado. | Mostrar como trabalho futuro. |
| "O ETA está correto?" | Tolerância proposta (2 min até 10 min) **não foi medida em campo**. | Validar em campo se houver tempo, ou declarar como limite. |
| "A IA já errou?" | Sim, e está documentado: incidente da #35 (aprovação por comentário confundida com review formal), plano de 4 apps vs. código monolítico exposto em vez de escolhido em silêncio. | Escolher 2 exemplos (um de processo, um de código) para o slide. |

---

## 4. Como mostrar a tese (roteiro do bloco 7, 5 min)

1. **Como trabalhamos (1 min):** skills e comandos versionados (`.claude/commands`, `.opencode/skills`, `.gemini`: criar issue, gerenciar branches e commits, gerar diagrama de sequência, desenvolver US backend/frontend, review de PR). Manual do ciclo em `docs/manual-sprint.md`.
2. **As travas (1 min):** `main` e `homolog` protegidas, CI obrigatório, aprovação formal, DoD em dois níveis (sprint e release), "IA não faz merge nem bypass sem pedir". Fonte: `docs/boas-praticas-ia.md`.
3. **O que os números dizem (1 min):** 84 issues → 126 PRs → 1.260 testes; 27/27 PRs com teste; CI de 79% para 94% verde.
4. **Onde a IA/o processo falhou (1,5 min):** 23 defeitos, 4 em produção, 10 de conexão entre as peças; o `X-User-Id` (#188) como defeito de segurança; a lição de "verificar antes de declarar pronto".
5. **Conclusão (0,5 min):** a IA mudou **onde o esforço humano vai**: menos digitação, mais especificação (BDD, diagramas), revisão e verificação.

**Slide sugerido (um só, denso):** linha do tempo de 10 semanas com PRs por semana (barras), e ao lado os 4 números que importam: 1.260 testes · 93,7% / 89,1% · 23 defeitos (4 em produção) · 11 PRs fechados sem merge (retrabalho, não rejeição).

---

## 5. Demonstração ao vivo (blocos 3, 4 e 5)

Fluxo único e contínuo, passando o "bastão" entre os três:

1. **Kelvin:** abrir o app → mapa com minha localização → buscar linha `0.110` → ver ônibus se movendo → tocar no ônibus e ver o ETA com selo "ao vivo".
2. **Luis:** tocar numa parada → "Chegando nesta parada" → "Para onde você vai?" → rota → pegar o ônibus → alerta de proximidade.
3. **Vitória:** reportar ocorrência → ver a ocorrência → salvar rota favorita; mostrar o protótipo ao lado para a comparação.

**Plano B obrigatório (cenário 2 da #205):** gravar o mesmo fluxo em vídeo, com a localização simulada via DevTools → *Sensors*. A demo depende de rede, GPS e de um ônibus real em operação (madrugada = sem ônibus). Combinar a hora do ensaio de modo a conferir a linha usada.

---

## 6. Antes de 13/11

| Item | Quem | Observação |
|---|---|---|
| Conferir os PRs sem aprovação (3.4) e como foram mergeados | Davi | Sem isso, não colocar o 50/114 nos slides |
| Regerar os números de qualidade (`docs/qa/README.md`, "Como regerar") | Davi / Breno | Os de 16/10 são anteriores a vários PRs |
| Corrigir os defeitos abertos (#216, #230 a #233, e o risco #234) ou declará-los como limites | Davi + responsáveis | P1 e P2/P3 executados até 28/10 (quadro em `docs/qa/execucao-casos-p1.md`); #211 a #215 já corrigidos |
| Slides (#205), vídeo de plano B | Vitória + todos | |
| Ensaio completo cronometrado, 2 vezes | Todos | Meta: terminar com folga para perguntas |
| Promoção #203 (`homolog` → `main`) e validação em produção | Davi | A demo deve rodar no que está em produção |
| **Voltar `RAIO_EMBARQUE_M` a 100** (hoje 100000 = 100 km, de propósito, para testar de qualquer lugar) e retestar a recusa a mais de 100 m: `flyctl secrets set RAIO_EMBARQUE_M=100 -a movecity-mobilidade` | Davi | **Dizer na defesa que o embarque está em modo de teste**; reverter depois, se a regra for demonstrada |
| Decidir o que entra no "fora de escopo" (#26, #28, #115, #118, #199, #207) | Grupo | Só apresentar como entregue o que está mergeado |

**Regra de ouro (cenário 3 da #205):** todo número no slide tem fonte (comando, issue, PR ou relatório em `docs/qa/`); o que não foi medido não aparece como medido.

---

## 6.1 Limites conhecidos para declarar na defesa

- **O sistema não envia e-mails.** A confirmação de conta e a recuperação de senha por e-mail ficam como trabalho futuro (exigem provedor de e-mail). A tela ainda diz "Verifique seu e-mail", o que não corresponde ao comportamento.
- **Embarque com raio de 100 km** (`RAIO_EMBARQUE_M=100000`), de propósito, para demonstrar de qualquer lugar. A regra documentada é 100 m.
- **Alertas sem entrega:** a tela de preferências salva, mas não há push (#207) nem alerta de cancelamento (#28).
- **Sem ambiente de homologação separado** (decisão de custo).

## 7. Documentação final (próximo passo)

A defesa depende da documentação final (#204). Os modelos entregues pela disciplina são: **Documento de Arquitetura de Software v2**, **DRS** (requisitos) e **Documento de Visão** (`.dotx`). Estes templates ainda não foram abertos neste planejamento; o mapeamento de cada seção para o que já existe em `docs/` é o passo seguinte.
