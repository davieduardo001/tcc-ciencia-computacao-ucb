# Matriz de Rastreabilidade — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/matriz-rastreabilidade.md>

Liga cada User Story (ou card) entregue aos seus cenários BDD, aos [casos de teste manuais](casos-de-teste.md), aos PRs que a entregaram e aos arquivos de teste automatizados que a cobrem.

**Como foi montada** (16/10/2026, `homolog` @ `07c9edc`):
- **PRs:** PRs mergeados cujo título cita a US ou cujo corpo tem `Closes`/`Refs` para ela (`gh pr list --state merged --json number,title,body`). Os arquivos de teste de cada PR vêm de `gh pr view --json files`.
- **Estado:** estado da issue no GitHub e coluna do projeto *Projeto-Final-Catolica-CS*. "Entregue" quer dizer mergeado; issues abertas na coluna *Homolog* esperam a promoção para `main` e a validação em produção.
- **Arquivos de teste:** os principais, por nome; a lista completa com contagens está no [relatório unitário](relatorio-testes-unitarios.md). Caminhos relativos a `src/backend/` (arquivos `test_*.py`) e `src/frontend/` (arquivos `*.test.ts(x)`).

## 1. Matriz

| US / card | Título | Estado | Cenários na issue | Casos manuais | PRs | Testes automatizados principais |
|---|---|---|---|---|---|---|
| #10 | Login com e-mail e senha | fechada · Done | 3 | CT-AUT-02, 03 | #75 | `auth/tests/test_login.py`, `app/login/__tests__/page.test.tsx` |
| #11 | Criar nova conta | fechada · Done | 5 | CT-AUT-01 | #52 | `auth/tests/test_registro.py`, `app/cadastro/__tests__/page.test.tsx` |
| #12 | Login via Google | fechada · Done | 1 | CT-AUT-04 | #91 | `auth/tests/test_google_auth.py`, `test_google_login.py`, `app/login/__tests__/GoogleLoginButton.test.tsx` |
| #13 / #133 | Recuperação de senha (backend / telas) | fechadas · Done | 3 / 7 | CT-AUT-05 | #87 / #153 | `auth/tests/test_recuperacao_senha.py`, `app/recuperar-senha`, `app/redefinir-senha` |
| #31 | Ciclo de vida da sessão | fechada · Done | 4 | CT-AUT-03, 06, 07 | #56, #66 (citam a US) | `gateway/tests/test_auth_proxy.py`, `test_me_proxy.py`, `test_rotas_publicas.py` |
| #14 | Mapa com localização atual | fechada · Done | 3 | CT-MAP-01, 02, 03 | #85 | `app/mapa/__tests__/MapaInterativo.test.tsx` |
| #15 | Buscar linha por número | fechada · Done | 3 | CT-MAP-04, 05 | #99 | `mobilidade/tests/test_linha_service.py`, `test_linhas_route.py`, `test_linha_mock_provider.py` |
| #16 | Rastrear ônibus em tempo real | fechada · Done | 3 | CT-MAP-07, 08 | #120, #124 | `mobilidade/tests/test_posicao_service.py`, `test_posicoes_route.py` |
| #17 | Trajeto e paradas da linha | fechada · Done | 3 | CT-MAP-04, 06 | #105, #108, #109, #110, #111, #114 | `mobilidade/tests/test_linhas_route.py`, `test_osrm_router.py`, `test_polyline_decoder.py`, `test_semob_source.py` |
| #18 | Detalhes de uma parada | fechada · Done | 3 | CT-PAR-01, 02, 03 | #169 | `mobilidade/tests/test_paradas_route.py`, `MapaInterativo.test.tsx` |
| #19 | ETA do ônibus até a minha parada | fechada · Done | 5 | CT-ETA-01, 02, 03 | #154, #160 | `mobilidade/tests/test_eta_service.py`, `test_eta_trajeto.py`, `test_posicoes_route.py` |
| #20 | Calcular rota por ônibus | fechada · Done | 5 | CT-ROT-01, 02, 03, 04 | #116, #119 | `mobilidade/tests/test_rota_service.py`, `test_rotas_route.py`, `test_geocode_service.py`, `app/mapa/__tests__/PlanejadorViagem.test.tsx` |
| #159 | ETA real da rota planejada | fechada · Done | 3 | CT-ROT-02 | #160 | `mobilidade/tests/test_eta_trajeto.py`, `test_rota_service.py` |
| #22 | Notificações de rotas preferidas | fechada · Done | 3 | sem caso dedicado (ver nota 1) | #94 | `colaboracao/tests/test_notificacoes.py` |
| #23 | Reportar ocorrência | fechada · Done | 3 | CT-COL-01, 02, 03 | #162 | `colaboracao/tests/test_ocorrencias.py`, `app/ocorrencias/reportar/__tests__/page.test.tsx` |
| #24 | Ver ocorrências de outros passageiros | **aberta** · Homolog | 3 | CT-COL-04, 05 | #180 | `colaboracao/tests/test_ocorrencias.py`, `app/ocorrencias/__tests__/page.test.tsx` |
| #25 | Rota favorita | **aberta** · Homolog | 3 | CT-ROT-05 | #176 | `colaboracao/tests/test_favoritos.py`, `app/favoritos/__tests__/page.test.tsx` |
| #27 | Alerta de atraso | fechada · Done | 3 | CT-NOT-02 | #152 | `mobilidade/tests/test_servico_rastreamento.py`, `test_servico_notificacoes.py`, `test_routes.py` |
| #29 | Preferências de notificação | fechada · Done | 3 | CT-NOT-01 | #127 | `colaboracao/tests/test_preferencias_notificacao.py`, `app/configuracoes/__tests__/page.test.tsx` |
| #30 | Tutorial no primeiro acesso | fechada · Done | 3 | CT-MAP-09 | #158 | `auth/tests/test_first_access.py`, `app/tutorial/__tests__/page.test.tsx` |
| #171 | Pegar o ônibus | **aberta** · Homolog | 4 | CT-VIA-01 a 05, 07 | #186, #187, #191 | `mobilidade/tests/test_viagem.py`, `ViagemContext.test.tsx`, `FaixaDaViagem.test.tsx`, `BotoesDaViagem.test.tsx` |
| #172 | Alerta de proximidade | **aberta** · Homolog (parcial) | 4 | CT-VIA-08 | #178, #186, #194 | `mobilidade/tests/test_servico_proximidade.py`, `test_worker_proximidade.py`, `test_eta_destino_trajeto.py`, `test_alerta_proximidade_entrega.py`, `AvisoDeProximidade.test.tsx` |
| #173 | ETA: mapeamento entre paradas | **aberta** · Homolog | 4 | CT-PAR-04, CT-ETA-01 | #177, #185 | `mobilidade/tests/test_paradas_fisicas.py`, `test_ingestao_paradas.py`, `test_horarios_por_dia.py`, `test_chegadas_parada.py` |
| #174 | Follow-up da US #18 | **aberta** · Homolog | sem BDD na issue (ver nota 2) | CT-PAR-01, 03 | #192 | `mobilidade/tests/test_parada_horarios_por_linha.py`, `SaidasDoTerminal.test.tsx` |
| #179 | Navegação, rotas e ETA (card) | **aberta** · Homolog | regras RN-01 a RN-15 | CT-ETA-04, CT-ROT-07, CT-PAR-04 | #181 a #185 | `AppShell.test.tsx`, `contraste.test.ts`, `PlanejadorViagem.test.tsx`, `resumoViagem.test.ts`, `SeloFonte.test.tsx` |
| #188 | Bug: `X-User-Id` do cliente | **aberta** · Homolog | 4 | CT-SEG-01 | #189 | `gateway/tests/test_proxy.py` |
| #190 | Paradas de subir e descer na rota | **aberta** · Homolog | 11 | CT-ROT-06, CT-VIA-06 | #191, #193 | `mobilidade/tests/test_chegadas_da_rota.py`, `TempoNaParada.test.tsx`, `useChegadasDaRota.test.tsx`, `BotoesDaViagem.test.tsx` |

## 2. Notas

1. **#22** são notificações geradas no servidor. Segundo o comentário da #172 sobre o alerta de atraso (#27), o notificador usado pelos serviços de alerta é o `NotificadorNulo`, que não entrega nada ao usuário; sem canal de entrega não há comportamento observável na tela para um caso manual, e a US fica coberta só por teste automatizado. Reavaliar quando o Web Push existir (issue #195).
2. **#174** não tem cenários BDD na issue (só o escopo técnico). Os casos CT-PAR-01 e CT-PAR-03 foram escritos a partir da descrição dos PRs #184, #185 e #192.
3. **US sem entrega, fora desta matriz:** #21 (sem código em `homolog` nem em `main`), #26, #28, #115 e #118 (backlog).
4. Issues fechadas aparecem como entregues em produção; as marcadas "aberta · Homolog" estão mergeadas em `homolog` e aguardam a promoção para `main` (DoD de dois níveis do `AGENT.md`).

## 3. Cobertura dos cenários por casos manuais

| Medida | Valor |
|---|---|
| USs e cards listados (a #13 e a #133 contam como uma linha) | 27 |
| Com ao menos um caso manual | 26 (a #22 é a exceção, ver nota 1) |
| Casos manuais escritos | 49 (18 P1, 24 P2, 7 P3) |
| Por severidade | 1 crítica, 28 altas, 20 médias |
| Casos executados até 16/10/2026 | 0 |

> Contagens a partir de [`casos-de-teste.md`](casos-de-teste.md); a última linha é o ponto de atenção desta documentação: os casos existem, mas ainda precisam ser executados.
