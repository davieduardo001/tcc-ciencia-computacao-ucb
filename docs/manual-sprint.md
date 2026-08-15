# Manual do Sprint Movecity — do Backlog ao Deploy

Manual de referência do ciclo completo de trabalho no Movecity: desde a ideia virar item de backlog (PRD/SPEC) até o código rodando em produção. É o documento pra entender **o porquê** de cada etapa, não só o comando a digitar — os comandos e prompts práticos ficam nos documentos específicos, linkados ao longo do texto.

**Para quem é:** qualquer pessoa do time (ou agente de IA operando em nome dela) que vá pegar uma User Story do zero.

---

## 1. Metodologia

O Movecity combina duas abordagens, cada uma resolvendo um problema diferente:

- **Lean Inception** (CAROLI, 2018) — usada na fase de especificação do produto, antes de qualquer código: alinhar personas, benchmarking (`docs/documento_visao.md`, seção 2.3) e a declaração de visão do produto (seção 3.2). Resolve o problema de "construir a coisa certa".
- **Agentic Workflow** — o desenvolvimento em si é conduzido por agentes de IA (Claude Code, OpenCode) operando em nome de cada dev, seguindo as regras deste repositório. Resolve o problema de "construir rápido sem perder rastreabilidade".

O restante deste manual detalha como as duas se encaixam no ciclo prático de uma sprint.

---

## 2. Arquitetura do sistema (resumo)

Documentação completa: `docs/documento_arquitetura.md` (modelo 4+1 de Kruchten, 1994). Resumo do que todo mundo precisa saber antes de tocar em código:

### 2.1 Estilo arquitetural

**Microserviços com API Gateway.** Não é escolha estética — está ligado a um requisito de qualidade específico (escalabilidade independente por serviço, isolamento de falha, evolução incremental sem redesenho total). Isso se reflete direto na estrutura de pastas do backend (`gateway/`, `auth/`, `mobilidade/`, `colaboracao/`, cada um deployável e escalável separadamente).

### 2.2 Camadas e o papel do Gateway

```
[Apresentação — Next.js]
        │
        ▼
[API Gateway]  ← ponto único de entrada, valida JWT localmente
        │
        ├──► [Serviço de Autenticação]
        ├──► [Serviço de Mobilidade]
        └──► [Serviço de Colaboração]
                    │
                    ▼
        [PostgreSQL + PostGIS / API SEMOB-GDF]
```

Regra que **nunca** pode ser ignorada em nenhum diagrama de sequência ou implementação: o Gateway valida o token JWT **localmente**, sem round-trip ao serviço de autenticação a cada requisição. Os serviços de domínio não conhecem sessão — recebem `identidadeUsuario` já validado pelo Gateway. Essa decisão existe pra não transformar o serviço de autenticação num gargalo de toda requisição do sistema.

### 2.3 Decisões de stack e o porquê

| Camada | Escolha | Por quê (resumo) |
|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript | SSR/SSG reduz tempo de carregamento (requisito: ≤3s em 4G); tipagem estática reduz bugs |
| Mapa | Leaflet JS + OpenStreetMap | Gratuito, sem risco de custo de API de mapa em produção |
| Backend | FastAPI (Python 3.12) | Assíncrono, alta performance, OpenAPI automático, ecossistema geoespacial maduro (PostGIS) |
| Banco | PostgreSQL + PostGIS (Neon serverless) | Free tier viável pro TCC, escala sozinho, suporta dado geoespacial nativamente |
| Deploy backend | Fly.io (Docker) | Deploy simples, múltiplas regiões, sem lock-in de nuvem proprietária |
| Deploy frontend | Vercel | Integração nativa com Next.js, preview automático por branch |
| CI/CD | GitHub Actions | Nativo do repositório, sem custo adicional |
| Autenticação | JWT stateless | Elimina estado de sessão no servidor; Gateway valida sem round-trip |

Tabela completa com justificativas: `docs/documento_arquitetura.md`, seção 4.2.

### 2.4 Requisitos não-funcionais que toda US precisa respeitar

- Carregamento inicial ≤ 3s em 4G
- Disponibilidade ≥ 99% nos horários de pico (5h–9h, 17h–20h)
- Reporte colaborativo só confirma com ≥ 2 confirmações independentes (anti-spam/anti-fraude)
- Dado de geolocalização tratado conforme LGPD

---

## 3. Do backlog à issue: PRD, SPEC e User Story

Antes de qualquer linha de código, toda US precisa estar **formalizada como issue no GitHub**, com três camadas de informação separadas (não misturadas no mesmo texto):

| Camada | O que contém | Onde fica |
|---|---|---|
| **User Story** | Formato `Como / Quero / Para` + cenários BDD (`Dado/Quando/Então`) — o valor pro usuário | Corpo principal da issue |
| **PRD** | Objetivos de negócio, mudanças de UI, regras de negócio | Comentário separado na issue |
| **SPEC** | Arquitetura, modelos de dados, endpoints, requisitos de performance | Comentário separado na issue |

Por que separado e não tudo num texto só: cada camada tem um público e um ritmo de mudança diferente. A US raramente muda depois de escrita; a SPEC pode mudar várias vezes durante o desenvolvimento sem precisar reescrever o valor de negócio.

**Como formalizar:** skill `gh-create-issue` (`.claude/commands/gh-create-issue.md`) — peça pro agente:

> "Formaliza a US de [descrição] como issue, seguindo o template."

Templates de referência: `docs/templates/Template_User_Stories.md` (US) e `docs/templates/template-card-sprint.md` (card de sprint).

### Critérios DOR (Definitivamente Pronto pra Desenvolvimento)

Uma US só entra em desenvolvimento quando:

- [ ] PRD e SPEC documentados (comentários na issue)
- [ ] Critérios de aceite definidos (BDD)
- [ ] Estimativa de complexidade
- [ ] Dependências mapeadas (outra US precisa terminar antes?)
- [ ] Diagrama de sequência disponível

O diagrama de sequência é a **spec técnica de execução** — descreve, seta por seta, como Gateway/Serviços/Modelos interagem pra aquele caso de uso. É o que garante que duas pessoas implementando USs diferentes sigam o mesmo padrão arquitetural (ex.: validação de JWT sempre no Gateway, nunca duplicada no serviço de domínio).

---

## 4. Sprint Planning

1. Time se reúne (cerimônia), sprint backlog é revisado.
2. Cada membro pega **1 US por sprint** — regra deliberada pra evitar gargalo de review (se todo mundo pegar 3 USs, o reviewer vira o gargalo do time inteiro) e manter escopo gerenciável dentro do prazo.
3. Card de sprint criado no GitHub Projects a partir de `docs/templates/template-card-sprint.md` — tem checklist de desenvolvimento, review e deploy embutido, então serve de guia durante toda a US.
4. Responsabilidade por épico já é fixa (ver `docs/distribuicao_us.md`) — reduz troca de contexto, cada pessoa aprofunda no domínio que já é dela.

---

## 5. Desenvolvimento (ciclo agêntico)

Esse é o miolo prático — **não duplicado aqui**, está em `docs/workflow-passo-a-passo.md`: clonar o repo, abrir o agente, o que falar pra ele em cada etapa (ler a US, criar branch, implementar, testar, commitar, abrir PR, acompanhar CI, confirmar review formal, mergear, validar em produção).

O que vale destacar aqui é a lógica por trás da ordem das etapas — por que não dá pra pular nenhuma:

1. **Ler a US + diagrama antes de codar** — é "spec programming": sem isso, o código tende a divergir da arquitetura pretendida e só se descobre isso no review, tarde demais.
2. **Testar local antes de commitar** — o CI vai rodar os mesmos testes; falhar lá é só perda de tempo (rodada de CI demora, feedback local é instantâneo).
3. **Commit atômico, Conventional Commits** — histórico legível permite automação futura (changelog, versionamento semântico) e facilita reverter uma mudança específica sem arrastar outras.

---

## 6. Gitflow: a lógica dos 3 níveis

```
feat/* e fix/*   →  homolog  →  main
docs/* e chore/* →  main (direto)
```

Por quê **3 níveis** e não 2 (branch → main direto)? Porque `feat/` e `fix/` alteram **comportamento funcional** — código que roda, que pode quebrar algo em produção. `homolog` existe como um ambiente real de staging onde essa mudança roda antes de qualquer usuário real (ou avaliador do TCC) ver — é a rede de segurança entre "compilou" e "está em produção".

Por quê `docs/` e `chore/` **pulam** esse ambiente e vão direto pra `main`? Porque não alteram comportamento do sistema em produção — não tem risco funcional que uma homologação capturaria. Forçar essas mudanças a passar por `homolog` só adicionaria fricção sem benefício.

Detalhes completos e comandos: `docs/guia-contribuicao.md`.

### Por que 1 aprovação obrigatória, sempre

Porque código sem segundo par de olhos é a fonte mais comum de bug que "parecia óbvio" pra quem escreveu. A regra não tem exceção — nem para IA, nem para urgência (ver `docs/boas-praticas-ia.md`, seção de bypass). E aprovação só conta se for formal (botão **Approve**, aba "Files changed") — um comentário de texto não satisfaz a branch protection do GitHub, por mais que pareça uma aprovação na conversa.

---

## 7. Uso de IA no processo

Regras completas: `docs/boas-praticas-ia.md`. Os pontos que mais importam pra quem tá começando:

- A IA nunca é citada como autora — commits, PRs e comentários de issue são só do desenvolvedor.
- A IA pode implementar, testar, commitar e abrir PR sozinha; **merge sempre passa por confirmação sua**, mesmo com CI verde e aprovação.
- Bypass de branch protection só é aceitável quando o próprio objetivo do trabalho é testar o pipeline — e precisa ficar registrado explicitamente na issue, nunca silencioso.
- Se um plano de arquitetura divergir do código real, a IA expõe a divergência pra você decidir, não escolhe um lado sozinha.

---

## 8. CI/CD e Deploy

- **CI** (`ci.yml`): dispara em todo PR pra `homolog`/`main` — lint de Conventional Commits, pytest, Jest. Ninguém mergeia com CI vermelho.
- **CD** (`deploy-fly.yml` + Vercel): dispara automaticamente no push pra `homolog` ou `main` — não é passo manual, é consequência do merge.
- **Homolog e produção usam o mesmo pipeline**, só muda a branch de destino — isso é bom (consistência) e tem uma lacuna conhecida (backend não tem apps/banco separados por ambiente ainda — ver issue [#42](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/42) e `docs/deploy-plan.md`).

Passo a passo prático de deploy: `docs/workflow-passo-a-passo.md`, seções 6–11.

---

## 9. Fechando o ciclo

- Issue comentada com o resultado (PR mergeado, rodando em produção).
- Se algo saiu diferente do planejado (débito técnico consciente, divergência de plano), isso é **documentado**, não escondido — vira uma issue de acompanhamento se representar risco antes de dado real de usuário (exemplo real: issue #42).
- Card de sprint atualizado (checklist de `docs/templates/template-card-sprint.md`).
- Próxima sprint: repete o ciclo a partir da seção 3.

---

## Mapa de documentos

| Pergunta | Documento |
|---|---|
| Por que a arquitetura é assim? | `docs/documento_arquitetura.md` |
| Qual o produto e pra quem? | `docs/documento_visao.md` |
| Quem é responsável por qual US? | `docs/distribuicao_us.md` |
| Como formalizar uma US? | `.claude/commands/gh-create-issue.md`, `docs/templates/` |
| Como executar o ciclo com o agente, na prática? | `docs/workflow-passo-a-passo.md` |
| Quais as regras de branch/commit e por quê? | `docs/guia-contribuicao.md` |
| O que a IA pode/não pode fazer sozinha? | `docs/boas-praticas-ia.md` |
| Como foi o deploy real da issue #35 (estudo de caso)? | `docs/relato-deploy-sprint0.md` |
| Como rodar o projeto localmente? | `docs/setup-local.md` |
