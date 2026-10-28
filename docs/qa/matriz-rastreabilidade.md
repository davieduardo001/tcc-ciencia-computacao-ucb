# Matriz de Rastreabilidade — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/matriz-rastreabilidade.md>

Liga cada User Story (ou card) entregue aos seus cenários BDD, aos [casos de teste manuais](casos-de-teste.md), aos PRs que a entregaram e aos arquivos de teste automatizados que a cobrem.

**Como foi montada** (28/10/2026, `homolog` @ `b46b7a6`):
- **PRs:** PRs mergeados cujo título cita a US ou cujo corpo tem `Closes`/`Refs` para ela (`gh pr list --state merged --json number,title,body`). Os arquivos de teste de cada PR vêm de `gh pr view --json files`.
- **Estado:** estado da issue no GitHub em 28/10/2026. "Entregue" quer dizer mergeado. Issue fechada indica promoção para `main` (a promoção mais recente foi o PR #203, de 22/10); "aberta · Homolog" indica PR mergeado em `homolog` que espera a promoção para `main`. Como o deploy publica `homolog` na produção, o código mergeado em `homolog` já está no ar (ver o [plano de testes](plano-de-testes.md), seção 3).
- **Casos manuais:** com o resultado final da execução de 27 e 28/10/2026 (ver o [quadro geral](execucao-casos-p1.md#quadro-geral-dos-49-casos-atualizado-em-2810)). Siglas: **A** aprovado, **A\*** aprovado em parte ou com ressalva, **R** reprovado por configuração, **NV** não verificável hoje, **NE** não executado.
- **Arquivos de teste:** os principais, por nome; a lista completa com contagens está no [relatório unitário](relatorio-testes-unitarios.md). Caminhos relativos a `src/backend/` (arquivos `test_*.py`) e `src/frontend/` (arquivos `*.test.ts(x)`).

## 1. Matriz

| US / card | Título | Estado | Cenários na issue | Casos manuais (resultado) | PRs | Testes automatizados principais |
|---|---|---|---|---|---|---|
| #10 | Login com e-mail e senha | fechada · Done | 3 | CT-AUT-02 (A), CT-AUT-03 (A\*) | #75 | `auth/tests/test_login.py`, `app/login/__tests__/page.test.tsx` |
| #11 | Criar nova conta | fechada · Done | 5 | CT-AUT-01 (A\*) | #52; #218 (termos no cadastro, #211) | `auth/tests/test_registro.py`, `test_registrar_termos.py`, `app/cadastro/__tests__/page.test.tsx` |
| #12 | Login via Google | fechada · Done | 1 | CT-AUT-04 (A) | #91 | `auth/tests/test_google_auth.py`, `test_google_login.py`, `app/login/__tests__/GoogleLoginButton.test.tsx` |
| #13 / #133 / #237 | Recuperação de senha (backend / telas / e-mail por SMTP) | #13 e #133 fechadas · Done; #237 aberta · Homolog | 3 / 7 / sem BDD na issue | CT-AUT-05 (A\*) | #87 / #153 / #238 (cita também a #230) | `auth/tests/test_recuperacao_senha.py`, `test_email_service.py`, `app/recuperar-senha`, `app/redefinir-senha`, `app/cadastro/__tests__/page.test.tsx` |
| #31 (+ #212, #221) | Ciclo de vida da sessão (inclui `/auth/refresh` e renovação no 401) | #31 fechada · Done; #212 e #221 abertas · Homolog | 4 | CT-AUT-03 (A\*), CT-AUT-06 (A), CT-AUT-07 (A) | #56, #66 (citam a US); #218 (`/auth/refresh`, #212); #222 (renovação, #221) | `gateway/tests/test_auth_proxy.py`, `test_me_proxy.py`, `test_rotas_publicas.py`, `auth/tests/test_refresh.py`, `lib/__tests__/api.sessao.test.ts` |
| #14 | Mapa com localização atual | fechada · Done | 3 | CT-MAP-01 (A), CT-MAP-02 (A), CT-MAP-03 (NE) | #85 | `app/mapa/__tests__/MapaInterativo.test.tsx` |
| #15 | Buscar linha por número | fechada · Done | 3 | CT-MAP-04 (A), CT-MAP-05 (A) | #99 | `mobilidade/tests/test_linha_service.py`, `test_linhas_route.py`, `test_linha_mock_provider.py` |
| #16 | Rastrear ônibus em tempo real | fechada · Done | 3 | CT-MAP-07 (A), CT-MAP-08 (A) | #120, #124 | `mobilidade/tests/test_posicao_service.py`, `test_posicoes_route.py` |
| #17 | Trajeto e paradas da linha | fechada · Done | 3 | CT-MAP-04 (A), CT-MAP-06 (A) | #105, #108, #109, #110, #111, #114 | `mobilidade/tests/test_linhas_route.py`, `test_osrm_router.py`, `test_polyline_decoder.py`, `test_semob_source.py` |
| #18 | Detalhes de uma parada | fechada · Done | 3 | CT-PAR-01 (A, revalidado), CT-PAR-02 (A), CT-PAR-03 (A\*) | #169; correções #219 (#215) e #220 (folha única, #217) | `mobilidade/tests/test_paradas_route.py`, `MapaInterativo.test.tsx`, `FolhaInferior.test.tsx` |
| #19 | ETA do ônibus até a minha parada | fechada · Done | 5 | CT-ETA-01 (A), CT-ETA-02 (A), CT-ETA-03 (NE) | #154, #160 | `mobilidade/tests/test_eta_service.py`, `test_eta_trajeto.py`, `test_posicoes_route.py` |
| #20 | Calcular rota por ônibus | fechada · Done | 5 | CT-ROT-01 (A), CT-ROT-02 (A), CT-ROT-03 (A), CT-ROT-04 (A) | #116, #119 | `mobilidade/tests/test_rota_service.py`, `test_rotas_route.py`, `test_geocode_service.py`, `app/mapa/__tests__/PlanejadorViagem.test.tsx` |
| #159 | ETA real da rota planejada | fechada · Done | 3 | CT-ROT-02 (A) | #160 | `mobilidade/tests/test_eta_trajeto.py`, `test_rota_service.py` |
| #21 | Buscar parada por nome ou endereço | fechada · Done | ver a issue | sem caso dedicado (ver nota 3) | #197 | `mobilidade/tests/test_busca_parada_route.py`, `app/mapa/__tests__/BuscaParada.test.tsx`, `lib/__tests__/buscarParadas.test.ts` |
| #22 | Notificações de rotas preferidas | fechada · Done | 3 | sem caso dedicado (ver nota 1) | #94 | `colaboracao/tests/test_notificacoes.py` |
| #23 | Reportar ocorrência | fechada · Done | 3 | CT-COL-01 (A), CT-COL-02 (A), CT-COL-03 (A) | #162 | `colaboracao/tests/test_ocorrencias.py`, `app/ocorrencias/reportar/__tests__/page.test.tsx` |
| #24 | Ver ocorrências de outros passageiros | fechada · Done | 3 | CT-COL-04 (A\*), CT-COL-05 (A) | #180 | `colaboracao/tests/test_ocorrencias.py`, `app/ocorrencias/__tests__/page.test.tsx` |
| #25 | Rota favorita | fechada · Done | 3 | CT-ROT-05 (A) | #176; correção #239 (coordenadas na URL, #231) | `colaboracao/tests/test_favoritos.py`, `app/favoritos/__tests__/page.test.tsx`, `app/mapa/__tests__/page.test.tsx` |
| #26 | Confirmar ocorrência de outro passageiro | **aberta** · Homolog | ver a issue | sem caso dedicado (ver nota 3) | #209 | `colaboracao/tests/test_confirmar_ocorrencia.py`, `app/ocorrencias/__tests__/page.test.tsx` |
| #27 | Alerta de atraso | fechada · Done | 3 | CT-NOT-02 (NV) | #152 | `mobilidade/tests/test_servico_rastreamento.py`, `test_servico_notificacoes.py`, `test_routes.py` |
| #29 | Preferências de notificação | **aberta** (reaberta em 27/10) · Homolog | 3 | CT-NOT-01 (A, depois da correção) | #127 (backend); #223 (tela `/alertas`); #218 e #224 (500 com usuário inexistente e FK, #213) | `colaboracao/tests/test_preferencias_notificacao.py`, `test_preferencia_isolamento.py`, `app/alertas/__tests__/page.test.tsx`, `lib/__tests__/api.preferencias.test.ts` |
| #30 | Tutorial no primeiro acesso | fechada · Done | 3 | CT-MAP-09 (A) | #158 | `auth/tests/test_first_access.py`, `app/tutorial/__tests__/page.test.tsx` |
| #171 | Pegar o ônibus | fechada · Done | 4 | CT-VIA-01 (R), CT-VIA-02 (A\*), CT-VIA-03 (A), CT-VIA-04 (A), CT-VIA-05 (A), CT-VIA-07 (NV), CT-SEG-03 (A) | #186, #187, #191; correções #219 e #225 (embarque pelo popup, #216) | `mobilidade/tests/test_viagem.py`, `ViagemContext.test.tsx`, `FaixaDaViagem.test.tsx`, `BotoesDaViagem.test.tsx` |
| #172 | Alerta de proximidade | fechada · Done | 4 | CT-VIA-08 (NV) | #178, #186, #194 | `mobilidade/tests/test_servico_proximidade.py`, `test_worker_proximidade.py`, `test_eta_destino_trajeto.py`, `test_alerta_proximidade_entrega.py`, `AvisoDeProximidade.test.tsx` |
| #195 / #200 | Alerta de proximidade com a tela bloqueada (Web Push) / chaves VAPID no CI | #195 fechada · Done; #200 **aberta** · Homolog | ver a issue | sem caso dedicado (ver nota 4) | #196 / #210 | `mobilidade/tests/test_web_push.py`, `app/__tests__/service-worker-push.test.ts`, `app/configuracoes/__tests__/avisos-push.test.tsx`, `lib/__tests__/push.test.ts` |
| #173 | ETA: mapeamento entre paradas | fechada · Done | 4 | CT-PAR-04 (A, revalidado), CT-ETA-01 (A) | #177, #185 | `mobilidade/tests/test_paradas_fisicas.py`, `test_ingestao_paradas.py`, `test_horarios_por_dia.py`, `test_chegadas_parada.py` |
| #174 | Follow-up da US #18 | fechada · Done | sem BDD na issue (ver nota 2) | CT-PAR-01 (A, revalidado), CT-PAR-03 (A\*) | #192; correção #219 | `mobilidade/tests/test_parada_horarios_por_linha.py`, `SaidasDoTerminal.test.tsx` |
| #179 | Navegação, rotas e ETA (card) | fechada · Done | regras RN-01 a RN-15 | CT-ETA-04 (A\*), CT-ROT-07 (A\*), CT-PAR-04 (A, revalidado) | #181 a #185; #228 (botão de perfil sem ação, #227) | `AppShell.test.tsx`, `contraste.test.ts`, `PlanejadorViagem.test.tsx`, `resumoViagem.test.ts`, `SeloFonte.test.tsx` |
| #188 | Bug: `X-User-Id` do cliente | fechada · Done | 4 | CT-SEG-01 (A\*) | #189 | `gateway/tests/test_proxy.py` |
| #190 | Paradas de subir e descer na rota | fechada · Done | 11 | CT-ROT-06 (A\*), CT-VIA-06 (A) | #191, #193; correção #240 (parada sem nome, #232) | `mobilidade/tests/test_chegadas_da_rota.py`, `TempoNaParada.test.tsx`, `useChegadasDaRota.test.tsx`, `BotoesDaViagem.test.tsx`, `PlanejadorViagem.test.tsx` |
| #149 | Bug: Swagger 401 em produção (rotas públicas) | fechada · Done | ver a issue | CT-SEG-02 (A) | #150 | `gateway/tests/test_rotas_publicas.py` |
| #217 | Folha única com 3 alturas (celular) | **aberta** · Homolog | ver a issue | sem caso; conferir em celular real (pendente) | #220 | `app/mapa/__tests__/FolhaInferior.test.tsx`, `PlanejadorViagem.test.tsx`, `MapaInterativo.test.tsx` |

## 2. Notas

1. **#22** são notificações geradas no servidor. O notificador usado pelos serviços de alerta é o `NotificadorNulo`, que não entrega nada ao usuário; sem canal de entrega não há comportamento observável na tela para um caso manual, e a US fica coberta só por teste automatizado. O mesmo vale para o CT-NOT-02 (#27), registrado como não verificável. A entrega por push dessas notificações é a US #207, ainda sem PR mergeado.
2. **#174** não tem cenários BDD na issue (só o escopo técnico). Os casos CT-PAR-01 e CT-PAR-03 foram escritos a partir da descrição dos PRs #184, #185 e #192.
3. **#21 e #26** foram entregues depois da escrita dos casos e não têm caso manual dedicado; ficam cobertas pelos testes automatizados listados. Escrever os casos é trabalho futuro.
4. **#195 / #200:** o Web Push foi entregue (PR #196), mas a validação em aparelho real depende da issue #200 (chaves VAPID pelo CI, PR #210 em `homolog`), ainda aberta. Não há caso manual; o CT-VIA-08 (aviso com o app aberto) ficou não verificável hoje.
5. **US sem entrega, fora desta matriz:** #28 (alerta de cancelamento), #199 (fallback colaborativo) e #207 (push dos alertas) estão abertas e sem PR mergeado; #115 e #118 estão fora de escopo (trabalho futuro, segundo a issue #206).
6. **Defeitos da execução de 27 e 28/10** e a correção que cada um recebeu: #211, #212 e #213 (PR #218; o #213 também no PR #224), #215 e #216 (PRs #219 e #225), #221 (PR #222), #227 (PR #228), #230 e #237 (PR #238), #231 (PR #239) e #232 (PR #240). O #214 foi reclassificado como comportamento intencional da #179. Seguem abertas sem PR: #233 (rota sem resultado a investigar), #234, #236 e #243. Os defeitos com correção em `homolog` aparecem na linha da US afetada.
7. Issues "aberta · Homolog" estão mergeadas em `homolog` e aguardam a promoção para `main` (DoD de dois níveis do `AGENT.md`); a última promoção (PR #203) é de 22/10. Os PRs #209, #210, #218 a #225, #228 e #238 a #240 estão só em `homolog`.

## 3. Cobertura dos cenários por casos manuais

| Medida | Valor |
|---|---|
| Linhas da matriz (a #13/#133/#237, a #31/#212/#221 e a #195/#200 contam como uma linha) | 32 |
| Com ao menos um caso manual | 27 (as 5 exceções: #21, #22, #26, #195/#200 e #217, ver notas 1, 3 e 4) |
| Casos manuais escritos | 49 (18 P1, 24 P2, 7 P3) |
| Por severidade | 1 crítica, 28 altas, 20 médias |
| Casos com resultado em 28/10/2026 | 44 (33 aprovados, 10 aprovados em parte ou com ressalva, 1 reprovado por configuração) |
| Casos sem resultado | 5 (3 não verificáveis hoje: CT-NOT-02, CT-VIA-07, CT-VIA-08; 2 não executados: CT-MAP-03, CT-ETA-03) |

> Contagens a partir de [`casos-de-teste.md`](casos-de-teste.md) e do [quadro geral](execucao-casos-p1.md#quadro-geral-dos-49-casos-atualizado-em-2810). O único reprovado (CT-VIA-01) falha por configuração (raio de embarque em 100 km em produção, mantido para a demonstração), não por defeito de código; ver o [plano de testes](plano-de-testes.md).
