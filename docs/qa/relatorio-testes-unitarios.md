# Relatório de Testes Unitários — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/relatorio-testes-unitarios.md>

Resultado real das suítes automatizadas (pytest e Jest) e o que cada PR mergeado desde o início da Sprint 2 (22/09/2026) acrescentou em teste. Contexto e plano: [`README.md`](README.md).

## 1. Execução de referência

| Item | Valor |
|---|---|
| Commit medido | `07c9edc` (`origin/homolog`, merge do PR #194) |
| Data | 16/10/2026 |
| Backend | Python 3.14.7, PostgreSQL 16.15 temporário (porta 55432), `alembic upgrade head` aplicado até a migration de `viagem`, depois pytest |
| Frontend | Node v24.19.0, `npm ci`, Jest 29 |

Comandos (a partir de `src/backend` e `src/frontend`):

```bash
alembic upgrade head
pytest -q --cov=auth --cov=colaboracao --cov=gateway --cov=mobilidade --cov=shared --cov-report=term
npx jest --coverage --silent          # e uma segunda passada com --json para a contagem por arquivo
```

### Resultado

| Suíte | Arquivos | Testes | Passando | Falhando | Tempo |
|---|---|---|---|---|---|
| Backend (pytest) | 56 | 671 | **671** | 0 | 65,2 s |
| Frontend (Jest) | 33 | 589 | **589** | 0 | 35,7 s |
| **Total** | **89** | **1.260** | **1.260** | **0** | |

Por serviço do backend (`pytest --collect-only`, que coincide com os 671 executados):

| Serviço | Arquivos de teste | Testes |
|---|---|---|
| mobilidade | 34 | 525 |
| colaboracao | 7 | 77 |
| auth | 7 | 37 |
| gateway | 7 | 29 |
| shared | 1 | 3 |

Evolução: o corpo original da #151 registrava **297 testes** (185 backend, 112 frontend). A medição de hoje, **1.260**, é 963 testes a mais.

### Atualização de 28/10/2026 (CI da `homolog`)

Os números acima são de 16/10 (`07c9edc`). Em 28/10 a contagem foi refeita **a partir do log do CI**, sem rodar nada localmente: execução [`40689632241`](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/actions/runs/40689632241) do workflow `ci.yml`, commit `48483be` (`homolog` com os PRs #238, #239 e #240), todos os jobs verdes.

| Suíte | Arquivos | Testes | Passando | Falhando | Tempo |
|---|---|---|---|---|---|
| Backend (pytest) | não recontado | 844 | **844** | 0 | 29,5 s |
| Frontend (Jest) | 43 suítes | 796 | **796** | 0 | n/d |
| **Total** | | **1.640** | **1.640** | **0** | |

São **380 testes a mais** que em 16/10 (173 no backend, 207 no frontend). A cobertura **não foi remedida**: o CI não a mede, então os 93,7% (backend) e 89,1% (frontend) continuam sendo os de 16/10. O número de arquivos de teste por serviço do backend também não foi recontado.

### Atualização de 31/10/2026 (`homolog` com o PR #265)

Com a entrada do alerta de cancelamento (#28), da posição colaborativa (#199) e do planejamento por horário (#115) na `homolog`, a contagem foi refeita **rodando as suítes completas** sobre `homolog` com o PR #265 (backend contra PostgreSQL 16 local; o CI do PR #265 também passou nos 7 checks).

| Suíte | Arquivos | Testes | Passando | Falhando |
|---|---|---|---|---|
| Backend (pytest) | não recontado | 952 | **952** | 0 |
| Frontend (Jest) | 45 suítes | 840 | **840** | 0 |
| **Total** | | **1.792** | **1.792** | **0** |

São 152 testes a mais que em 28/10 (108 no backend, 44 no frontend). A cobertura **não foi remedida**: continuam valendo os números de 16/10. Os casos manuais (CT-xxx) e a avaliação de Nielsen **não foram refeitos** para as três funcionalidades novas.

### Ressalvas sobre a execução

- **Ambiente diferente do CI.** O CI usa Python 3.12, Node 20 e a imagem `postgis/postgis:16-3.4`; a medição local usou Python 3.14.7, Node 24 e PostgreSQL 16.15 sem PostGIS. Os 7 checks do CI do PR #194 passaram (ver a tabela da seção 2); esta execução confirma o mesmo resultado fora do CI, e não o substitui.
- **173 avisos** (`warnings`) do pytest não foram analisados.
- O pytest rodou **uma vez**, com cobertura; a contagem por arquivo vem de `--collect-only`.
- Contagem de testes não mede qualidade. A cobertura está em [`relatorio-cobertura-e-defeitos.md`](relatorio-cobertura-e-defeitos.md).

## 2. Testes por PR (Sprint 2 em diante)

Fonte: `gh pr list --state merged --search "merged:>=2026-09-22"` e, para cada PR, `gh pr view --json files,statusCheckRollup,body`.
- **Arquivos de teste** = arquivos alterados em `*/tests/test_*.py` (py) e em `__tests__/` ou `*.test.ts(x)` (js).
- **Linhas de teste adicionadas** = soma das linhas adicionadas nesses arquivos.
- **CI no PR** = checks concluídos com sucesso sobre o total, no estado final do PR. O CI mudou ao longo do período: os PRs antigos têm 3 checks e, a partir do #148, 7 (o #181 tem 14 por ter rodado duas vezes).
- **Números "passed" citados** = números seguidos de "passed/passando/passaram" encontrados no corpo do PR, sem interpretação. Cada número descreve a branch no momento em que o autor escreveu; eles não se somam entre PRs.

| PR | Título | Autoria | Mesclado em | Base | Arquivos de teste (py/js) | Linhas de teste adicionadas | CI no PR | Números “passed” citados no corpo |
|---|---|---|---|---|---|---|---|---|
| #142 (promoção) | chore: promover homolog para producao — identidade v3, interface do... | @davieduardo001 | 2026-09-22 | main | 1/5 | +450 | 3/3 verdes | — |
| #147 | docs: registrar que a promocao para producao usa merge commit, nao ... | @davieduardo001 | 2026-09-22 | main | 0/0 | +0 | 3/3 verdes | — |
| #148 | ci: verificar o conteiner dos quatro servicos, nao so o gateway | @davieduardo001 | 2026-09-24 | homolog | 0/0 | +0 | 7/7 verdes | — |
| #150 | fix: swagger bloqueado por erro de digitacao na lista de rotas publ... | @davieduardo001 | 2026-09-24 | homolog | 1/0 | +61 | 7/7 verdes | — |
| #152 | feat(#27): implementar alerta de atraso na linha acompanhada | @ngualbertolopes | 2026-09-29 | homolog | 3/0 | +329 | 7/7 verdes | 24 |
| #153 | feat(auth): Recuperação de Senha no aplicativo — rota no Gateway e ... | @brenouchihar | 2026-09-29 | homolog | 0/4 | +389 | 7/7 verdes | — |
| #154 | feat(#19): ver tempo estimado de chegada do ônibus | @davieduardo001 | 2026-09-28 | homolog | 2/2 | +367 | 7/7 verdes | — |
| #158 | feat: tutorial no primeiro acesso (US #30) - reescrito | @Kelvin963 | 2026-09-30 | homolog | 1/0 | +157 | 7/7 verdes | — |
| #160 | feat: ETA real do ônibus e da rota planejada (#19, #159) | @Vitoria-Albuquerque | 2026-09-30 | homolog | 8/0 | +670 | 7/7 verdes | — |
| #161 | fix: não exigir sentido "CIRCULAR" do veículo em linha circular | @Vitoria-Albuquerque | 2026-10-01 | homolog | 1/0 | +32 | 7/7 verdes | — |
| #162 | feat: reportar ocorrencia em uma linha (US #23) | @Vitoria-Albuquerque | 2026-10-01 | homolog | 1/2 | +255 | 7/7 verdes | — |
| #163 (promoção) | chore: promover homolog para producao — ETA, alertas, recuperacao d... | @davieduardo001 | 2026-10-01 | main | 15/7 | +2260 | 7/7 verdes | — |
| #164 | chore: reconvergir homolog com main (PR #147 ficou so em main) | @Vitoria-Albuquerque | 2026-10-01 | homolog | 0/0 | +0 | 7/7 verdes | — |
| #166 | fix: consolidar correcoes de UI/UX (guia, v3, web, WCAG) | @Vitoria-Albuquerque | 2026-10-01 | homolog | 1/7 | +443 | 7/7 verdes | 68, 157 |
| #167 | docs: mapear adequacao de UI ao prototipo v3 (web, tablet, mobile) | @Vitoria-Albuquerque | 2026-10-01 | main | 0/0 | +0 | 7/7 verdes | — |
| #168 | fix: achados de teste real - painel de linha, legibilidade, direcao... | @Vitoria-Albuquerque | 2026-10-01 | homolog | 0/2 | +50 | 7/7 verdes | — |
| #169 | feat: ver detalhes de uma parada no mapa (US #18) | @louisassis | 2026-10-05 | homolog | 1/1 | +238 | 7/7 verdes | 168, 165 |
| #170 (promoção) | chore: promover homolog para producao — detalhes de parada (US #18)... | @davieduardo001 | 2026-10-05 | main | 2/9 | +731 | 7/7 verdes | — |
| #176 | feat: US #25 — Salvar e Visualizar Rota Favorita | @brenouchihar | 2026-10-06 | homolog | 1/5 | +1239 | 7/7 verdes | — |
| #177 | fix: identidade única de parada física (#173, parte 1 de 2) | @davieduardo001 | 2026-10-08 | homolog | 4/0 | +592 | 7/7 verdes | — |
| #178 | feat: alerta de proximidade da parada (#172, parte independente) | @ngualbertolopes | 2026-10-08 | homolog | 4/0 | +663 | 7/7 verdes | — |
| #180 | feat: visualizar ocorrencias reportadas por outros passageiros (US ... | @Vitoria-Albuquerque | 2026-10-15 | homolog | 1/3 | +465 | 7/7 verdes | 224 |
| #181 | fix: remover Linhas e Rotas do menu, que duplicavam busca e planeja... | @Vitoria-Albuquerque | 2026-10-15 | homolog | 0/2 | +36 | 14/14 verdes | 209 |
| #182 | fix: contraste AA, foco e favorito estilizado na tela de rotas (#17... | @Vitoria-Albuquerque | 2026-10-15 | homolog | 0/2 | +195 | 7/7 verdes | 227 |
| #183 | fix: redesenhar resultado de rota — hierarquia, linha do tempo e es... | @Vitoria-Albuquerque | 2026-10-15 | homolog | 0/4 | +595 | 7/7 verdes | 279 |
| #184 | fix: rotular a origem de cada tempo exibido (#179 — 4/5) | @Vitoria-Albuquerque | 2026-10-16 | homolog | 0/4 | +130 | 7/7 verdes | 294 |
| #185 | fix: ETA ate a parada fisica, com velocidade percorrida e fonte dec... | @Vitoria-Albuquerque | 2026-10-16 | homolog | 4/5 | +1531 | 7/7 verdes | 431, 330 |
| #186 | feat(mobilidade): pegar o onibus - embarcar, acompanhar e encerrar ... | @Vitoria-Albuquerque | 2026-10-16 | homolog | 1/0 | +946 | 7/7 verdes | 446 |
| #187 | feat(frontend): pegar o onibus - faixa de viagem, embarque pelo pop... | @Vitoria-Albuquerque | 2026-10-16 | homolog | 0/10 | +1668 | 7/7 verdes | 446 |
| #189 | fix(gateway): descartar o X-User-Id enviado pelo cliente (#188) | @Vitoria-Albuquerque | 2026-10-16 | homolog | 1/0 | +119 | 7/7 verdes | 368 |
| #191 | fix: raio de embarque configuravel e embarque com o onibus chegando... | @davieduardo001 | 2026-10-16 | homolog | 1/1 | +337 | 7/7 verdes | 566, 470 |
| #192 | fix: resposta atrasada, horarios por linha e custo da consulta no p... | @davieduardo001 | 2026-10-16 | homolog | 1/3 | +663 | 7/7 verdes | 401, 479 |
| #193 | feat: tempo do onibus nas paradas de subir e descer da rota e embar... | @davieduardo001 | 2026-10-16 | homolog | 1/7 | +1485 | 7/7 verdes | 567, 546 |
| #194 | feat: concluir o alerta de proximidade - onibus da viagem, ETA pelo... | @davieduardo001 | 2026-10-16 | homolog | 4/3 | +1180 | 7/7 verdes | 584, 489 |

### Leitura

| Medida | Valor | Como foi obtido |
|---|---|---|
| PRs mergeados no período | 34 (3 de promoção para `main`) | `gh pr list` |
| PRs `feat`/`fix` | 27 | prefixo do título |
| Desses, com ao menos um arquivo de teste | **27 de 27** | `gh pr view --json files` |
| PRs sem arquivo de teste | 4 (#147 docs, #148 CI, #164 chore, #167 docs) | idem |
| Linhas adicionadas em arquivos de teste | 14.835 nos 31 PRs que não são de promoção | soma de `additions` |
| PRs com os 7 checks verdes ao serem mergeados | todos os que têm 7 checks | `statusCheckRollup` |

> O #148 não tem arquivo de teste porque é o próprio passo de CI que verifica o contêiner dos quatro serviços. Os PRs de promoção repetem arquivos já contados nos PRs de origem e por isso ficam fora das somas.

## 3. Testes do backend, por arquivo

Fonte: `pytest --collect-only -q` em `07c9edc`.

| Serviço | Arquivo de teste | Testes |
|---|---|---|
| auth | `auth/tests/test_first_access.py` | 6 |
| auth | `auth/tests/test_google_auth.py` | 2 |
| auth | `auth/tests/test_google_login.py` | 8 |
| auth | `auth/tests/test_hello.py` | 2 |
| auth | `auth/tests/test_login.py` | 6 |
| auth | `auth/tests/test_me.py` | 3 |
| auth | `auth/tests/test_recuperacao_senha.py` | 10 |
| colaboracao | `colaboracao/tests/test_favoritos.py` | 22 |
| colaboracao | `colaboracao/tests/test_hello.py` | 1 |
| colaboracao | `colaboracao/tests/test_notificacoes.py` | 28 |
| colaboracao | `colaboracao/tests/test_ocorrencias.py` | 15 |
| colaboracao | `colaboracao/tests/test_preferencias_notificacao.py` | 9 |
| colaboracao | `colaboracao/tests/test_teste_gualberto.py` | 1 |
| colaboracao | `colaboracao/tests/test_teste_vitoria.py` | 1 |
| gateway | `gateway/tests/test_auth_proxy.py` | 5 |
| gateway | `gateway/tests/test_cors_ordem_middleware.py` | 2 |
| gateway | `gateway/tests/test_hello.py` | 1 |
| gateway | `gateway/tests/test_me_proxy.py` | 4 |
| gateway | `gateway/tests/test_proxy.py` | 10 |
| gateway | `gateway/tests/test_rotas_publicas.py` | 4 |
| gateway | `gateway/tests/test_status.py` | 3 |
| mobilidade | `mobilidade/tests/test_alerta_proximidade_entrega.py` | 19 |
| mobilidade | `mobilidade/tests/test_chegadas_da_rota.py` | 36 |
| mobilidade | `mobilidade/tests/test_chegadas_parada.py` | 38 |
| mobilidade | `mobilidade/tests/test_eta_destino_trajeto.py` | 25 |
| mobilidade | `mobilidade/tests/test_eta_service.py` | 7 |
| mobilidade | `mobilidade/tests/test_eta_trajeto.py` | 18 |
| mobilidade | `mobilidade/tests/test_eta_velocidade_efetiva.py` | 15 |
| mobilidade | `mobilidade/tests/test_fontes_proximidade.py` | 9 |
| mobilidade | `mobilidade/tests/test_geocode_service.py` | 7 |
| mobilidade | `mobilidade/tests/test_geometria.py` | 5 |
| mobilidade | `mobilidade/tests/test_hello.py` | 2 |
| mobilidade | `mobilidade/tests/test_horarios_por_dia.py` | 8 |
| mobilidade | `mobilidade/tests/test_ingestao_paradas.py` | 6 |
| mobilidade | `mobilidade/tests/test_ingestao_semob.py` | 4 |
| mobilidade | `mobilidade/tests/test_linha_mock_provider.py` | 4 |
| mobilidade | `mobilidade/tests/test_linha_service.py` | 12 |
| mobilidade | `mobilidade/tests/test_linhas_route.py` | 9 |
| mobilidade | `mobilidade/tests/test_osrm_router.py` | 4 |
| mobilidade | `mobilidade/tests/test_parada_horarios_por_linha.py` | 16 |
| mobilidade | `mobilidade/tests/test_paradas_fisicas.py` | 13 |
| mobilidade | `mobilidade/tests/test_paradas_route.py` | 10 |
| mobilidade | `mobilidade/tests/test_polyline_decoder.py` | 2 |
| mobilidade | `mobilidade/tests/test_posicao_service.py` | 18 |
| mobilidade | `mobilidade/tests/test_posicoes_route.py` | 8 |
| mobilidade | `mobilidade/tests/test_rota_service.py` | 16 |
| mobilidade | `mobilidade/tests/test_rotas_route.py` | 9 |
| mobilidade | `mobilidade/tests/test_routes.py` | 8 |
| mobilidade | `mobilidade/tests/test_semob_source.py` | 16 |
| mobilidade | `mobilidade/tests/test_servico_notificacoes.py` | 7 |
| mobilidade | `mobilidade/tests/test_servico_proximidade.py` | 25 |
| mobilidade | `mobilidade/tests/test_servico_rastreamento.py` | 9 |
| mobilidade | `mobilidade/tests/test_velocidade_media.py` | 16 |
| mobilidade | `mobilidade/tests/test_viagem.py` | 119 |
| mobilidade | `mobilidade/tests/test_worker_proximidade.py` | 5 |
| shared | `shared/tests/test_logs.py` | 3 |

## 4. Testes do frontend, por arquivo

Fonte: `jest --json` em `07c9edc`.

| Arquivo de teste | Testes |
|---|---|
| `app/__tests__/SplashScreen.test.tsx` | 3 |
| `app/__tests__/contraste.test.ts` | 30 |
| `app/__tests__/page.test.tsx` | 2 |
| `app/cadastro/__tests__/page.test.tsx` | 7 |
| `app/configuracoes/__tests__/page.test.tsx` | 6 |
| `app/favoritos/__tests__/page.test.tsx` | 11 |
| `app/login/__tests__/GoogleLoginButton.test.tsx` | 3 |
| `app/login/__tests__/page.test.tsx` | 12 |
| `app/mapa/__tests__/AppShell.aviso.test.tsx` | 5 |
| `app/mapa/__tests__/AppShell.test.tsx` | 31 |
| `app/mapa/__tests__/AvisoDeProximidade.test.tsx` | 11 |
| `app/mapa/__tests__/BotoesDaViagem.test.tsx` | 24 |
| `app/mapa/__tests__/FaixaDaViagem.test.tsx` | 16 |
| `app/mapa/__tests__/MapaInterativo.test.tsx` | 88 |
| `app/mapa/__tests__/PlanejadorViagem.test.tsx` | 67 |
| `app/mapa/__tests__/SaidasDoTerminal.test.tsx` | 5 |
| `app/mapa/__tests__/SeloFonte.test.tsx` | 8 |
| `app/mapa/__tests__/TempoNaParada.test.tsx` | 16 |
| `app/mapa/__tests__/ViagemContext.test.tsx` | 25 |
| `app/mapa/__tests__/page.test.tsx` | 18 |
| `app/mapa/__tests__/resumoViagem.test.ts` | 21 |
| `app/mapa/__tests__/tempo.test.ts` | 6 |
| `app/mapa/__tests__/textoDaViagem.test.ts` | 8 |
| `app/mapa/__tests__/useChegadasDaParada.test.tsx` | 9 |
| `app/mapa/__tests__/useChegadasDaRota.test.tsx` | 20 |
| `app/ocorrencias/__tests__/page.test.tsx` | 16 |
| `app/ocorrencias/reportar/__tests__/page.test.tsx` | 6 |
| `app/recuperar-senha/__tests__/page.test.tsx` | 5 |
| `app/redefinir-senha/__tests__/page.test.tsx` | 5 |
| `app/status/__tests__/page.test.tsx` | 2 |
| `app/tutorial/__tests__/page.test.tsx` | 5 |
| `lib/__tests__/api.aviso-proximidade.test.ts` | 8 |
| `lib/__tests__/api.test.ts` | 90 |
