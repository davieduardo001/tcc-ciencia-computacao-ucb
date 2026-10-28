# Execução dos Casos P1 — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/execucao-casos-p1.md>

Registro da primeira execução dos casos P1 de [`casos-de-teste.md`](casos-de-teste.md). Segue as regras do [plano de testes](plano-de-testes.md): todo resultado tem evidência; o que não foi executado é dito como tal.

**Data:** 27/10/2026 · **Ambiente:** Gateway de produção `https://movecity-gateway.fly.dev` (não há homologação separada, por decisão de custo) · **Método:** requisições HTTP ao Gateway com `curl` e jar de cookies, a mesma via que o frontend usa. A parte de tela foi executada depois, no navegador (ver tabela de tela abaixo).

> **Efeito colateral:** foi criada a conta de teste `qa.movecity.1793098062@example.com` no banco compartilhado (cadastrada, inclusive, sem aceite dos termos, ver AUT-01). Deve ser removida.

## Resumo

> Esta tabela é o resultado da **primeira execução dos 18 casos P1 (27/10)**. O estado atual dos 49 casos está no [quadro geral](#quadro-geral-dos-49-casos-atualizado-em-2810) mais abaixo.

| Estado | Casos |
|---|---|
| Aprovado | AUT-02, AUT-06, MAP-01, MAP-02, MAP-04, MAP-05, ETA-01, ETA-02, ROT-01, ROT-02, VIA-03, SEG-01 (parcial) |
| Aprovado com ressalva | VIA-01 (ver abaixo), VIA-02 (parcial) |
| **Reprovado** | **AUT-01**, **AUT-03**, **PAR-01**, **PAR-04** |
| Não executado | nenhum |

**18 de 18 casos P1 executados, 4 reprovados.** Parte pela API (autenticação, busca, rota) e parte no navegador, em `movecity-frontend.vercel.app` na largura de desktop (1280 px) e de celular (390 px), com a conta do próprio usuário. Com a posição do marcador azul em Sol Nascente/Ceilândia, longe das linhas.

## Resultados

| ID | Estado | Evidência |
|---|---|---|
| CT-AUT-01 | **Reprovado** | `POST /api/auth/registrar` com `termos_aceitos:false` respondeu **200** e criou a conta. Esperado: recusar. Se a tela bloqueia, a regra existe só no cliente. Cadastro repetido do mesmo e-mail: 409 (correto). |
| CT-AUT-02 | Aprovado | Senha errada: 401 `Usuário ou senha inválidos`. Correta: 200 com cookies `access_token` (1 h) e `refresh_token` (7 dias), `HttpOnly; Secure; SameSite=None`. |
| CT-AUT-03 | **Reprovado** | `GET /api/auth/me` com o cookie: 200. `POST /api/auth/refresh` com o cookie: **404 `Not Found`**. O Gateway repassa para `/auth/refresh` do Auth Service, e `src/backend/auth/routes.py` **não define essa rota**. Passada 1 h, o usuário perde a sessão, contrariando "renovado sem pedir login" (#31 c2). |
| CT-AUT-06 | Aprovado | `POST /api/auth/logout`: 200; depois `GET /api/auth/me`: 401 `Não autenticado`. Sem cookie, 401 também. |
| CT-MAP-04 | Aprovado (API) | `GET /api/mobilidade/linhas?q=0.110` retorna `0.110 — Circular - Rodoviária do Plano Piloto / UNB`; `GET /linhas/0.110` traz 4 paradas, trajeto de 643 pontos e horários previstos. |
| CT-MAP-05 | Aprovado (API) | `?q=99999zzz` retorna `[]`, 200. A mensagem "linha não encontrada" é da tela, **não verificada**. |
| CT-ROT-01 | Aprovado (API) | `GET /api/mobilidade/rotas` de Taguatinga Centro à Rodoviária do Plano devolveu **10 opções**; a primeira, linha 383.1, embarque a 89 m, desembarque a 62 m, 25 paradas. Destino fora da área: `[]`. Linha do tempo na tela não verificada. |
| CT-SEG-01 | Aprovado (parcial) | `GET /api/auth/me` com `X-User-Id: 0000…` devolveu a identidade do **usuário do cookie**, ignorando o cabeçalho. Confirmação numa rota de Colaboração não foi possível: a consulta usada respondeu 500 (observação 1). |

## Resultados de tela (27/10, ~08:00, desktop e celular)

| ID | Estado | Evidência |
|---|---|---|
| CT-MAP-01 | Aprovado | Mapa abre com o marcador azul da posição do usuário, em desktop e em celular. |
| CT-MAP-02 | Aprovado | Com a permissão de localização do site desativada pelo usuário, o mapa abre na região padrão (Taguatinga/Ceilândia) e mostra o aviso "…possível obter sua localização. Exibindo a região padrão (Taguatinga/Ceilândia)." O app não quebra e o botão de recentrar fica desabilitado. **Observação de interface:** o início do aviso ("Não foi") fica coberto pelos botões "Para onde você vai?" e "Buscar parada" em 1280 px. |
| CT-MAP-04 | Aprovado | Busca `0.110` sugere a linha; ao escolher, abre o painel com nome, sentido, trajeto desenhado, 4 paradas e "10 ônibus em operação agora" (11 depois). No celular o painel vira folha inferior. |
| CT-PAR-01 | Aprovado na revalidação (ver seção "Revalidação") | Ao tocar na parada `QNL 10 — Taguatinga Norte` (PR-43869) o painel mostra nome, código, linhas e "Próximas saídas do terminal", com o aviso de que não é a hora em que passa na parada. **Não há a seção "Chegando nesta parada"** exigida pelo caso. **Nota (revisão):** pela decisão da #179 a seção fica escondida sem chegadas; o caso foi escrito esperando-a sempre. O defeito #214 foi reclassificado como comportamento intencional, e o caso precisa ser reescrito. |
| CT-PAR-04 | **Reprovado** | Sem a seção, também não há, por linha, o tempo com selo nem "Sem previsão no momento". |
| CT-ETA-01 | Aprovado | Com a posição simulada em DevTools → *Sensors* (lat -15.7934, lng -47.8825, Setor Bancário Sul), as etiquetas dos ônibus da 0.110 mostram o ETA (`<1 min`, `1 min`, `18 min`…). O popup do carro 124541 (sentido ida, 8 km/h) diz "Chega na parada Eixo L Central, Setor Bancário Sul em menos de 1 min" com o selo **ao vivo** e "Posição de 2 min atrás". O popup do carro 124621, parado, diz "Sem previsão no momento" (CT-ETA-02). O usuário operou os toques com o DevTools aberto, porque a extensão perde a conexão com a aba nessa condição; a leitura foi minha. **Observação:** o selo "ao vivo" convive com uma posição de 2 min atrás. |
| CT-ETA-02 | Aprovado | Popup do ônibus: "Sem previsão no momento" e "Posição de 1 min atrás"; nenhum tempo inventado. |
| CT-ROT-01 | Aprovado | De Terminal Taguatinga Sul à Rodoviária do Plano Piloto: várias opções, a primeira com a linha 0.306 (selo `ESTIMADO`, "2 ônibus rodando agora · ao vivo"), linha do tempo (caminhar, embarcar, 57 paradas, descer, caminhar) e "Sem previsão no momento" onde faltou dado. |
| CT-ROT-03 | Aprovado | Da posição do usuário à Rodoviária: "Nenhuma linha liga esses dois pontos — nem com troca de ônibus." |
| CT-ROT-02 | Aprovado | Da posição do usuário (Avenida do Valo) à UCB (campus QS 06): "5 opções · 1 direta, 4 com baldeação". Na opção `0.376` + `0.092` a tela mostra as duas linhas, "Baldeação: caminhe 1 min (114 m) e pegue a linha 0.092", "15 ônibus rodando agora · ao vivo" para o segundo trecho e o rodapé que diz que só a espera do primeiro ônibus é ao vivo e o resto é estimado. A rota foi montada pelo usuário no navegador. |
| CT-VIA-01 | Aprovado, com ressalva | "Peguei este ônibus" abriu a faixa `Em viagem · linha 0.110`. **Ressalva:** o marcador do usuário estava em Sol Nascente e o ônibus perto do Plano Piloto, a dezenas de km; o caso prevê recusar a mais de 100 m. A viagem foi aceita, e não verifiquei por quê (posição real do aparelho, regra de proximidade ou ausência de checagem). A investigar. |
| CT-VIA-02 | Aprovado (parcial) | A faixa mostra a próxima parada; "Paradas" abre a orientação de tocar na parada e escolher "Descer nesta parada". Contagem de paradas restantes **não executada**. |
| CT-VIA-03 | Aprovado | "Cheguei" encerrou a viagem; a faixa sumiu e o app voltou ao mapa. |

**Celular (390 × 844):** a barra inferior (Mapa, botão `+`, Perfil), a busca, a folha da linha e o planejador de rota funcionam. Observação de interface: o botão `+` flutua sobre o fim do painel e cobre o item "Terminal Taguatinga Centro" da lista de paradas.

## Mobile: folha de rota durante a viagem (evidência do usuário, 27/10)

Fluxo em 375 px de largura, na rota 0.331 + 0.960 (1 baldeação), na conta do usuário, relatado e capturado por ele. As imagens estão em [`evidencias/`](evidencias/).

| # | Situação | O que se vê | Imagem |
|---|---|---|---|
| 1 | Resultado da rota, antes de embarcar | A folha ocupa a parte baixa e termina atrás da barra inferior: o botão "Peguei este ônibus" fica cortado e coberto pelo botão `+` | `mobile-viagem-1-folha-resultado.png` |
| 2 | Depois de tocar "Peguei este ônibus" | A viagem começa ("Em viagem · linha 0.331 · Acompanhando o ônibus"), mas a **folha com a rota inteira continua aberta, flutuando** sobre o mapa, com o botão de camadas e o de localização espiando pela borda | `mobile-viagem-2-folha-flutuando.png` |
| 3 | Usuário arrasta a folha para baixo | Sobra uma faixa branca "Para onde você vai?" sem conteúdo, com o mapa e os botões por baixo; o estado não vira o de viagem | `mobile-viagem-3-folha-arrastada.png` |

**Comportamento esperado (do usuário, como no Waze):** ao embarcar, a folha de planejamento some ou desce, e o foco fica no estado da viagem, com poucos controles: **"Peguei este ônibus"/"Cheguei"** e **"Reportar ocorrência"**; a rota completa fica a um toque, recolhida.

### Complemento: posições da folha e linha sobre rota

| # | Situação | O que se vê | Imagem |
|---|---|---|---|
| 4 | Usuário puxa a folha da rota para cima | Abre quase em tela cheia, com a rota e o botão "Peguei este ônibus" visíveis (é o resultado desejado) | `mobile-folha-4-puxada-max.png` |
| 5 | Usuário solta | A folha **volta sozinha** para a posição do meio, em vez de permanecer onde foi deixada | `mobile-folha-5-volta-para-meio.png` |
| 6 | Linha 0.110 pesquisada com a rota ainda aberta | O painel da linha ("0.110 — Taguatinga / Rodoviária", "11 ônibus em operação agora") aparece **sobreposto** à folha da rota, que fica espiando embaixo ("Para onde você vai?") atrás do botão `+`. Duas folhas se cruzam e as informações da rota e da linha se misturam | `mobile-folha-6-linha-sobre-rota.png` |

**Esperado (do usuário):**
1. **Três posições** para a folha, que fica onde o usuário a deixou: **máxima** (tela quase cheia), **média** (a atual) e **mínima** (só o cabeçalho, com o mapa em foco).
2. **Uma coisa de cada vez:** a linha pesquisada deve usar o **mesmo padrão de folha** da rota, no lugar de um painel diferente por cima. Rota e linha não aparecem juntas na tela.

**Severidade proposta:** média (atrapalha o uso e a leitura no celular, mas não impede concluir a viagem). Relaciona-se com a #208 (alinhamento de UX) e com a observação do botão `+` cobrindo conteúdo.

## Casos P2/P3 executados

| ID | Estado | Evidência |
|---|---|---|
| CT-SEG-02 | Aprovado | Sem cookie, o Gateway de produção responde **200** em `/docs`, `/redoc`, `/openapi.json`, `/health` e `/` (rotas públicas, #149) e **401** em `/api/auth/me`, `/api/mobilidade/linhas`, `/api/colaboracao/...`, `/api/doc` e `/gateway/hello`. Entradas mortas da lista de rotas públicas continuam protegidas, como esperado. |
| CT-AUT-07 | Aprovado | Sem cookie, `GET /api/auth/me` responde 401 `Não autenticado`. A parte de tela (redirecionar ao login) não foi verificada. |

## Casos P2/P3 executados no navegador (27/10, ~09:25, desktop 1366 px, conta do usuário)

Cada linha traz os passos e a imagem. Hora aproximada; sessão renovada por novo login às ~09:20.

| ID | Estado | Passos | Resultado e evidência |
|---|---|---|---|
| CT-MAP-01 (refeito com imagem) | Aprovado | Abrir `/mapa` logado, localização permitida | Marcador azul na posição do usuário (Avenida do Valo). [`CT-MAP-01-mapa-com-localizacao.jpg`](evidencias/CT-MAP-01-mapa-com-localizacao.jpg) |
| CT-MAP-04 (refeito com imagem) | Aprovado | Digitar `0.110` na busca, escolher a sugestão | Painel com nome, sentido, "10 ônibus em operação agora", trajeto desenhado e 4 paradas. [`CT-MAP-04-linha-0110-trajeto-paradas.jpg`](evidencias/CT-MAP-04-linha-0110-trajeto-paradas.jpg) |
| CT-MAP-06 | Aprovado | Com a 0.110 aberta, ampliar o trajeto | Uma seta triangular sobre o trajeto indica o sentido. [`CT-MAP-06-seta-de-sentido-ampliada.png`](evidencias/CT-MAP-06-seta-de-sentido-ampliada.png) |
| CT-PAR-03 | Aprovado (com ressalva) | Tocar numa parada e, sem esperar, em outra; depois fechar o painel antes de reabrir | O painel mostra **uma só parada** (Praça do Relógio, PR-97765) e, ao fechar, volta ao painel da linha **e não reabre depois**. Ressalva: a corrida entre as duas respostas não foi cronometrada; só confirma o resultado final. [`CT-PAR-03-painel-da-parada.jpg`](evidencias/CT-PAR-03-painel-da-parada.jpg), [`CT-PAR-03-apos-fechar-volta-ao-painel-da-linha.jpg`](evidencias/CT-PAR-03-apos-fechar-volta-ao-painel-da-linha.jpg) |
| CT-ETA-04 (parte) | Aprovado (parcial) | Abrir uma parada | O bloco "Próximas saídas do terminal" traz o aviso "Horário em que o ônibus sai da origem da linha — não é a hora em que passa nesta parada", então a saída do terminal **não é apresentada como passagem na parada**. O cruzamento com "Chegando nesta parada" não foi verificado (seção escondida, #179). Mesma imagem do PAR-03. |
| CT-ROT-04 | Aprovado | No planejador, digitar "Rodoviaria do Plano Piloto" e "Universidade Catolica de Brasilia" | Sugestões de lugares, inclusive dois campi da UCB; o escolhido vira destino. Capturas em texto na seção de rotas acima; sem imagem salva. |
| CT-ROT-07 (parte) | Aprovado (parcial) | Observar o menu lateral | Só "Mapa Interativo", "Rotas Salvas", "Ocorrências" e "Alertas"; sem "Linhas" nem "Rotas" duplicando a busca e o planejador. O **contraste** do número da linha (1,78:1 na #179) **não foi medido**. [`CT-MAP-04-linha-0110-trajeto-paradas.jpg`](evidencias/CT-MAP-04-linha-0110-trajeto-paradas.jpg) |

**Reconfirmado:** o bug da #215 persiste na produção (09:25): a parada ainda lista "06:00 · 06:20 · 06:40" como próximas saídas.

**[Superado em 28/10: CT-PAR-02 e CT-MAP-08 foram executados e aprovados; CT-MAP-03 e CT-ETA-03 seguem como descrito na seção de 28/10.]** Texto original: **Não executados e por quê:** CT-PAR-02 (não achei uma parada sem horários), CT-MAP-03 e CT-ETA-03 (precisam de posição simulada em DevTools → *Sensors*, que impede meus cliques), CT-MAP-08 (a linha tinha 10 ônibus; a vez em que "não havia ônibus" foi o 401 da sessão expirada).

## Revalidação após as correções (27/10, ~09:30, produção atualizada pelos PRs #218, #219 e #220)

| Item | Passos | Resultado |
|---|---|---|
| **#211** (CT-AUT-01) | `POST /api/auth/registrar` com `termos_aceitos:false` e com o campo ausente | **422** nos dois ("É necessário aceitar os Termos de Uso e a Política de Privacidade" e "Field required"). **Corrigido.** |
| **#212** (CT-AUT-03) | `POST /api/auth/refresh` sem cookie e com cookie inválido | **401** ("Não autenticado." e "Token inválido ou expirado."), em vez do 404 de antes: a rota passou a existir. O caminho de sucesso (renovar uma sessão real) **não foi exercitado**. Segue pendente. |
| **#215** | Abrir a parada `Marginal Norte EPTG` (PR-12243) às ~09:29 | "Próximas saídas do terminal" lista só horários a partir do atual (ex.: `0.089 09:30 · 09:55 · 10:15`) e escreve "sem saída prevista hoje" para linhas sem saída. **Corrigido.** |
| **CT-PAR-01 e CT-PAR-04** | Mesma parada, linha 0.110 selecionada | O painel mostra a seção **"Chegando nesta parada"**, por linha, com o tempo e o selo `ao vivo` (ex.: `0.089 · 26 min`) ou `previsto` (ex.: `0.159 · 09:34, em 5 min`), e **"Sem previsão no momento"** quando não há dado (`154.7`, `351.6`, `379.1`, `411.1`). **Aprovados** nesta parada. Confirma que a #214 era a regra da #179 (a seção some só sem chegadas, como na `QNL 10`), não defeito de código. [`revalidacao-CT-PAR-01-marginal-norte-eptg.jpg`](evidencias/revalidacao-CT-PAR-01-marginal-norte-eptg.jpg) |

## Casos P2/P3 executados após as correções (27/10, ~10:00, produção, conta do usuário, desktop)

| ID | Estado | Passos | Resultado e evidência |
|---|---|---|---|
| CT-MAP-09 (c1, c3) | Aprovado | `/configuracoes` > "Ver tutorial" > "Próximo" até o fim | Tutorial em **4 etapas** na ordem esperada: Buscar Linhas, Visualizar no Mapa, Reportar Ocorrência, Salvar Rota Favorita; o último botão vira "Começar". Recomeça do início ao rever. O cenário 2 (pular e não reabrir no acesso seguinte) exige conta nova e **não foi executado**. [`etapa 1`](evidencias/CT-MAP-09-tutorial-etapa-1.jpg), [`etapa 4`](evidencias/CT-MAP-09-tutorial-etapa-4.jpg) |
| CT-ROT-05 (c2) | Aprovado (parcial) | `/favoritos` > "Ir" na rota salva | A tela "Minhas Rotas" lista a favorita (`SHVP - Rua 2 - Chácara 30 → Vila São José`, linha 0.331). "Ir" abre `/mapa?painel=rotas&origem_lat=...` com origem e destino **preenchidos**, recalcula (4 opções) e mostra "Salva nos favoritos". **Salvar uma nova e remover (c1, c3) não foram executados**, para não alterar nem apagar os dados do usuário. [`lista`](evidencias/CT-ROT-05-rotas-salvas.jpg), [`ir`](evidencias/CT-ROT-05-ir-recalcula-rota.jpg) |
| CT-NOT-01 (#29) | **Reprovado antes, aprovado depois** | Ver a seção "Tela de Alertas (#29)" abaixo | A tela não existia (só o backend do PR #127); foi desenvolvida no PR #223, falhou em produção com 500 (defeito 20) e passou depois do PR #224. |

**Observação de privacidade (relacionada ao CT-SEG-03/LGPD):** a ação "Ir" coloca no endereço da página as **coordenadas e os nomes** de origem e destino (`origem_lat`, `origem_lng`, `destino_lat`, `destino_lng`, `origem_nome`, `destino_nome`). Esse endereço vai para o histórico do navegador e pode ser copiado e compartilhado. Se a origem for a localização do usuário, vira dado de geolocalização na URL.

## Rota, baldeação e embarque com captura (27/10, ~10:45, produção, desktop 1366 px)

| ID | Estado | Passos | Resultado e evidência |
|---|---|---|---|
| **CT-ROT-02** (refeito com imagem) | Aprovado | `/favoritos` > "Ir" na rota salva (SHVP Rua 2 → Vila São José) | "4 opções · todas com baldeação"; a primeira traz as linhas `0.331 ⇄ 0.960`, "1 baldeação", "Baldeação: caminhe 1 min (21 m) e pegue a linha 0.960". [`duas linhas`](evidencias/CT-ROT-02-baldeacao-duas-linhas.jpg), [`ponto de troca`](evidencias/CT-ROT-02-baldeacao-ponto-de-troca.jpg) |
| **CT-VIA-04 / CT-VIA-06** (parte) | Aprovado | Na rota, tocar "Peguei este ônibus" no trecho da `0.960`, sem ônibus reportando posição | **Recusado**: "Não conseguimos confirmar seu embarque: nenhum ônibus desta linha está perto de você agora. Tente de novo quando o ônibus estiver na parada." Não criou viagem. [`imagem`](evidencias/CT-VIA-04-embarque-pela-rota-recusado.jpg) |
| **CT-VIA-01** | **Reprovado por configuração (raio de 100 km em produção)** | Abrir a `0.110`, tocar num ônibus (carro 124931) e em "Peguei este ônibus", com o marcador do usuário em Avenida do Valo (Ceilândia) e o ônibus no Setor Bancário Sul | **Aceito**: faixa "Em viagem · linha 0.110 — Próxima parada: Eixo Rodoviário, Setor Bancário Sul", popup "Você está neste ônibus". Na rede: `POST /api/mobilidade/viagens` **201**. O caso e o PR #219 (#216) esperavam recusar a mais de 100 m. **Diferença entre os caminhos:** pela rota o servidor recusa; pelo popup aceita. [`popup`](evidencias/CT-VIA-01-popup-do-onibus.jpg), [`aceito`](evidencias/CT-VIA-01-embarque-aceito-longe-do-onibus.jpg) |
| **CT-VIA-03** | Aprovado | "Cheguei" depois da viagem | `POST /viagens/<id>/encerrar` **200**; a faixa some e o app volta ao mapa. Viagem desfeita. |

**Causa encontrada (configuração, não código):** o secret `RAIO_EMBARQUE_M` do app `movecity-mobilidade` no Fly.io está em **`100000`** (lido com `flyctl ssh console -a movecity-mobilidade -C "printenv RAIO_EMBARQUE_M"`). O código usa 100 m como padrão (`viagem_service.py`, `_limite_do_ambiente("RAIO_EMBARQUE_M", 100.0)`) e `docs/secrets-por-plataforma.md` documenta 100. Com 100 km, qualquer ônibus da linha "está perto", e a regra de 100 m fica **na prática desligada em produção**. A rota recusou porque a `0.960` não tinha **nenhum** ônibus reportando posição, não por distância. Defeito reclassificado: **configuração de teste deixada em produção**, não bug de código. Correção: voltar o secret a `100` (`flyctl secrets set RAIO_EMBARQUE_M=100 -a movecity-mobilidade`). **Decisão do grupo (27/10): manter 100 km até a defesa**, para demonstrar o embarque de qualquer lugar; **limite conhecido** da demonstração, a reverter para 100 m depois.

## Ocorrências e linha sem ônibus (27/10, ~10:35, produção, conta do usuário, sessão válida)

| ID | Estado | Passos | Resultado e evidência |
|---|---|---|---|
| **CT-MAP-08** | Aprovado | Buscar `0.960` (sem ônibus no horário) | Painel: "Nenhum ônibus em operação no momento. **Próxima saída prevista do terminal: 12:30.**" Com sessão válida (diferente do falso positivo do 401). Observação de dados: a lista de paradas repete muitos nomes iguais ("Avenida Recanto das Emas, Recanto das Emas" ~25 vezes) e traz "Parada sem nome cadastrado". [`imagem`](evidencias/CT-MAP-08-linha-sem-onibus-0960.jpg) |
| **CT-COL-01** | Aprovado | `/ocorrencias` > "Reportar" > linha `0.110`, tipo **Lotação**, descrição "TESTE QA da equipe — ignorar (caso CT-COL-01)" > "Enviar reporte" | Mensagem "Reporte enviado! Obrigado por ajudar outros passageiros." Autorizado pelo usuário; escolhido um tipo que exige 2 confirmações. [`formulário`](evidencias/CT-COL-01-formulario.jpg), [`preenchido`](evidencias/CT-COL-01-formulario-preenchido.jpg), [`enviado`](evidencias/CT-COL-01-reporte-enviado.jpg) |
| **CT-COL-04** | Aprovado (parcial) | Ver `/ocorrencias` antes e depois do reporte; filtrar por linha | Antes: "Nenhuma ocorrência ativa no momento." Depois: "Lotação — 0.110, agora mesmo, **Aguardando confirmação**" com o texto do teste. Com o filtro `0.110` ela permanece. O filtro por outra linha (`0.960`) foi capturado em "Carregando ocorrências...", **sem o estado final**, então a exclusão pelo filtro **não está comprovada**. [`vazia`](evidencias/CT-COL-04-lista-vazia-antes.jpg), [`na lista`](evidencias/CT-COL-04-ocorrencia-na-lista.jpg), [`filtro`](evidencias/CT-COL-04-filtro-outra-linha-carregando.jpg) |

**Ocorrência de teste em produção:** criada às ~10:35; segundo a própria tela, "sai da lista sozinha quando perde a validade". A expiração (CT-COL-05) pode ser conferida voltando depois.

## Autenticação executada pelo usuário no navegador (27/10, produção; capturas enviadas pelo usuário)

O login com Google, a recuperação de senha e o cadastro envolvem a conta Google, senha e caixa de e-mail do usuário, então foram **executados por ele**; este documento registra os resultados.

| ID | Estado | Passos | Resultado e evidência |
|---|---|---|---|
| **CT-AUT-04** (login com Google, #12) | Aprovado | Em `/login` tocar "Continuar como Davi Eduardo" > escolher a conta no seletor do Google | Entra no app, no mapa, com o perfil `teste` na barra lateral. [`tela de login`](evidencias/CT-AUT-04-login-tela-continuar-com-google.png), [`seletor do Google`](evidencias/CT-AUT-04-google-escolher-conta.png), [`logado`](evidencias/CT-AUT-04-logado-apos-google.png) |
| **CT-AUT-05** (esqueci a senha, #13/#133) | Aprovado em parte (não conclui: o sistema não envia e-mails) | `/recuperar-senha`, informar o e-mail, "Enviar link de recuperação" | Mensagem **"Se o e-mail estiver cadastrado, você receberá um link de redefinição."**, sem revelar se o e-mail existe (cenário de não expor contas). **Não verificado:** o recebimento do e-mail, a definição da nova senha com o link, link expirado e confirmação divergente. [`formulário`](evidencias/CT-AUT-05-recuperar-senha-formulario.png), [`mensagem`](evidencias/CT-AUT-05-recuperar-senha-mensagem.png) |
| **CT-AUT-01** (criar conta, #11) | Aprovado em parte | Aba "Criar conta": e-mail já cadastrado; depois um cadastro novo | **E-mail em uso:** "Este e-mail já está em uso." sob o campo. A tela mostra o medidor de senha ("Forte") com os 4 requisitos (8 caracteres, maiúscula, número, símbolo) e "Aceito os termos de uso". **Cadastro novo:** "Verifique seu e-mail para confirmar a conta." [`e-mail em uso`](evidencias/CT-AUT-01-criar-conta-email-em-uso.png), [`verifique o e-mail`](evidencias/CT-AUT-01-criar-conta-verifique-email.png) |

**Limite conhecido (confirmado pelo grupo em 27/10): o sistema não envia e-mails hoje.** Não há provedor de e-mail em produção, então **nenhuma mensagem é entregue**: nem a confirmação de conta nem o link de recuperação de senha. Isso bate com o observado: o usuário não recebeu os e-mails, e na execução por API a conta de teste entrou **sem nenhuma confirmação** (`POST /auth/login` 200 logo após o cadastro). Consequências para os testes: o **CT-AUT-05** (esqueci a senha) **não pode ser concluído** (não chega link para definir a nova senha, nem testar link expirado), e o texto da tela de cadastro, "Verifique seu e-mail para confirmar a conta.", **anuncia uma etapa que não existe**. A mensagem de recuperação ("Se o e-mail estiver cadastrado, você receberá um link...") também promete uma entrega que não ocorre. O que vale na defesa: a conta se cria e já entra; confirmação de e-mail e recuperação de senha por e-mail ficam como **trabalho futuro** (exigem um provedor de e-mail).

## Primeiro acesso e tutorial (27/10, produção; executado pelo usuário)

| ID | Estado | Resultado |
|---|---|---|
| **CT-MAP-09 cenário 1** (tutorial no primeiro acesso) | Aprovado | Ao entrar com a conta recém-criada pelo cadastro, o app levou direto ao **tutorial** (primeiro acesso), como esperado. Os cenários de pular/rever já haviam sido vistos pelo botão "Ver tutorial" em Configurações. |

## CT-VIA-05 — uma viagem por vez (27/10, produção, conta nova do usuário, desktop)

| ID | Estado | Passos | Resultado e evidência |
|---|---|---|---|
| **CT-VIA-05** | Aprovado (no nível da tela) | Planejador: de "Terminal de Taguatinga Sul" a "Rodoviária do Plano Piloto" (10 opções, 6 diretas e 4 com baldeação) > "Peguei este ônibus" na opção `0.306` > olhar as demais opções > "Cheguei" | Com a viagem ativa (faixa "Em viagem · linha 0.306"), o botão **"Peguei este ônibus" some de todas as opções**, e o card da `0.306` mostra "Você está nesta linha." Não há como iniciar uma segunda viagem pela tela. Ao encerrar, a faixa some e os botões voltam. **Não testado:** tentar uma segunda viagem direto pela API (a regra no servidor). [`opções`](evidencias/CT-VIA-05-rota-ate-rodoviaria-opcoes.jpg), [`em viagem`](evidencias/CT-VIA-05-em-viagem-sem-botoes-de-embarque.jpg), [`encerrada`](evidencias/CT-VIA-05-viagem-encerrada.jpg) |

**Observação:** logo ao embarcar, a faixa disse "O ônibus já passou de Eixo Rodoviário, Setor Bancário Sul" (a parada de descer), porque o embarque foi aceito com o ônibus já no destino, efeito do raio de 100 km (`RAIO_EMBARQUE_M`) mantido para a demonstração.

## CT-COL-02 — reporte sem autenticação (27/10, produção, via API)

| ID | Estado | Passos | Resultado |
|---|---|---|---|
| **CT-COL-02** | Aprovado | Sem cookie, `POST /api/colaboracao/ocorrencias` com linha, tipo e descrição; e `GET /api/colaboracao/ocorrencias` | **401** `Não autenticado` nos dois; nada foi gravado. A tela de redirecionamento ao login não foi verificada. |

## Tela de Alertas (US #29) — antes e depois das correções (27/10, ~10:30)

**Contexto:** a US #29 foi fechada em 22/09 só com o backend (PR #127). Reaberta em 27/10; a tela `/alertas` entrou no PR #223.

| Momento | Resultado |
|---|---|
| Depois do #223 | `/alertas` mostrou "Não foi possível carregar suas preferências. Tente novamente." Na rede: `GET /api/colaboracao/preferencias/<id>` **500**. Log do serviço: `NoReferencedTableError ... could not find table 'usuarios'` (defeito 20). [`erro 500`](evidencias/CT-NOT-01-erro-500-antes-da-correcao.png) |
| Depois do #224 (remove a FK do ORM) | A tela carrega com os valores padrão (30 min, ambos ativados). [`carregada`](evidencias/CT-NOT-01-alertas-carregada.jpg) |

**Cenários da US, em produção, depois do #224:**

| Cenário | Passos | Resultado |
|---|---|---|
| **1. Antecedência** | Tocar em "10 min" | Mensagem "Alertas serão enviados com 10 minutos de antecedência." e o botão fica selecionado. [`imagem`](evidencias/CT-NOT-01-c1-antecedencia-10min.jpg) |
| **2. Desativar um tipo** | Desligar "Cancelamento de viagem" mantendo "Chegada" | "Notificações de cancelamento desativadas."; "Chegada" segue ativada. [`imagem`](evidencias/CT-NOT-01-c2-cancelamento-desativado.jpg) |
| **Persistência** | Recarregar a página | Continuam 10 min e cancelamento desativado. [`imagem`](evidencias/CT-NOT-01-persistiu-apos-recarregar.jpg) |
| **3. Desativar todas** | "Desativar todas" | "Todas as notificações foram desativadas."; o botão vira "Reativar notificações" e os ajustes individuais são preservados ("voltam a valer quando você reativá-las"). [`imagem`](evidencias/CT-NOT-01-c3-desativar-todas.jpg) |
| **Restauração** | Reativar, religar cancelamento, voltar a 30 min | Estado padrão restaurado na conta do usuário. [`imagem`](evidencias/CT-NOT-01-restaurado-30min.jpg) |

**Estado: Aprovado** nos 3 cenários. **Limite:** só a **gravação** das preferências foi verificada. O **efeito** (o sistema passar a enviar alertas com a antecedência escolhida, ou parar de enviar) **não é verificável**: não há canal de entrega (#207, push) nem alerta de cancelamento (#28), e o serviço de rastreamento usa o `NotificadorNulo`.

## Sessão expirada na prática (27/10, ~09:05)

Evidência de campo do CT-AUT-03 / defeito #212, na conta do usuário, no navegador:

| Momento | O que se viu |
|---|---|
| ~08:00 | Usuário logado; mapa e linha 0.110 com 10 a 11 ônibus |
| ~09:05 | O painel da linha dizia **"Nenhum ônibus desta linha em operação no momento."** e a parada `QNL 10 — Taguatinga Norte` dizia **"Não foi possível carregar os detalhes da parada. Tente novamente."** |
| causa | `GET /api/mobilidade/linhas/0.110/posicoes` respondeu **401** (lido na rede da aba): o `access_token` de 1 h tinha expirado e não há `/auth/refresh` (#212) |
| após recarregar | A tela passou a mostrar "Visitante · Não autenticado", sem redirecionar ao login |

**Dois problemas, não um:**
1. A sessão cai em 1 h por falta de refresh (#212, já aberta).
2. **Novo:** com a sessão expirada o app **não manda ao login nem avisa**; mostra dados vazios ("nenhum ônibus em operação") e erros genéricos, o que é enganoso: parece que o serviço não tem ônibus, quando é a autenticação que falhou. O frontend deve tratar 401 como sessão expirada (tentar renovar, senão ir ao login com aviso). Issue #221.

Consequência para os casos anteriores: o resultado "nenhum ônibus em operação" visto às 09:05 **não vale** como evidência do CT-MAP-08 (é artefato do 401).

## Observações fora dos casos

1. `GET /api/colaboracao/preferencias/{usuario_id}` com UUID inexistente respondeu **500** em vez de 404 ou vazio. Causa não investigada.
2. "Próximas saídas do terminal" listou 06:00, 06:20 e 06:40 às 07:58: são horários que já passaram, não as próximas saídas.
3. **Resultado inconsistente na rota:** a primeira consulta da posição do usuário à UCB respondeu "Nenhuma linha liga esses dois pontos"; minutos depois o usuário refez o mesmo par e vieram 5 opções. Não foi possível reproduzir nem explicar (cache, geocodificação do destino ou origem diferente). A investigar.
4. **"Parada sem nome":** embarque e desembarque de trechos das rotas 0.306 e 0.376/0.092 aparecem como "Parada sem nome" (falta o nome no cadastro da parada).
5. `GET /api/mobilidade/linhas/0.110/posicoes` traz `eta_minutos: null` sem posição do usuário, como esperado; o ETA com localização é o CT-ETA-01 (pendente).

## CT-COL-03, CT-ETA-02 e casos não verificáveis (28/10, ~08:15, produção, conta do usuário, desktop 1366 px)

| Caso | Estado | O que foi feito e visto |
|---|---|---|
| CT-COL-03 | **Aprovado** | Na linha 0.960 enviei 4 reportes de teste ("Lotação", descrição "TESTE QA CT-COL-03 (n/4), ignorar") pela tela "Reportar". Foram aceitos exatamente **3** ("Reporte enviado! Obrigado por ajudar outros passageiros.", e a lista de ocorrências mostra os 3 como "Aguardando confirmação"). O **4º** foi barrado com "Você atingiu o limite de reportes. Tente novamente mais tarde." Bate com `LIMITE_REPORTES_POR_HORA = 3` e o 429 `limite_reportes_excedido` do código. Evidências: [`limite`](evidencias/CT-COL-03-limite-de-reportes.jpg), [`3 aceitos`](evidencias/CT-COL-03-tres-reportes-aceitos.jpg). Os 3 reportes ficam visíveis até expirarem. |
| CT-ETA-02 | **Aprovado** | Popup do carro 445711 da linha 0.306: "Sentido volta · parado", "**Sem previsão no momento**" e "Posição de 59s atrás". Não mostra tempo inventado. Evidência: [`popup`](evidencias/CT-ETA-02-popup-parado-sem-previsao.jpg). |
| CT-ROT-01 | **Aprovado** | Evidência de tela adicionada: a rota de Terminal de Taguatinga Sul até a Rodoviária mostra 10 opções (6 diretas, 4 com baldeação) em [`rota-ate-rodoviaria-opcoes`](evidencias/CT-VIA-05-rota-ate-rodoviaria-opcoes.jpg), e o card da opção direta em [`paradas`](evidencias/CT-ROT-06-paradas-embarque-desembarque.jpg). |
| CT-SEG-03 | **Aprovado** | Embarquei no carro 445711 (0.306) pelo popup, abri `GET /api/mobilidade/viagens/ativa` no navegador com a sessão e li o JSON, depois encerrei com "Cheguei" (a resposta voltou a `ativa:false`). A resposta traz `viagem` (id, linha, sentido, prefixo do veículo, `embarcou_em`), `veiculo` (posição do **ônibus**), `sinal`, `destino`, `proxima_parada`, `paradas_restantes` e `alerta_proximidade`; **não há coordenada nem trilha do usuário**. Bate com a RN-06 (a posição do usuário serve só para validar o embarque). |
| CT-VIA-08 | **Não verificável hoje** | Exige uma viagem com destino e um ônibus **se aproximando** da parada de descida, com o app aberto. Os ônibus da 0.306 estavam um parado (posição de 59 s atrás) e outro já no fim do trajeto; sem ônibus a caminho da parada de descida o aviso não tem como disparar. Como o aviso é entregue por consulta (só com o app aberto, `AvisoDeProximidade`), a única prova é em campo. **Deve ser parte do ensaio da defesa** (a demo do Luis inclui esse aviso). |
| CT-NOT-02 | **Não verificável** | O alerta de atraso depende do ciclo do worker de monitoramento e **não tem canal de entrega** (o push, #207, não existe). A lógica (limiar de 5 min, sem repetir, reset com margem) é coberta pelos testes unitários do `deduplicador` e do `monitoring_worker`, mas não há como observar o alerta no app. |
| CT-MAP-03 e CT-ETA-03 | **Não executados** | Precisam alterar a localização pelo DevTools (Sensors). Com o DevTools aberto a extensão do navegador perde o controle dos cliques, então só podem ser feitos à mão. Passo a passo para quem for fazer: DevTools, More tools, Sensors, Location, Other; escolher uma posição perto de uma parada de linha com ônibus em movimento; ver o marcador azul se mover (MAP-03) e manter o popup do ônibus aberto por ~1 min para ver o tempo mudar (ETA-03). |

## CT-COL-05 e renovação de sessão (#222) (28/10, ~09:17, produção, conta do usuário, desktop)

| Item | Estado | O que foi visto |
|---|---|---|
| CT-COL-05 | **Aprovado** | Os 3 reportes de teste do CT-COL-03 (linha 0.960, "Aguardando confirmação") foram criados às ~08:13 e apareciam na lista às ~08:15. Às ~09:17, depois de 60 min sem confirmação, "Ocorrências" mostra **"Nenhuma ocorrência ativa no momento."** Evidência: [`lista vazia`](evidencias/CT-COL-05-lista-vazia-apos-60-min.jpg); [`ontem`](evidencias/CT-COL-05-lista-sem-ocorrencia-de-ontem.jpg) é a conferência anterior. |
| **#222** (renovação da sessão) | **Validada em produção** | Ao abrir `/ocorrencias` com o token de acesso vencido, a rede da aba registrou: `GET /api/auth/me` **401**, `GET /api/mobilidade/viagens/ativa` **401**, `GET /api/colaboracao/ocorrencias` **401**, depois `POST /api/auth/refresh` **200**, `GET /api/colaboracao/ocorrencias` **200** (refeita) e `GET /api/auth/me` **200**. A tela mostrou "Carregando…" por alguns segundos e terminou logada, **sem pedir login**. Isto fecha o caminho de sucesso que o CT-AUT-03 deixou pendente. |

## Validação das correções #231 e #232 e CT-ROT-05 completo (28/10, ~09:50, produção, conta do usuário, desktop)

Depois do merge dos PRs #239 (#231) e #240 (#232) e do deploy da Vercel.

| Item | Estado | O que foi feito e visto |
|---|---|---|
| **#232** ("Parada sem nome") | **Corrigido e validado** | Rota Terminal de Taguatinga Sul → Rodoviária do Plano Piloto: o embarque passou de "Parada sem nome" para "Embarque em **Parada a 14 m de você**". O desembarque continua com o nome ("Eixo Rodoviário, Setor Bancário Sul"). O embarque ainda não mostra o tempo de espera em minutos, só o selo "ao vivo" (a ressalva do CT-ROT-06 sobre o tempo continua; o provável é o backend devolver ETA vazio nessa rota). Evidência: [`parada a 14 m`](evidencias/CT-ROT-06-parada-a-14-m-de-voce.jpg). |
| **#231** (coordenadas na URL) | **Corrigido e validado** | Em "Rotas Salvas", toque em "Ir" na rota salva. O endereço da página ficou **`/mapa?painel=rotas`**, sem `origem_lat`, `origem_lng` nem outro parâmetro de coordenada. Origem e destino vieram preenchidos e a rota foi recalculada (10 opções). Evidência: [`ir sem coordenadas`](evidencias/CT-ROT-05-ir-sem-coordenadas-na-url.jpg). |
| **CT-ROT-05** (c1, c2, c3) | **Aprovado** | Esta rodada executou também os passos que faltavam: **salvar** a rota nova ("Salvar como favorita", que apareceu em "Minhas Rotas") e **remover** pela lixeira (voltou a "Você ainda não salvou nenhuma rota"). A favorita de teste foi removida, e a conta ficou como estava. |

## Quadro geral dos 49 casos (atualizado em 28/10)

| Estado | Qtd | Casos |
|---|---|---|
| Aprovado | 33 | AUT-02, AUT-04, AUT-06, AUT-07, COL-01, COL-02, COL-03, ETA-01, ETA-02, MAP-01, MAP-02, MAP-04, MAP-05, MAP-06, MAP-07, MAP-08, MAP-09, PAR-01 (revalidado), PAR-02, ROT-01, ROT-02, ROT-03, ROT-04, SEG-02, SEG-03, VIA-03, VIA-04, VIA-05, VIA-06, NOT-01 (depois da correção), PAR-04 (revalidado), COL-05, ROT-05 |
| Aprovado em parte ou com ressalva | 10 | AUT-01 (revalidado só por API), AUT-03 (rota existe; a renovação real foi observada depois, ver #222), AUT-05 (o sistema não envia e-mail), COL-04, ETA-04, PAR-03, ROT-06, ROT-07, SEG-01, VIA-02 |
| **Reprovado por configuração** | 1 | VIA-01: o embarque é aceito longe do ônibus porque o secret `RAIO_EMBARQUE_M` está em 100 km em produção (decisão até a defesa); a regra de 100 m só vale quando o secret voltar a 100 |
| Não verificável hoje | 3 | NOT-02 (sem canal de entrega), VIA-07 (a regra fica mascarada pelo raio), VIA-08 (precisa de ônibus se aproximando) |
| Não executado | 2 | MAP-03 e ETA-03 (precisam do DevTools Sensors, à mão) |

> 33 + 10 + 1 + 3 + 2 = 49. Cada caso aparece pelo **estado final**: PAR-01, PAR-04, AUT-01, NOT-01 e VIA-01 tiveram duas execuções (antes e depois das correções). Passos e evidência de cada um estão nas seções acima.

## Pendentes

- **MAP-03 e ETA-03** (à mão, com DevTools Sensors): ver o passo a passo na seção de 28/10.
- **VIA-08 e VIA-07**: só em campo; **entram no ensaio da defesa**. Para o VIA-07, antes voltar o raio a 100 m.
- **#222 (renovação de sessão)**: validada em 28/10, ver a seção acima.
- **#217 (folha de rota)**: conferir em celular real.
- **Usabilidade (heurísticas de Nielsen)**: avaliação não feita (ver o roteiro da disciplina).

## Defeitos novos e suas issues

| Defeito | Severidade | Onde |
|---|---|---|
| #211 Cadastro aceita `termos_aceitos: false` | Alta (LGPD) | `auth/routes.py`, `schemas.py` |
| #212 `/auth/refresh` não existe no Auth Service (404) | Alta | `auth/routes.py`; gateway `routes.py:142` |
| #213 500 em `/colaboracao/preferencias/{id}` com usuário inexistente | Média | serviço de Colaboração |
| #214 "Chegando nesta parada" ausente do painel da parada (PAR-01/PAR-04) | **Reclassificado**: é o comportamento da #179, não defeito | frontend, painel da parada |
| #215 "Próximas saídas do terminal" mostra horários já passados | Média | mobilidade / frontend |
| #216 Viagem iniciada sem a checagem de proximidade esperada (VIA-01), **a confirmar** | Alta, se confirmada | mobilidade |
