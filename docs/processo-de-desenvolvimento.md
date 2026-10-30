# Processo de Desenvolvimento — Movecity

Como o Movecity foi construído: do item de backlog ao código em produção. Este capítulo reúne o que está nos guias do repositório (manual de sprint, workflow passo a passo, guia de contribuição, checklist de pré-commit e boas práticas de uso de IA) em um só texto.

## 1. Metodologia

O projeto combina duas abordagens, cada uma resolvendo um problema:

- **Lean Inception** (CAROLI, 2018), na fase de especificação, antes de qualquer código: personas, benchmarking e declaração de visão. Resolve o problema de construir a coisa certa.
- **Agentic Workflow**: o desenvolvimento é conduzido por agentes de IA (Claude Code e OpenCode) operando em nome de cada integrante, seguindo as regras do repositório. Resolve o problema de construir rápido sem perder rastreabilidade.

Todo o código foi gerado por agentes de IA, conduzidos pelos seis integrantes do grupo, que especificaram, revisaram e aprovaram. O que a IA escreve entra no repositório como trabalho de quem conduziu a sessão; commits, PRs e issues não levam assinatura de ferramenta.

## 2. Do backlog à issue

Toda User Story é formalizada como issue no GitHub, em três camadas separadas:

| Camada | O que contém | Onde fica |
|---|---|---|
| **User Story** | `Como / Quero / Para` e cenários BDD (`Dado / Quando / Então`): o valor para o usuário | Corpo da issue |
| **PRD** | Objetivos de negócio, mudanças de interface e regras de negócio | Comentário |
| **SPEC** | Arquitetura, modelo de dados, endpoints e requisitos de desempenho | Comentário |

A separação existe porque cada camada muda num ritmo: a US raramente muda, e a SPEC pode mudar várias vezes durante o desenvolvimento sem reescrever o valor de negócio.

**Definição de pronto para desenvolver (DoR).** Uma US só entra em desenvolvimento quando tem PRD e SPEC, critérios de aceite em BDD, estimativa de complexidade, dependências mapeadas e diagrama de sequência. O diagrama é a especificação técnica de execução: mostra, seta por seta, como Gateway, serviços e modelos interagem, e garante que duas pessoas implementando USs diferentes sigam o mesmo padrão (por exemplo, o JWT é validado sempre no Gateway, nunca duplicado no serviço de domínio).

## 3. Planejamento da sprint

- O time se reúne, revisa o backlog da sprint e cada integrante pega **uma US por sprint**. A regra evita que quem revisa vire gargalo e mantém o escopo dentro do prazo.
- Cada US vira um card no GitHub Projects, com checklist de desenvolvimento, revisão e deploy.
- A responsabilidade por épico é fixa (ver a distribuição de US no Documento de Requisitos), o que reduz troca de contexto.
- O trabalho foi organizado em cinco sprints; a última é a de fechamento e apresentação.

## 4. Ciclo de desenvolvimento com o agente

Para cada US, o agente segue esta ordem, e cada passo existe por um motivo:

1. **Ler a US e o diagrama antes de codar.** Sem isso, o código tende a divergir da arquitetura e a divergência só aparece na revisão, tarde demais.
2. **Criar a branch** a partir da base certa (ver o fluxo de branches abaixo).
3. **Implementar e testar localmente.** O CI roda os mesmos testes; falhar lá só gasta tempo.
4. **Antes do commit**, rodar o `scripts/verificar-deploy.sh`, que reproduz a verificação de contêiner do CI (cada serviço instala só o próprio `requirements.txt` e importa a aplicação) e confere o health check do Gateway, as rotas públicas e a rota protegida sem sessão. O motivo: uma dependência faltando no `requirements.txt` de um serviço passa no CI da raiz e derruba o contêiner no boot.
5. **Commit atômico, em Conventional Commits** (`feat`, `fix`, `docs`, `chore`, `test`...), o que deixa o histórico legível e permite reverter uma mudança específica. Mudanças em `docs/` e `src/` vão em commits separados.
6. **Abrir o PR** vinculado a uma issue (`Closes #N`), acompanhar o CI e aguardar a aprovação formal.
7. **Mergear, acompanhar o deploy e validar** o endpoint ou a tela real.

## 5. Fluxo de branches e revisão

```
feat/* e fix/*   →  homolog  →  main
docs/* e chore/* →  main (direto)
```

`feat` e `fix` mudam comportamento do sistema; por isso passam pela `homolog` antes de chegar à `main`. `docs` e `chore` não alteram o que roda em produção e vão direto para a `main`.

A `homolog` não é um ambiente isolado: o push nela já publica o frontend e o backend na produção pública, que compartilham os mesmos apps do Fly.io e o mesmo banco Neon. A decisão foi de custo, e o efeito prático é que **o merge em `homolog` equivale a publicar** e deve ser validado logo em seguida.

`main` e `homolog` são protegidas: exigem **uma aprovação formal** e CI verde. Só conta o botão **Approve** da aba "Files changed"; um comentário de texto não satisfaz a proteção. O autor do PR não pode aprovar o próprio, de modo que os PRs do orquestrador dependem de outro revisor ou de um bypass de administrador, que precisa ser decidido pelo orquestrador e registrado na issue relevante.

## 6. CI/CD

- **CI** (`ci.yml`): roda em todo PR para `homolog` ou `main`, com quatro verificações: lint de Conventional Commits (título do PR e commits), testes de backend (pytest, com migrations contra PostgreSQL), verificação do contêiner de cada serviço e testes de frontend (Jest). Ninguém mergeia com CI vermelho.
- **CD** (`deploy-fly.yml` e `deploy-vercel.yml`): o backend publica no push para `homolog` ou `main` que altere `src/backend/**`, rodando as migrations uma vez antes dos deploys e terminando com um teste de `GET /health` de cada serviço; o frontend publica só no push para `homolog`. Não há passo manual de deploy.
- **Ingestão da SEMOB** (`ingestao-semob.yml`): mensal, copia o catálogo de linhas e paradas para o banco.

Segredos e variáveis de cada plataforma, e a instalação local, estão nos guias `secrets-por-plataforma` e `setup-local` do repositório.

## 7. Definição de pronto (DoD), em dois níveis

A promoção para `main` costuma acontecer em lote, por isso uma US só fecha depois de dois níveis:

| Nível | Critérios |
|---|---|
| **DoD-Sprint** (feita na sprint) | PR mergeado em `homolog` com aprovação formal e CI verde; cenários BDD validados em `homolog`; comentário na issue com o resultado |
| **DoD-Release** (entregue de verdade) | PR `homolog` → `main` aprovado e mergeado; validado em produção (tela ou endpoint real, não suposição); issue fechada; documentação atualizada, se a US alterou algo documentado |

## 8. Regras para o uso de IA

- **O que o agente faz sem perguntar:** ler código, rodar testes locais, investigar bugs, criar e editar arquivos, criar branches, commitar e dar push em branches não protegidas, e consultar produção apenas para leitura (logs, variáveis, `curl`).
- **O que exige confirmação antes:** deletar recursos em produção, alterar produção (deploy manual, secrets, migrations contra o banco), mergear PR, bypass de proteção, editar issues de terceiros e qualquer ação fora do que foi pedido na conversa. Uma aprovação anterior não vale para uma ação nova.
- **Bypass de proteção** é decisão do usuário, nunca do agente, e todo bypass é registrado na issue (por quê, e que normalmente bloquearia o merge).
- **Verificar antes de declarar pronto:** ler a saída do comando, conferir o resultado real do CI (`gh pr checks`) e validar o endpoint depois do deploy. Quando o agente não pôde rodar algo, o relato diz isso ("testes escritos, não executados; validação pelo CI").
- **Divergência entre plano e código:** o agente expõe a divergência ao usuário e deixa a decisão explícita, em vez de escolher um lado em silêncio.

### O que o processo ensinou

- **Aprovação por comentário não é aprovação** (issue #35): um "revisado" na conversa do PR foi confundido com review formal, e dali veio a regra de só contar o botão Approve.
- **Plano que diverge do código** (issue #35): o plano previa quatro apps e o código era um monolito; a divergência foi exposta e decidida por uma pessoa.
- **Diagnóstico por leitura de código nem sempre bate com a produção** (#213): o erro 500 nas preferências de notificação foi atribuído a uma violação de chave estrangeira; os logs do Fly mostraram outra causa (o serviço de Colaboração não carrega o modelo `Usuario`). Os testes passavam porque carregam todos os modelos juntos.
- **A causa era configuração, não código** (#216): o embarque aceito de longe levou a uma correção de código, mas o valor de `RAIO_EMBARQUE_M` em produção estava em 100 km. Antes de mexer no código de um comportamento que depende de limite, ler o valor efetivo no ambiente. Quando a causa não está confirmada, o PR usa `Refs`, não `Closes`.

## 9. Registrar as lacunas

Quando uma simplificação é feita para caber no prazo (como a falta de homologação separada), ela é documentada no lugar certo, comunicada ao usuário no momento da decisão e, se for risco antes de dado real, vira issue de acompanhamento. Débito técnico invisível é pior que débito técnico registrado.
