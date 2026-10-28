# Relatório de Cobertura, Defeitos e Histórico de CI — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/relatorio-cobertura-e-defeitos.md>

Cobertura medida, defeitos encontrados e corrigidos nas Sprints 2 e 3 (e como cada um foi detectado), histórico do CI e dívida de testes. Medições em 16/10/2026, `homolog` @ `07c9edc`; defeitos 14 a 25 acrescentados em 27 e 28/10/2026 pela [execução dos casos](execucao-casos-p1.md). Contexto: [`README.md`](README.md).

## 1. Cobertura

### 1.1 Backend (`pytest --cov`)

Comando: `pytest -q --cov=auth --cov=colaboracao --cov=gateway --cov=mobilidade --cov=shared --cov-report=term` (Postgres 16, 671 testes).

| Serviço | Instruções do código de produção | Não cobertas | Cobertura |
|---|---|---|---|
| mobilidade | 2.700 | 146 | 94,6% |
| colaboracao | 535 | 35 | 93,5% |
| auth | 372 | 29 | 92,2% |
| gateway | 180 | 31 | 82,8% |
| shared | 41 | 0 | 100,0% |
| **Código de produção** | **3.828** | **241** | **93,7%** |

> O relatório do pytest mostra `TOTAL 9361 / 254 / 97%`. Esse total **inclui os próprios arquivos de teste** (que se cobrem a si mesmos) e por isso é mais alto. Os números acima separam o código de produção pelo caminho (`*/tests/*` e `test_*.py` ficam de fora).

Arquivos de produção com menos de 85% de cobertura (20 ou mais instruções):

| Arquivo | Cobertura | Não cobertas | Observação |
|---|---|---|---|
| `mobilidade/providers/linha_google_maps.py` | 30% | 32 de 46 | Provider real do Google (chamada externa) |
| `mobilidade/workers/monitoramento.py` | 62% | 15 de 39 | Worker de alertas |
| `mobilidade/main.py` | 73% | 11 de 41 | Montagem da aplicação e do worker |
| `gateway/routes.py` | 81% | 16 de 86 | Rotas de proxy |
| `gateway/proxy.py` | 83% | 4 de 23 | Proxy (testado com `httpx` mockado) |

### 1.2 Frontend (`jest --coverage`)

| Medida | Cobertura | Cobertas / total |
|---|---|---|
| Instruções | **89,07%** | 1.622 / 1.821 |
| Ramos | 84,65% | 855 / 1.010 |
| Funções | 86,09% | 353 / 410 |
| Linhas | 90,86% | 1.532 / 1.686 |

Menos cobertos (linhas): `app/ocorrencias/reportar/page.tsx` 73,8%, `app/tutorial/page.tsx` 81,1%, `app/AvisoEmBreve.tsx` 81,8%, `app/redefinir-senha/page.tsx` 82,6%, `lib/api.ts` 84,5%.

> **Limitação importante.** O Jest do projeto não define `collectCoverageFrom`, então só entram na conta os arquivos **importados por algum teste**. Dos 43 arquivos `.ts`/`.tsx` em `app/` e `lib/` (fora dos testes), 40 foram medidos. Os 3 que ficaram de fora são `app/layout.tsx`, `app/manifest.ts` e `app/RegistrarServiceWorker.tsx`. Os 89,07% são, portanto, um piso otimista; incluir esses arquivos (por exemplo, com `collectCoverageFrom`) derrubaria o número.

## 2. Defeitos encontrados e corrigidos

Selecionados nas issues e PRs das Sprints 1 a 3, com a forma de detecção **registrada na própria issue ou PR**. Quando o registro não diz como foi detectado, a tabela diz isso.

| # | Defeito | Issue / PR | Causa | Detectado por | Quando |
|---|---|---|---|---|---|
| 1 | Contêiner dos serviços morria no boot | PR #102; #127/#128; corrigido pelo CI da #145 e do PR #148 | `requirements.txt` do serviço sem pacote que o código importa; o CI instalava só o requirements combinado | **Produção** (queda) | Sprint 1 |
| 2 | Front chamava caminho que o Gateway não serve | PR #81 (citado na #151) | Sem teste de contrato front ↔ Gateway | **Produção**, segundo a #151 | Sprint 1 |
| 3 | Ordem do CORS quebrava toda rota protegida | PR #107 (citado na #151) | Ordem dos middlewares | **Produção**, segundo a #151 | Sprint 1 |
| 4 | `/docs` do Gateway respondia 401 | #149 → PR #150 | Entrada `"/doc"` (sem "s") em `ROTAS_PUBLICAS`; 6 das 18 entradas não correspondiam a rota alguma | **Produção**; depois **auditoria** da lista contra a aplicação rodando | 24/09 |
| 5 | CI vermelho: `No module named 'psycopg'` nas migrations e no boot dos serviços | Runs de 27 e 28/09; commit `cf3289d` ("travar sqlalchemy em 2.0.x pra nao puxar o driver psycopg v3"), mergeado pelo PR #154 | SQLAlchemy sem versão travada puxava outro driver | **CI** (antes do merge) | 27–28/09 |
| 6 | Tutorial voltava a aparecer sempre (`first_access` nunca persistia) | PR #165 (fechado), consolidado no #166 | Gateway não tinha proxy para `PUT /auth/me/first-access`; o 404 era engolido pelo `catch` do front | **Mapeamento de UI** da issue #143 (auditoria) | ~01/10 |
| 7 | Nenhuma linha circular mostrava ETA | PR #161 | O motor exigia `sentido: "CIRCULAR"` do veículo, que o feed real nunca reporta | **Validação manual** com o feed real do SEMOB | 30/09–01/10 |
| 8 | Achados de uso: botão de fechar do painel, legibilidade, direção do ônibus, atalho de reportar | PR #168 | Vários | **Teste manual contra dados reais** (descrito no PR) | 01/10 |
| 9 | ETA errado: sentido ambíguo e horários misturando dias | #173 → PRs #177 e #185 | 21,4% dos pares (parada, linha) casam IDA e VOLTA; 809 de 1.394 linha×sentido têm mais de um tipo de dia | **Medição** sobre o feed real do SEMOB (06/10), registrada na #173 | 06/10 |
| 10 | Número da linha com contraste 1,78:1; botão de favorito sem estilo; ETA medido até o GPS do usuário; saída do terminal apresentada como passagem | #179 → PRs #181 a #185 | Tokens de cor; CSS no escopo errado (`favoritos.css`); alvo do ETA | **Auditoria** do card, com contraste calculado e leitura do código | 14/10 |
| 11 | Gateway repassava o `X-User-Id` do cliente | #188 → PR #189 | Dois cabeçalhos `X-User-Id` chegavam ao serviço (o `dict` distingue maiúsculas) e o serviço lia o primeiro | **Não registrado** na issue | 14/10 |
| 12 | Import de ícone perdido num merge quebrava o chip de viagem | PR #187 (commit `a3d03e5`) | Merge sem conflito do Git removeu o import usado por outro PR | **CI** (Jest), antes de chegar ao usuário | 16/10 |
| 13 | Embarque recusado a mais de 100 m do ônibus | PR #191 (issue #190) | Raio fixo | **Teste real** da equipe (de longe do ônibus) | 16/10 |
| 14 | Cadastro aceita `termos_aceitos: false` e cria a conta | [execucao-casos-p1.md](execucao-casos-p1.md) (CT-AUT-01); issue #211 | Campo lido mas não validado no backend; a regra pode existir só na tela | **Execução de casos P1** (API, produção) | 27/10 |
| 15 | `/auth/refresh` responde 404: o Auth Service não tem a rota que o Gateway chama; a sessão expira em 1 h sem renovação | CT-AUT-03; issue #212 | Rota prevista (#31) e proxied no Gateway (`routes.py:142`), nunca implementada no serviço; testes do Gateway usam `httpx` mockado | **Execução de casos P1** (API, produção) | 27/10 |
| 16 | `GET /colaboracao/preferencias/{usuario_id}` com usuário inexistente responde 500 | observação do relatório de execução; issue #213 | Não investigada | **Execução de casos P1** (API, produção) | 27/10 |
| 17 | Painel da parada não mostra "Chegando nesta parada" quando não há chegadas | CT-PAR-01 e CT-PAR-04; issue #214 | **Comportamento da #179, não defeito de código**: a seção fica escondida durante uma viagem em andamento, quando a consulta falha ou dá 404 e quando a lista vem vazia. O caso CT-PAR-01 esperava a seção sempre; o texto do caso deve ser ajustado | **Execução de casos P1** (navegador, produção) | 27/10 |
| 18 | "Próximas saídas do terminal" lista horários já passados (06:00 às 07:58) | observação do relatório de execução; issue #215 | Não investigada | **Execução de casos P1** (navegador, produção) | 27/10 |
| 19 | Com a sessão expirada o app mostra "Nenhum ônibus em operação" e "Não foi possível carregar os detalhes da parada" em vez de pedir novo login | [execucao-casos-p1.md](execucao-casos-p1.md), seção "Sessão expirada na prática"; issue #221 | O frontend não trata 401 das chamadas de linhas/posições/paradas como sessão expirada; agrava o #212 (sem refresh, a sessão cai em 1 h) | **Execução de casos P1** (navegador, produção, rede da aba) | 27/10 |
| 20 | `GET /colaboracao/preferencias/{id}` responde 500 para qualquer usuário: `NoReferencedTableError` (FK `usuarios.id` sem o modelo `Usuario` carregado no processo da Colaboração) | #213; PR #224; [execucao-casos-p1.md](execucao-casos-p1.md), seção "Tela de Alertas" | O container da Colaboração carrega só `models`, `shared` e `colaboracao`; o `conftest` dos testes carrega todos os modelos, então o teste não reproduz. Corrige o diagnóstico anterior da #213 (violação de FK no commit) | **Uso real** (tela `/alertas` em produção) e **log do Fly.io** | 27/10 |
| 21 | Mensagens mandam verificar um e-mail que o sistema não envia ("Verifique seu e-mail para confirmar a conta", "receberá um link") | #230; CT-AUT-01 e CT-AUT-05 | Não há provedor de e-mail; o texto descreve um fluxo que não existe, e a conta de teste entrou sem confirmação | **Execução de casos** (navegador, produção, pelo usuário) | 27/10 |
| 22 | "Ir" no planejador coloca as coordenadas do usuário (`origem_lat`, `origem_lng`) na URL | #231 | A posição fica no histórico, em links copiados e em logs; contraria o RNF de LGPD e a RN-06 da viagem | **Execução de casos** (navegador, produção) | 27/10 |
| 23 | "Parada sem nome" no embarque e no desembarque dos cards de rota; o embarque não mostra o tempo em minutos, só o selo "ao vivo" | #232; CT-ROT-06 | Parada sem nome no dado de origem e o card não tem referência de reserva | **Execução de casos** (navegador, produção) | 27/10 e 28/10 |
| 24 | Mensagens de erro da redefinição de senha saem sem acentos ("Este link nao e mais valido ou expirou.") | #243; CT-AUT-05 | Textos do backend de autenticação escritos sem acento; cosmético | **Execução de casos** (navegador, produção) | 28/10 |
| 25 | A tela de reporte diz "mínimo 2 confirmações", mas o servidor exige 3 (`LIMITE_CONFIRMACOES = 3`) | #249; conferência do Documento de Visão com o código | Texto fixo na tela de reporte, sem ler a constante do servidor; o Documento de Visão e a issue #24 repetiam o 2 | **Documentação** (conferência de texto contra o código) | 28/10 |

> **Situação em 28/10:** o defeito 22 (#231) foi corrigido pelo PR #239 e o 23 (#232) pelo PR #240, ambos **validados em produção** ([execucao-casos-p1.md](execucao-casos-p1.md)). O defeito 21 (#230) teve o texto do cadastro trocado pelo PR #238; o e-mail de recuperação de senha por SMTP (#237) está no ar e aguarda a confirmação de entrega.

> **Observações sem contagem:** a #233 (a rota respondeu "Nenhuma linha liga esses dois pontos" uma vez para um par que depois deu 5 opções; não reproduzido, pode ser o defeito 19) e a #234 (o build do frontend depende do Google Fonts; falha transitória no deploy do PR #219) são riscos a investigar, não defeitos confirmados de código.

### Resumo da detecção (25 defeitos)

| Detectado por | Quantidade | Defeitos |
|---|---|---|
| Produção, antes do usuário final reportar | 4 | 1, 2, 3, 4 |
| CI, antes do merge | 2 | 5, 12 |
| Teste manual, execução de casos ou uso com dados reais | 14 | 7, 8, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24 |
| Auditoria, medição ou conferência de documento | 4 | 6, 9, 10, 25 |
| Não registrado | 1 | 11 |

> **Leitura.** Dos 25 defeitos, **10 são de conexão entre as peças** (1, 2, 3, 4, 5, 6, 11, 12, 15, 20: dependência faltando, contrato front ↔ Gateway, ordem de middleware, rotas públicas, cabeçalhos duplicados, import perdido num merge), e 15 são de regra, dado ou interface (7, 8, 9, 10, 13, 14, 16, 17, 18, 19, 21, 22, 23, 24, 25). Isso reforça a prioridade dos testes de integração do [relatório de integração](relatorio-testes-integracao.md). Os defeitos 1 a 4 foram relatados como ocorridos em produção. Os demais foram achados por outros meios, mas como `homolog` publica direto no ambiente visível (ver o [plano de testes](plano-de-testes.md)), os defeitos 6, 7, 10 e 11 também estiveram no código publicado até a correção; os registros consultados não dizem se algum usuário foi afetado.

## 3. Histórico do CI

Fonte: `gh run list --limit 1000 --json databaseId,workflowName,conclusion,createdAt,updatedAt,headBranch` (327 execuções, de 18/06 a 16/10/2026) e `gh run view` para o passo que falhou.

### 3.1 CI de PR ("CI — Testes no PR")

| Janela | Execuções concluídas | Verdes | Vermelhas | % verde | Duração mediana |
|---|---|---|---|---|---|
| Desde 18/06 (todas) | 199 | 148 | 51 | 74% | — |
| Desde 22/09 (Sprint 2 em diante) | 76 | 60 | 16 | 79% | 1,1 min |
| Desde 05/10 (Sprint 3) | 35 | 33 | 2 | 94% | 1,1 min |

(Há ainda 1 execução cancelada no total.) A duração máxima desde 22/09 aparece como 275,6 min; é um valor atípico (execução presa ou reexecutada) cuja causa **não foi investigada**. Desde 05/10, o máximo foi de 4,3 min.

### 3.2 As 16 execuções vermelhas desde 22/09

| Branch | Execuções | Passos que falharam |
|---|---|---|
| `feat/issue-27-alerta-atraso-linha` | 6 (26 e 28/09) | verificação de imports; migrations; testes |
| `feat/issue-30-tutorial-primeiro-acesso` | 6 (30/09) | migrations; importar a aplicação; Conventional Commits |
| `feat/issue-133-recuperacao-de-senha-no-aplicativo` | 1 (27/09) | migrations; importar a aplicação (3 serviços) |
| `feat/issue-19-eta-onibus` | 1 (28/09) | migrations; importar a aplicação (3 serviços) |
| `fix/issue-173-mapeamento-paradas` | 1 (08/10) | migrations |
| `feat/issue-171-pegar-onibus-frontend` | 1 (16/10) | Jest (`Bus is not defined`, ver defeito 12) |

Só duas causas estão confirmadas em log: `ModuleNotFoundError: No module named 'psycopg'` (27/09) e o import perdido de 16/10. A causa dos demais vermelhos em "Rodar migrations" não foi investigada.

### 3.3 Deploys

| Workflow | Sucesso | Falha | Cancelado | Desde 22/09 |
|---|---|---|---|---|
| Deploy Backend (Fly.io) | 62 | 6 | 3 | nenhuma falha |
| Deploy Frontend (Vercel) | 48 | 1 | 0 | nenhuma falha |
| Ingestão de linhas do SEMOB | 4 | 1 | 0 | — |
| Deploy Protótipo (GitHub Pages) | 1 | 1 | 0 | — |

Os deploys de `homolog` do commit `07c9edc` (backend e frontend) terminaram com sucesso.

## 4. Dívida de testes

| Área | O que falta | Evidência |
|---|---|---|
| Casos manuais | Os 49 casos de [`casos-de-teste.md`](casos-de-teste.md) ainda não foram executados | 0 execuções registradas |
| Contrato front ↔ Gateway | Nenhum teste compara `lib/api.ts` com o Gateway | `fetch` mockado em todo o frontend; defeitos 2 e 6 |
| Gateway ↔ serviços | Proxy testado com `httpx` mockado | `gateway/tests/test_proxy.py`; defeito 11 |
| Cobertura no CI | A cobertura não é medida nem exibida no PR | `ci.yml` roda `pytest -v` e `npm test` sem `--cov`/`--coverage` |
| Jest sem `collectCoverageFrom` | 3 arquivos fora da medição | seção 1.2 |
| Lint do frontend | `next lint` não está configurado | PR #187, "Notas e limites" |
| Postgres × SQLite | 2 arquivos de teste usam SQLite em memória; o PR #192 mediu o custo da consulta em SQLite | seção 2.2 do relatório de integração; PR #192 |
| Validação visual e no celular | O toque em "Cheguei", o estado de erro e a posição do botão no passo do card não foram conferidos no navegador | PR #187 e PR #193, "O que NÃO foi verificado" |
| ETA em campo | Tolerância proposta de 2 min para ETA até 10 min não foi medida; raio de 100 m e regra do embarque com o ônibus chegando (400 m, 2 min) também não | issue #173; PR #191 |
| Web Push / tela bloqueada | Não existe ainda; sem teste em dispositivo real nem no iOS | issue #195 |
| Avisos do pytest | 173 avisos não analisados | execução de 16/10 |
| APIs externas | SEMOB, OSRM, Nominatim e Google só em mocks | relatório de integração |
