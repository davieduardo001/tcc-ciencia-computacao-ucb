# Relatório de Testes de Integração — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/relatorio-testes-integracao.md>

Estado dos testes que exercitam a **conexão entre as peças** (serviços, banco, migrations, contêineres, frontend ↔ Gateway), as lacunas e um plano priorizado. Medido em 16/10/2026 em `07c9edc` (`homolog`). Contexto: [`README.md`](README.md) e a issue [#151](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/151).

## 1. Resumo

- O CI já cobre **três** pontos de integração reais: o banco Postgres com migrations, o boot de cada serviço com o próprio `requirements.txt` e o `/health` do Gateway.
- O que **não** está coberto é a conversa entre as peças: o proxy do Gateway é testado com o `httpx` mockado, e o frontend chama o Gateway apenas em testes com `fetch` mockado.
- Na prática, a maior parte do CI vermelho desde a Sprint 2 veio de integração (passos de migrations e de boot), e não de regra de negócio (ver a seção 4).

## 2. Inventário do que existe

### 2.1 No CI de todo PR (`.github/workflows/ci.yml`)

| Item | O que verifica | Resultado no PR #194 |
|---|---|---|
| `test-backend`, passo "Health check" | Sobe o Gateway com `uvicorn` e exige `GET /health` com sucesso | verde |
| `test-backend`, passo "Rodar migrations" | `alembic upgrade head` num PostgreSQL (`postgis/postgis:16-3.4`) | verde |
| `test-backend`, passo "Rodar testes" | `pytest -v` com o banco do serviço do CI | verde |
| `verificar-servicos` (matriz: gateway, auth, mobilidade, colaboracao) | Venv limpo com **só** o `requirements.txt` do serviço e import da aplicação, como o contêiner faz no boot | 4 de 4 verdes |
| `test-frontend` | `npm ci` e `npm test` (Jest) | verde |
| `lint` | Título do PR e commits em Conventional Commits | verde |

Fonte: `.github/workflows/ci.yml` e `gh pr checks 194` (7 checks, todos `pass`).

### 2.2 Nos testes (busca textual em `src/backend`, 56 arquivos de teste)

| Característica | Arquivos | Observação |
|---|---|---|
| Usam sessão de banco (`SessionLocal`, `create_engine`, `get_db`, `db_session`) | 20 | No CI, o banco é o Postgres do serviço |
| Desses, criam SQLite em memória | 2 (`test_servico_proximidade.py`, `test_ocorrencias.py`) | Não exercitam o Postgres |
| Usam mock ou patch (`unittest.mock`, `monkeypatch`, `patch(`) | 31 | Pontas externas e vizinhos mockados |
| Usam `TestClient`, `ASGITransport` ou `AsyncClient` | 35 | HTTP **em processo**, sem rede |

### 2.3 Gateway (`src/backend/gateway/tests`, 29 testes em 7 arquivos)

| Arquivo | Foco |
|---|---|
| `test_proxy.py` (10) | Roteamento por path e cabeçalhos; roda com `httpx.AsyncClient.request` **mockado** (inclui o descarte do `X-User-Id` do cliente, PR #189) |
| `test_auth_proxy.py` (5), `test_me_proxy.py` (4) | Login, refresh, logout e `/me` pelo proxy |
| `test_cors_ordem_middleware.py` (2) | Ordem do CORS no middleware (incidente do PR #107, segundo a #151): 401 em rota protegida deve chegar como 401, e não como erro de CORS |
| `test_rotas_publicas.py` (4) | Rotas públicas do middleware (incidente #149, corrigido no PR #150): as entradas de `ROTAS_PUBLICAS` devem corresponder a rotas reais |
| `test_status.py` (3), `test_hello.py` (1) | Endpoint `/api/status` e saúde |

### 2.4 Fora do PR (verificação posterior)

| Item | O que verifica |
|---|---|
| `deploy-fly.yml` | Roda `alembic upgrade head` contra o `DATABASE_URL` real e, depois do deploy de cada serviço, um **smoke test** nos quatro apps |
| `/api/status` (produção) | Consulta o `/health` dos quatro serviços; é o que a tela inicial exibe |
| `ingestao-semob.yml` | Ingestão mensal das linhas do SEMOB; termina com `assert total > 500` |

### 2.5 Frontend

O `src/frontend/lib/__tests__/api.test.ts` (90 testes) e os testes de página substituem `fetch` por um mock. Nenhum teste automatizado faz o frontend falar com o Gateway de verdade.

## 3. Lacunas e plano priorizado

| Prioridade | Lacuna | Por que importa | Proposta (item da #151) | Esforço |
|---|---|---|---|---|
| P1 | **Gateway ↔ serviços com HTTP real**: o proxy é testado com `httpx` mockado | O #188 (`X-User-Id` do cliente repassado) só se manifesta quando dois cabeçalhos chegam ao serviço; o PR #107 foi o mesmo tipo de falha | Subir os quatro serviços com `uvicorn` em portas locais no CI e exercitar o proxy ponta a ponta (item 3) | M |
| P1 | **Contrato front ↔ Gateway**: `fetch` mockado | Incidente do PR #81 (front chamando caminho que o Gateway não serve) | Comparar os caminhos de `lib/api.ts` com `app.openapi()["paths"]` (item 2) | P |
| P2 | **Conflito entre migrations paralelas**: 13 dos 16 vermelhos desde 22/09 falharam em "Rodar migrations" | O comentário da #172 já previa reencadear a migration caso o #177 entrasse antes | Teste de "uma só cabeça" do Alembic (`alembic heads`) no CI; a causa exata de cada vermelho não foi investigada neste relatório (ver seção 4) | P |
| P2 | **Resultado de testes só no log** | Não há tabela por execução para a review | `pytest --junitxml` e `jest --json` no `$GITHUB_STEP_SUMMARY` (item 1) | P |
| P3 | **APIs externas** (SEMOB, OSRM, Nominatim, Google) | Hoje são mocks; uma mudança de contrato só aparece em produção | Resposta gravada no PR e job semanal que chama a API real e abre issue (item 4) | M |
| P3 | **Ponta a ponta no navegador** | Nenhum fluxo (login → mapa → linha → viagem) é exercitado junto | Playwright sob demanda (item 5) | G |
| P3 | **Dispositivos e campo** | Localização real, push com tela bloqueada e iOS não têm teste | Roteiro manual do [plano de testes](plano-de-testes.md) | — |

## 4. Observação sobre as falhas de CI

Desde 22/09 houve 16 execuções vermelhas do CI de PR (detalhes no [relatório de defeitos](relatorio-cobertura-e-defeitos.md)). Por passo que falhou: **13** em "Rodar migrations", **8** em "Importar a aplicação, como o contêiner faz no boot", **3** em "Verificar Conventional Commits", **2** em "Rodar testes" (um no pytest, um no Jest) e **1** num passo antigo chamado "Verificar imports" (algumas execuções falharam em mais de um passo). Só uma causa foi confirmada no log: em 27/09, `ModuleNotFoundError: No module named 'psycopg'` derrubou as migrations e o boot dos serviços. A causa dos demais vermelhos em "Rodar migrations" **não foi investigada** aqui.

## 5. O que não foi entregue neste PR

Nenhum código de teste novo foi aberto. Os itens da seção 3 são propostas e estão registrados na #151 como Fase 2; nenhum era pequeno e independente o bastante para entrar junto de uma documentação.
