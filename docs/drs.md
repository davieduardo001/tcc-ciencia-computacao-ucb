# Documento de Requisitos de Software (DRS) - Movecity

> **Versão 1.0 · 28/10/2026.** Descreve o produto **como está entregue**, não como foi planejado. "Entregue" significa mergeado em `homolog` ou `main`; o código em produção é o de `homolog` (a `homolog` é publicada na produção da Vercel e o backend é único, sem ambiente de homologação separado). O que não foi feito ou não foi medido está escrito como tal. Estrutura conforme o `Template_DRS` da disciplina.

## 1. Introdução

### 1.1 Propósito do documento
Definir e consolidar os requisitos do Movecity (aplicativo web de mobilidade urbana colaborativa para o DF, projeto-piloto em Taguatinga e Ceilândia) para servir de base ao projeto, aos testes e à manutenção. Cada requisito aponta para a User Story (issue `[US]`) de origem, o PR que o entregou e os casos de teste manuais que o exercitam.

### 1.2 Link para o Documento de Visão
[`docs/documento_visao.md`](documento_visao.md) (versão 1.1, 28/10/2026).

### 1.3 Definições, acrônimos e abreviações

| Termo | Significado |
| :--- | :--- |
| US | User Story, registrada como issue `[US]` no GitHub, com cenários BDD (Dado/Quando/Então) |
| BDD | Behavior-Driven Development; formato dos critérios de aceite |
| SEMOB | Secretaria de Mobilidade do DF; fonte dos dados de linhas, paradas e posição GPS dos ônibus |
| ETA | Tempo estimado de chegada (*estimated time of arrival*) |
| Gateway | Ponto único de entrada das requisições do frontend; valida o JWT e roteia para Auth, Mobilidade e Colaboração |
| PWA | Aplicativo web instalável na tela inicial |
| Web Push | Notificação entregue ao aparelho com o app fechado ou a tela bloqueada |
| VAPID | Chaves que identificam o servidor para o serviço de Web Push |
| LGPD | Lei Geral de Proteção de Dados |
| RF / RNF / RN | Requisito funcional / requisito não funcional / regra de negócio |
| CT | Caso de teste manual, em [`docs/qa/casos-de-teste.md`](qa/casos-de-teste.md) |
| ADR | Registro de decisão arquitetural, em [`documento_arquitetura.md`](documento_arquitetura.md), seção 10 |

### 1.4 Metodologia de elicitação
- **Lean Inception** (CAROLI, 2018), que originou o [Documento de Visão](documento_visao.md) e o backlog.
- **Histórias de usuário com cenários BDD**, escritas como issues `[US]` e refinadas ao longo das sprints (a #19, por exemplo, teve o escopo ampliado em 18/09/2026).
- **Protótipo de alta fidelidade** (issue #33) e sua adequação à identidade visual v3 (`docs/adequacao-ui-prototipo-v3.md`).
- **Pesquisa de integração** com os dados de ônibus do DF (`docs/pesquisa-integracao-onibus-df.md`).
- **Teste real e execução de casos manuais em produção** (27 e 28/10/2026), que geraram defeitos e novos requisitos corrigidos (ver [`qa/relatorio-cobertura-e-defeitos.md`](qa/relatorio-cobertura-e-defeitos.md)).

As datas de cada sessão de elicitação não foram registradas (informação do grupo, 29/10/2026).

## 2. Visão geral dos requisitos funcionais

**Abordagem:** Histórias de Usuário (US), com a lista de casos de uso (diagramas de sequência) na seção 6. O backlog priorizado é o conjunto de issues `[US]` do GitHub; a prioridade usada abaixo é a do Documento de Visão (Alta/Média), mantida por funcionalidade. Não foi aplicada técnica formal de priorização (MoSCoW, WSJF), conforme o grupo.

Panorama das funcionalidades críticas (necessidades da Visão, seção 5.1):

| Necessidade (Visão) | Requisitos |
| :--- | :--- |
| Saber onde está o ônibus | RF-06 a RF-09 |
| Saber quanto falta | RF-10, RF-11 |
| Chegar de um ponto a outro | RF-12, RF-13, RF-14 |
| Acompanhar a viagem | RF-15, RF-16, RF-17 |
| Contribuir com informação de campo | RF-18 a RF-20 |
| Ser avisado de atraso e rotas | RF-22, RF-23, RF-24 (parcial); RF-28, RF-29 (não entregues) |
| Acesso seguro | RF-01 a RF-05 |
| Voltar a trajetos frequentes; aprender a usar | RF-21, RF-25, RF-26 |

Resumo do estado em 28/10/2026: **27 requisitos entregues** (RF-01 a RF-27, dos quais RF-22 e RF-23 sem entrega ao usuário) e **5 não entregues** (RF-28 a RF-32).

## 3. Especificação dos requisitos funcionais

Responsáveis conforme [`distribuicao_us.md`](distribuicao_us.md). Para as USs criadas depois do plano, o responsável é o autor da issue e o atribuído, com os PRs que a entregaram. PRs conforme `gh pr list --state merged` (títulos e corpos) e a [matriz de rastreabilidade de QA](qa/matriz-rastreabilidade.md).

### 3.1 Acesso (autenticação e sessão)

**RF-01 — Criar nova conta** · US #11 · Alta · Responsável: @brenouchihar · **Entregue** · PR #52 (aceite dos termos validado no servidor: PR #218, issue #211)
- Como novo passageiro, quero criar uma conta com nome, e-mail e senha, para personalizar minha experiência.
- Aceite: (1) cadastro com todos os campos cria a conta; (2) campo obrigatório ausente é recusado; (3) e-mail já cadastrado é recusado (409); (4) senha precisa cumprir complexidade (8 caracteres, maiúscula, número e símbolo; a tela mostra o medidor); (5) sem aceite dos termos, o cadastro é recusado (422).
- Notas: não há confirmação de conta por e-mail; a conta entra direto (defeito 21, texto da tela corrigido pelo PR #238). O texto integral dos Termos de Uso e da Política de Privacidade (#32) não está em tela do aplicativo (confirmado pelo grupo em 29/10/2026); o texto existe como comentário da issue #32 (12/06/2026, @brenouchihar).

**RF-02 — Login com e-mail e senha** · US #10 · Alta · @brenouchihar · **Entregue** · PR #75
- Aceite: (1) credenciais corretas autenticam e redirecionam ao mapa; (2) senha incorreta mostra "Usuário ou senha inválidos"; (3) a sessão persiste por cookies httpOnly.
- Notas: bloqueio da conta por 15 min após 5 tentativas falhas (`auth/routes.py`).

**RF-03 — Login com Google** · US #12 (e #92, botão) · Média · @davieduardo001 · **Entregue** · PRs #91, #93
- Aceite: (1) no primeiro acesso via Google a conta é criada e o usuário entra. Dependência externa: Google Identity (variável `GOOGLE_CLIENT_ID`, PR #95).

**RF-04 — Recuperação de senha** · US #13 e #133 · Média · @brenouchihar (#13 e #133) · **Entregue** · PRs #87, #153, #238 (envio do e-mail por SMTP, issue #237)
- Aceite: (1) solicitar a redefinição por e-mail; (2) a resposta é a mesma para e-mail existente e inexistente (não revela quem tem conta); (3) excesso de tentativas é limitado; (4) token válido redefine a senha; (5) token inválido ou expirado é recusado; (6) confirmação de senha divergente é recusada; (7) o controle deixa de ser "em breve".
- Notas: e-mail entregue e fluxo validado em produção em 28/10/2026 (CT-AUT-05); mensagens de erro sem acento (defeito 24, issue #243) abertas.

**RF-05 — Ciclo de vida da sessão** · US #31 · Alta · @davieduardo001 · **Entregue** · PRs #56, #66; `/auth/refresh` no PR #218 (#212); renovação automática no frontend no PR #222 (#221)
- Aceite: (1) recurso protegido com sessão válida responde normalmente; (2) sessão expirada é renovada automaticamente com o refresh token; (3) sessão inválida sem renovação volta ao login; (4) logout encerra a sessão.
- Notas: `access_token` de 1 h e `refresh_token` de 7 dias, cookies `HttpOnly; Secure; SameSite=None`. O Gateway descarta o `X-User-Id` enviado pelo cliente (#188, PR #189).

### 3.2 Mapa, linha e rastreamento

**RF-06 — Mapa com localização atual** · US #14 · Alta · @Kelvin963 · **Entregue** · PR #85
- Aceite: (1) com permissão, o mapa centra na posição do usuário; (2) com a localização negada, aparece o aviso "Não foi possível obter sua localização"; (3) o marcador acompanha a movimentação.

**RF-07 — Buscar linha por número** · US #15 · Alta · @Kelvin963 · **Entregue** · PR #99
- Aceite: (1) a busca devolve a linha com nome, sentido e itinerário; (2) linha inexistente mostra erro; (3) resposta em tempo adequado. A busca por número, nome ou destino (autocomplete) veio no PR #108.
- Notas: o cenário 1 da issue cita "horários previstos"; o quadro de horários da linha não foi entregue (RF-31, #118).

**RF-08 — Rastrear a posição do ônibus em tempo real** · US #16 · Alta · @Kelvin963 · **Entregue** · PRs #120, #124 (correção #121)
- Aceite: (1) ícones dos ônibus sobre o trajeto; (2) atualização automática sem recarregar; (3) sem veículo em operação, aviso e próxima saída prevista do terminal.
- Notas: posição lida ao vivo da SEMOB com cache de 20 s, nunca persistida (ADR-04).

**RF-09 — Trajeto e paradas da linha** · US #17 · Alta · @davieduardo001 · **Entregue** · PRs #105, #108, #109 (traçado pela malha viária, OSRM), #110, #111 (dados reais da SEMOB), #114
- Aceite: (1) trajeto desenhado corretamente; (2) paradas marcadas, com nome ao tocar; (3) seta indica o sentido de operação.

**RF-10 — Detalhes de uma parada** · US #18 (e follow-up #174) · Média · @louisassis · **Entregue** · PRs #169, #192 (e #177, #185, #219 no mapeamento de paradas)
- Aceite: (1) painel com nome, código, linhas e próximas saídas; (2) parada sem horários mostra mensagem; (3) fechar o painel volta ao mapa e uma resposta atrasada não o reabre.
- Notas: a seção "Chegando nesta parada" fica oculta durante uma viagem, em erro ou lista vazia (comportamento da #179, defeito 17).

**RF-11 — Tempo estimado de chegada (ETA)** · US #19, #159 e #173 (ETA pela parada física) · Alta · @louisassis (#19), @Vitoria-Albuquerque (#159), @davieduardo001 (#173) · **Entregue** · PRs #154, #160 (#19 e #159), #161, #177, #185 (#173/#179)
- Aceite: (1) ETA calculado pela posição do veículo; (2) atualizado sem recarregar; (3) sem dado, mostra "Sem previsão no momento" (o texto da US dizia "usa horário teórico"); (4) ETA exibido no marcador do ônibus; (5) marcador sem ETA calculável.
- Notas: todo tempo exibido declara a origem (ao vivo ou previsto; RN-010); o ETA é medido até a parada física, no sentido dela (RN-007).

**RF-12 — Calcular rota de origem a destino por ônibus** · US #20 e #159 · Alta · @louisassis · **Entregue** (cenário 4 não localizado) · PRs #116, #119 (baldeação), #160 (ETA real)
- Aceite: (1) rota simples; (2) rota com baldeação e ponto de troca; (3) nenhuma rota: mensagem; (5) destino por endereço ou ponto de referência (geocodificação).
- Notas: o cenário 4 (alerta de ocorrência ativa no trecho) não foi entregue: segundo o grupo está em desenvolvimento, mas não há código, issue nem branch no repositório (verificado em 29/10/2026). O PR #239 impede que as coordenadas do usuário vão para a URL (#231).

**RF-13 — Buscar parada por nome ou endereço** · US #21 · Média · @louisassis · **Entregue** · PR #197
- Aceite: (1) busca por nome com resultado; (2) busca por endereço mostra paradas num raio de 500 m; (3) sem resultado, mensagem. Os três cenários foram conferidos em produção em 29/10/2026, sem caso de teste dedicado: por nome ("Terminal", 3 paradas), por endereço ("QNL 10 Taguatinga Norte", 1 parada marcada no mapa) e sem resultado ("Nenhuma parada encontrada… tente outro nome, um bairro ou um ponto de referência próximo"); ver `docs/qa/execucao-casos-p1.md`.

**RF-14 — Paradas de subir e descer na rota, com o tempo do ônibus** · US #190 · Média · @davieduardo001 · **Entregue** · PRs #191, #193 (e #240, #219)
- Aceite: (1) só as paradas de embarque e desembarque de cada trecho em destaque; (2) tempo do ônibus na parada de embarque, com a origem; (3) tempo até a de desembarque; (4) sem ônibus, horário previsto ou "Sem previsão no momento"; (5) baldeação mostra as paradas de cada trecho; (6) "Peguei este ônibus" no trecho já define o destino; (7) ponto sem parada cadastrada aparece como "Parada sem nome"; (8) raio de embarque configurável; (9) embarque com o ônibus chegando (a validar em campo); (10) nada vale: recusa; (11) "chega na sua parada em N min" no popup do ônibus.

### 3.3 Viagem e alertas de proximidade

**RF-15 — Pegar o ônibus (embarcar, acompanhar e encerrar a viagem)** · US #171 · Alta · @Kelvin963 (atribuída), entregue por @Vitoria-Albuquerque (PRs #186 e #187) · **Entregue** · PRs #186, #187, #189, #191
- Aceite: (1) "Peguei este ônibus" registra a viagem e ativa o modo "em viagem"; (2) em viagem, mostra o veículo, a próxima parada e as paradas restantes; (3) "Cheguei" encerra; (4) sem veículo identificável, avisa e não registra.
- Notas: uma viagem ativa por usuário (índice único parcial no banco); a viagem expira em 4 h; a posição do usuário valida o embarque e é descartada (ADR-15, RN-006). Em produção o raio está em 100 km por decisão de 28/10 (a regra de uso é 100 m).

**RF-16 — Alerta de proximidade da parada (dentro do app)** · US #172 · Alta · @gualbertonathalia (conta `ngualbertolopes`, PR #178) e @davieduardo001 (conclusão, PR #194) · **Entregue** · PRs #178, #186, #194
- Aceite: (1) alerta quando o ônibus chega à distância/tempo configurado; (2) uma única vez por parada e viagem; (3) respeita as preferências (RF-24); (4) sem posição do veículo, não emite alerta impreciso.

**RF-17 — Alerta de proximidade com a tela bloqueada (Web Push)** · US #195 · Alta · @davieduardo001 · **Entregue** · PRs #196, #210 (chaves VAPID no deploy)
- Aceite: (1) ativar com consentimento explícito na tela de Configurações; (2) receber com o app fechado, e o toque abre o mapa; (3) não receber duas vezes; (4) respeita as preferências; (5) remover a inscrição (404/410 do serviço de push limpa a inscrição); (6) servidor sem chaves VAPID: controle indisponível, sem erro; (7) iPhone exige instalar o app (PWA); (8) permissão negada é explicada.
- Notas: sem caso manual dedicado; o CT-VIA-08 (aviso de proximidade) ficou "não verificável" fora de campo.

### 3.4 Colaboração

**RF-18 — Reportar ocorrência em uma linha** · US #23 · Média · @Vitoria-Albuquerque · **Entregue** · PR #162
- Aceite: (1) reporte com sucesso é registrado e exibido; (2) sem autenticação, pede login (401); (3) limite de **3 reportes por hora** por usuário, com aviso (429).
- Notas: tipos atraso, não passou, lotação, obra na via, ônibus quebrou, acidente e segurança; validados em produção (CT-COL-02, CT-COL-03).

**RF-19 — Ver ocorrências reportadas por outros passageiros** · US #24 · Média · @Vitoria-Albuquerque · **Entregue** · PR #180
- Aceite: (1) ocorrência confirmada exibida; (2) pendente exibida como "Aguardando confirmação"; (3) expirada some da lista. A issue fala em "60 min"; no código a validade varia por tipo (RN-012).
- Notas: a lista não mostra quem reportou; a expiração é resolvida na leitura. CT-COL-05 foi aprovado em produção com reportes do tipo "lotação", conferidos cerca de 64 min depois da criação (a lista estava vazia); isso é coerente com a validade de 15 min do código, mas não prova a validade de 60 min citada na issue.

**RF-20 — Confirmar ocorrência de outro passageiro** · US #26 · Média · @Vitoria-Albuquerque · **Entregue em `homolog`** (issue ainda aberta) · PR #209 (27/10/2026)
- Aceite: (1) confirmação de ocorrência pendente; (2) o autor não confirma a própria (403); (3) não é possível confirmar após a expiração (422); cada usuário confirma uma vez (409); com **3 confirmações** a ocorrência vira "confirmada".
- Notas: não há caso manual dedicado e a execução em produção não foi registrada, porque a confirmação exige contas de três outros usuários além da autora.

**RF-21 — Salvar e visualizar rota favorita** · US #25 · Média · @Vitoria-Albuquerque · **Entregue** · PR #176
- Aceite: (1) salvar a rota; (2) acesso rápido: "Ir" recalcula com origem e destino preenchidos; (3) remover. Máximo de 20 favoritos por usuário.

### 3.5 Notificações

**RF-22 — Notificações de rotas preferidas** · US #22 · Alta · @gualbertonathalia · **Entregue no servidor, sem entrega ao usuário** · PR #94
- Aceite: (1) notificação de ônibus próximo; (2) com antecedência configurada; (3) desabilitada respeita a preferência. O worker de monitoramento gera os eventos, mas o notificador é nulo; o push desses avisos é a #207 (RF-29). Sem caso manual dedicado.

**RF-23 — Alerta de atraso na linha acompanhada** · US #27 · Alta · @gualbertonathalia · **Entregue no servidor, sem entrega ao usuário** · PR #152
- Aceite: (1) alerta automático acima do limiar de atraso; (2) atualizado quando o atraso aumenta; (3) cancelado quando o ônibus normaliza.
- Notas: o worker usa `FornecedorGTFSMock` e `NotificadorNulo` (`mobilidade/main.py`); CT-NOT-02 "não verificável" (sem canal de entrega).

**RF-24 — Preferências de notificação** · US #29 · Média · @gualbertonathalia · **Entregue** (issue ainda aberta) · PRs #127, #218, #223 (tela `/alertas`), #224 (correção do erro 500, #213)
- Aceite: (1) antecedência de 5, 10, 30 ou 60 min; (2) desativar um tipo; (3) desativar todas.

### 3.6 Onboarding e instalação

**RF-25 — Tutorial no primeiro acesso** · US #30 · Média · @Vitoria-Albuquerque · **Entregue** · PR #158
- Aceite: (1) tutorial automático no primeiro acesso; (2) "Pular" não o reabre; (3) rever pelas Configurações.

**RF-26 — Instalar o Movecity na tela inicial (PWA)** · US #136 · Média · @davieduardo001 · **Entregue** · PR #137
- Aceite: (1) instalar pelo Android; (2) pelo iPhone; (3) abre no mapa; (4) dado de transporte nunca vem de cache; (5) oscilação de rede não quebra a casca; (6) ícone recortado pelo sistema. Sem caso manual dedicado.

**RF-27 — Navegação sem itens mortos** · issue #201 (UX) · Baixa · @davieduardo001 · **Entregue** · PR #202
- Aceite: a barra lateral não mostra "Nova Viagem". A issue ainda consta aberta no GitHub.

### 3.7 Requisitos não entregues

| ID | Requisito | US | Estado | Situação |
| :--- | :--- | :--- | :--- | :--- |
| RF-28 | Alerta de cancelamento de viagem | #28 | Não entregue (aberta) | Só o interruptor nas preferências; sem detecção nem envio. Cenários: notificação, sugestão de alternativa, detecção por ausência do veículo após 15 min |
| RF-29 | Push dos alertas de atraso e das rotas preferidas | #207 | Não entregue (aberta) | Reaproveitaria o canal Web Push da #195 |
| RF-30 | Planejar viagem por horário de partida/chegada (GTFS + RAPTOR) | #115 | Não entregue (aberta) | A rota usa linhas e posição ao vivo, sem horário de partida/chegada |
| RF-31 | Horários de operação da linha | #118 | Não entregue (aberta) | Há saídas do terminal por linha na parada (#174); falta o quadro completo e a próxima partida |
| RF-32 | Fallback colaborativo: posição do ônibus por passageiros, com consentimento | #199 | Não entregue (aberta) | Sem código; ETA depende do GPS da SEMOB |

## 4. Lista de regras de negócio

As regras não têm catálogo único no repositório: estão nos comentários do código e nas issues (#171, #172, #179, #190). Cada uma aparece abaixo com o ID original quando houver. **Atenção a uma colisão de numeração:** a issue #179 usa RN-01 a RN-15 e o código da viagem (`viagem_service.py`, `models/viagem.py`) usa RN-15, RN-16 e RN-17 com outro sentido; por isso o DRS usa IDs próprios (RN-001...) e registra o ID de origem.

| ID | ID na fonte | Descrição | Fonte (arquivo ou issue) | Impacto |
| :--- | :--- | :--- | :--- | :--- |
| RN-001 | RN-04 | O passageiro está **Aguardando** ou **Em viagem**; só assume "Em viagem" por indicação explícita confirmada no servidor, nunca por suposição | #179; `mobilidade/viagem_service.py`, `models/viagem.py` | RF-15 |
| RN-002 | RN-05 | Em viagem, o ETA de espera some; mostram-se a próxima parada e as paradas restantes | #179; `app/mapa/MapaInterativo.tsx`, `FaixaDaViagem.tsx` | RF-15 |
| RN-003 | RN-06 | LGPD na viagem: persiste-se o mínimo (usuário, linha, sentido, veículo, parada de destino, horários), **sem trilha de posição**; a posição do usuário valida o embarque e é descartada; nenhuma coordenada do usuário na URL | #179, ADR-15; `alembic/versions/e5f6a7b8c9d0_*`, `viagem_service.py`, `src/frontend/lib/rotaPendente.ts` | RF-12, RF-15 |
| RN-004 | RN-16 | Confirmar o embarque exige veículo **da linha**, com posição recente (até 5 min), a até `RAIO_EMBARQUE_M` do usuário (padrão 100 m; valor inválido cai para 100 m); com vários, vale o mais próximo | `mobilidade/viagem_service.py`; #190 cenários 8 a 10 | RF-14, RF-15 |
| RN-005 | RN-15 (código) | Uma viagem ativa por usuário, garantida por índice único parcial no banco | `mobilidade/models/viagem.py`, `viagem_service.py` | RF-15 |
| RN-006 | RN-17 | Viagem esquecida expira sozinha em 4 h e não gera alerta | `viagem_service.py`, `providers/viagens_ativas_banco.py` | RF-15, RF-16 |
| RN-007 | RN-07 | O ETA é medido ao longo do trajeto até a **parada física**, no sentido dela; paradas de lados opostos são diferentes | #179, #173, ADR-14; `mobilidade/chegada_service.py` | RF-10, RF-11 |
| RN-008 | RN-08 | Horário previsto nunca mistura dia útil, sábado e domingo | #179; `parada_service.py`, `chegada_service.py` | RF-10, RF-11 |
| RN-009 | RN-09 | **Não inventar:** sem posição válida (até 15 min) nem horário confiável, a resposta é "sem previsão" (`eta_minutos = null`) | #179; `chegada_service.py`, `chegadas_da_rota.py`, `schemas.py` | RF-11, RF-14, RF-16 |
| RN-010 | RN-10 | Todo número de tempo declara a origem: `ao_vivo`, `previsto` ou saída do terminal; saída do terminal nunca é exibida como "passa aqui" | #179; `schemas.py`, `app/mapa/SeloFonte.tsx` | RF-10, RF-11, RF-14 |
| RN-011 | RN-11 | Ônibus que já passou, de sentido oposto ou com dado velho não entra como "chegando" | #179; `chegada_service.py` | RF-11 |
| RN-012 | RN-12 | Posição do ônibus lida ao vivo (cache de 20 s) e nunca persistida | #179, ADR-04 | RF-08, RF-11 |
| RN-013 | RN-13 | Interface em WCAG 2.2 AA: contraste 4,5:1 (texto) e 3:1 (componentes), alvo de toque de 44 px, foco visível | #179; `app/mapa/__tests__/contraste.test.ts` | todas as telas |
| RN-014 | RN-14 | A cor da linha é a mesma no mapa e no resultado de rota | #179; `app/mapa/corDaLinha.ts`, `BadgeLinha.tsx` | RF-12 |
| RN-015 | RN-15 (#179) | Estilos usam tokens do design system (`--mc-*`), sem cor fixa | #179 | telas |
| RN-016 | RN-01 a RN-03 (#179) | Uma função, um ponto de entrada (busca de linha = barra do topo; rota = planejador); o contrato `/mapa?painel=rotas&origem_*&destino_*` dos Favoritos permanece; a navegação inferior mantém o botão central centralizado | #179; `app/favoritos/page.tsx` | RF-12, RF-21 |
| RN-017 | — | Limite de **3 reportes por hora** por usuário (429 `limite_reportes_excedido`) | `colaboracao/models/ocorrencia.py` (`LIMITE_REPORTES_POR_HORA`), `routes.py` | RF-18 |
| RN-018 | — | Validade da ocorrência por tipo: lotação 15 min; atraso, acidente e segurança 30 min; não passou e ônibus quebrou 60 min; obra na via 120 min. Expirada não aparece e é marcada na leitura; o registro não é apagado | `colaboracao/models/ocorrencia.py` (`TTL_MINUTOS`), `routes.py` | RF-19 |
| RN-019 | — | Ocorrência de tipo crowd-validado nasce "pendente" e vira "confirmada" com **3 confirmações** de outros usuários; "acidente" e "segurança" nascem confirmadas. Divergência conhecida (#249): a tela anuncia "mínimo 2 confirmações", mas o servidor exige 3 | `ocorrencia.py` (`LIMITE_CONFIRMACOES`, `TIPOS_IMEDIATOS`) | RF-18, RF-19, RF-20 |
| RN-020 | — | O autor não confirma a própria ocorrência (403); um usuário confirma uma vez (409, restrição única no banco); ocorrência expirada não é confirmada (422) | `colaboracao/routes.py` | RF-20 |
| RN-021 | — | Máximo de 20 rotas favoritas por usuário | `colaboracao/models/rota_favorita.py` (`LIMITE_FAVORITOS`), `routes.py` | RF-21 |
| RN-022 | — | Antecedência do alerta: 5, 10, 30 ou 60 min (padrão 30); notificações, alerta de chegada e alerta de cancelamento são ativáveis separadamente | `colaboracao/models/preferencia_notificacao.py` | RF-16, RF-17, RF-24 |
| RN-023 | — | O alerta de proximidade dispara uma vez por parada e viagem, respeita as preferências e não dispara sem posição do veículo | #172, #195; `mobilidade/services/servico_proximidade.py` | RF-16, RF-17 |
| RN-024 | — | Conta bloqueada por 15 min após 5 tentativas de login falhas | `auth/routes.py` (`MAX_TENTATIVAS_FALHAS`, `BLOQUEIO_MINUTOS`) | RF-02 |
| RN-025 | — | Cadastro exige aceite dos termos (422 sem aceite); a recuperação de senha responde igual para e-mail existente e inexistente | #11, #133, #211; `auth/routes.py` | RF-01, RF-04 |
| RN-026 | — | O servidor ignora o `X-User-Id` enviado pelo cliente; a identidade vem do JWT validado no Gateway | #188; `gateway/proxy.py` | todas as rotas protegidas |

## 5. Lista de requisitos não funcionais

Classificação ISO/IEC 25010. Coluna "Verificação" diz o que foi feito de fato.

| ID | Requisito | Classificação | Método previsto | Verificação em 28/10/2026 |
| :--- | :--- | :--- | :--- | :--- |
| RNF-01 | Carregamento em até 3 s em conexão 4G | Eficiência de desempenho | Medição de carregamento em 4G (ex.: Lighthouse) | **Não medido.** A ADR-12 registra que a escala a zero do Fly causa partida a frio e conflita com a meta |
| RNF-02 | Disponibilidade de 99% nos horários de pico (5h-9h, 17h-20h) | Confiabilidade | Monitoramento contínuo | **Não medida.** Sem monitoramento de uptime; free tier com escala a zero |
| RNF-03 | Proteção de dados de geolocalização (LGPD) | Segurança | Revisão de código e execução de casos | **Parcialmente verificado.** CT-SEG-03 aprovado em produção (sem trilha de posição do usuário); defeito das coordenadas na URL (#231) corrigido e validado (PR #239). Sem auditoria formal de LGPD |
| RNF-04 | Sessão por cookies httpOnly, Secure, SameSite=None; JWT validado no Gateway; rotas públicas restritas | Segurança | Execução de casos e testes do Gateway | **Verificado:** CT-AUT-02 e CT-SEG-02 aprovados; CT-SEG-01 aprovado com ressalva. SameSite=None amplia a exposição a CSRF (ADR-07). **Proteção contra XSS reduzida (#253, correção pendente):** os cookies httpOnly protegem a sessão real, mas o frontend também grava `access_token` e `refresh_token` em `localStorage` (`src/frontend/lib/api.ts`), lidos do corpo da resposta de login; as funções que os leem (`getAccessToken`, `getRefreshToken`) não são chamadas em lugar nenhum. Estado: parcial |
| RNF-05 | Validação cruzada do reporte colaborativo (3 confirmações) | Confiabilidade | Teste automatizado e demonstração | **Código e testes automatizados** (`colaboracao/tests/test_ocorrencias.py`); não exercido em produção (ver RF-20). **Divergência conhecida (#249):** a tela anuncia "mínimo 2 confirmações", mas o servidor exige 3 |
| RNF-06 | Não inventar dado: sem posição ou horário confiável, mostrar "sem previsão" | Confiabilidade | Execução de casos | **Verificado:** CT-ETA-02 e CT-PAR-04 aprovados |
| RNF-07 | Acessibilidade WCAG 2.2 AA e avaliação por heurísticas de Nielsen | Usabilidade | Cálculo de contraste e avaliação heurística | **Parcial:** contraste calculado e coberto por teste (#179); a avaliação de Nielsen foi feita por um avaliador (o método pede 3 a 5) e não houve teste com usuários reais ([`qa/avaliacao-usabilidade-nielsen.md`](qa/avaliacao-usabilidade-nielsen.md)) |
| RNF-08 | Aplicativo web responsivo e instalável (PWA) | Portabilidade | Execução de casos | **Parcial:** o layout foi revisado para mobile e tablet (PRs #135, #220); instalação e Web Push em iPhone dependem de instalar o app; o grupo testou em iPhone com resultado funcional (sem evidência registrada no repositório) |
| RNF-09 | Tolerância a falha de integração externa (SEMOB, OSRM, geocodificação, CARTO) | Confiabilidade | Revisão de arquitetura | **Definida** em [`documento_arquitetura.md`](documento_arquitetura.md) (comportamento por falha, ADR-03, ADR-11); o CARTO recua para o OSM sem a chave |
| RNF-10 | Manutenibilidade: testes automatizados e CI | Manutenibilidade | Execução do CI e medição de cobertura | **CI de 28/10/2026:** 1.640 testes automatizados (844 backend, 796 frontend). Cobertura medida em 16/10/2026: 93,7% (backend) e 89,1% (frontend, só arquivos importados por teste), não remedida desde então. Execução manual: 49 casos (32 aprovados, 11 com ressalva, 1 reprovado por configuração, 3 não verificáveis, 2 pendentes) e 26 defeitos catalogados; valores informados pelo coordenador, o relatório de QA em `main` ainda traz os números anteriores ([`qa/relatorio-cobertura-e-defeitos.md`](qa/relatorio-cobertura-e-defeitos.md)) |
| RNF-11 | Frescor da posição: feed lido ao vivo com cache de 20 s, ETA atualizado sozinho | Eficiência de desempenho | Execução de casos | **Verificado:** CT-MAP-07 aprovado; CT-ETA-03 pendente (exige localização simulada) |

## 6. Casos de uso

Os diagramas de sequência (PlantUML) ficam em [`docs/diagramas/sequencia/`](diagramas/sequencia/). Os UC10 a UC30 usam o número da US como identificador.

| Caso de uso | US / RF | Diagrama |
| :--- | :--- | :--- |
| UC10 Realizar login com e-mail e senha | #10 / RF-02 | [`UC10`](diagramas/sequencia/UC10-realizar-login-email-senha.puml) |
| UC11 Criar nova conta de usuário | #11 / RF-01 | [`UC11`](diagramas/sequencia/UC11-criar-nova-conta-usuario.puml) |
| UC12 Realizar login com Google | #12 / RF-03 | [`UC12`](diagramas/sequencia/UC12-realizar-login-google.puml) |
| UC13 Recuperar senha | #13 / RF-04 | [`UC13`](diagramas/sequencia/UC13-recuperacao-senha.puml) |
| UC14 Visualizar mapa com localização atual | #14 / RF-06 | [`UC14`](diagramas/sequencia/UC14-visualizar-mapa-localizacao-atual.puml) |
| UC15 Buscar linha por número | #15 / RF-07 | [`UC15`](diagramas/sequencia/UC15-buscar-linha-por-numero.puml) |
| UC16 Rastrear posição do ônibus em tempo real | #16 / RF-08 | [`UC16`](diagramas/sequencia/UC16-rastrear-posicao-onibus-tempo-real.puml) |
| UC17 Visualizar trajeto e paradas no mapa | #17 / RF-09 | [`UC17`](diagramas/sequencia/UC17-visualizar-trajeto-paradas-no-mapa.puml) |
| UC18 Ver detalhes de uma parada | #18 / RF-10 | [`UC18`](diagramas/sequencia/UC18-ver-detalhes-parada.puml) |
| UC19 Ver tempo estimado de chegada | #19 / RF-11 | [`UC19`](diagramas/sequencia/UC19-ver-tempo-estimado-chegada.puml) |
| UC20 Calcular rota de origem a destino | #20 / RF-12 | [`UC20`](diagramas/sequencia/UC20-calcular-rota-origem-destino.puml) |
| UC21 Buscar parada por nome ou endereço | #21 / RF-13 | [`UC21`](diagramas/sequencia/UC21-buscar-parada-por-nome-endereco.puml) |
| UC22 Receber notificações de rotas preferidas | #22 / RF-22 | [`UC22`](diagramas/sequencia/UC22-receber-notificacoes-rotas-preferidas.puml) |
| UC23 Reportar ocorrência em uma linha | #23 / RF-18 | [`UC23`](diagramas/sequencia/UC23-reportar-ocorrencia-em-linha.puml) |
| UC24 Visualizar ocorrências reportadas | #24 / RF-19 | [`UC24`](diagramas/sequencia/UC24-visualizar-ocorrencias-reportadas.puml) |
| UC25 Salvar rota favorita | #25 / RF-21 | [`UC25`](diagramas/sequencia/UC25-salvar-rota-favorita.puml) |
| UC26 Confirmar ocorrência reportada | #26 / RF-20 | [`UC26`](diagramas/sequencia/UC26-confirmar-ocorrencia-reportada.puml) |
| UC27 Receber alerta de atraso na linha | #27 / RF-23 | [`UC27`](diagramas/sequencia/UC27-receber-alerta-atraso-linha.puml) |
| UC28 Receber alerta de cancelamento de viagem | #28 / RF-28 (não entregue) | [`UC28`](diagramas/sequencia/UC28-receber-alerta-cancelamento-viagem.puml) |
| UC29 Gerenciar preferências de notificação | #29 / RF-24 | [`UC29`](diagramas/sequencia/UC29-gerenciar-preferencias-notificacao.puml) |
| UC30 Visualizar tutorial no primeiro acesso | #30 / RF-25 | [`UC30`](diagramas/sequencia/UC30-visualizar-tutorial-primeiro-acesso.puml) |
| UC171 Pegar o ônibus | #171 / RF-15 | [`UC171`](diagramas/sequencia/UC171-pegar-onibus.puml) |
| Alerta de proximidade da parada | #172 / RF-16 | diagrama em `docs/diagramas/sequencia/` (PR em andamento) |
| ETA: mapeamento entre paradas | #173 / RF-11 | diagrama em `docs/diagramas/sequencia/` (PR em andamento) |
| Paradas de subir e descer na rota | #190 / RF-14 | diagrama em `docs/diagramas/sequencia/` (PR em andamento) |
| Alerta de proximidade com a tela bloqueada (Web Push) | #195 / RF-17 | diagrama em `docs/diagramas/sequencia/` (PR em andamento) |
| Fallback colaborativo da posição do ônibus | #199 / RF-32 (não entregue) | diagrama em `docs/diagramas/sequencia/` (PR em andamento) |

Sem diagrama de sequência: #31 (RF-05, descrito em [`gateway-auth-flow.md`](gateway-auth-flow.md)), #133 (RF-04), #136 (RF-26), #159 (RF-12), #174 (RF-10), #207 (RF-29), #115 (RF-30) e #118 (RF-31).

A especificação textual de cada caso (fluxo principal, alternativos, pré e pós-condições) é, nesta versão, o conjunto de cenários BDD de cada US na seção 3, não um formulário UC### separado.

## 7. Matriz de rastreabilidade

RF → US → PR → casos de teste manuais ([`qa/casos-de-teste.md`](qa/casos-de-teste.md), executados em 27 e 28/10/2026; resultados em [`qa/execucao-casos-p1.md`](qa/execucao-casos-p1.md)). A matriz de QA com arquivos de teste automatizados está em [`qa/matriz-rastreabilidade.md`](qa/matriz-rastreabilidade.md).

| RF | US | PRs | Casos de teste |
| :--- | :--- | :--- | :--- |
| RF-01 | #11 | #52, #218 | CT-AUT-01 |
| RF-02 | #10 | #75 | CT-AUT-02, CT-AUT-03 |
| RF-03 | #12 (#92) | #91, #93 | CT-AUT-04 |
| RF-04 | #13, #133 | #87, #153, #238 | CT-AUT-05 |
| RF-05 | #31 | #56, #66, #218, #222 | CT-AUT-03, CT-AUT-06, CT-AUT-07 |
| RF-06 | #14 | #85 | CT-MAP-01, CT-MAP-02, CT-MAP-03 |
| RF-07 | #15 | #99, #108 | CT-MAP-04, CT-MAP-05 |
| RF-08 | #16 | #120, #121, #124 | CT-MAP-07, CT-MAP-08 |
| RF-09 | #17 | #105, #108, #109, #110, #111, #114 | CT-MAP-04, CT-MAP-06 |
| RF-10 | #18, #174 | #169, #192 | CT-PAR-01, CT-PAR-02, CT-PAR-03 |
| RF-11 | #19, #159, #173 | #154, #160, #161, #177, #185 | CT-ETA-01, CT-ETA-02, CT-ETA-03, CT-ETA-04, CT-PAR-04 |
| RF-12 | #20, #159 | #116, #119, #160 | CT-ROT-01, CT-ROT-02, CT-ROT-03, CT-ROT-04, CT-ROT-07 |
| RF-13 | #21 | #197 | sem caso dedicado |
| RF-14 | #190 | #191, #193 | CT-ROT-06, CT-VIA-06, CT-VIA-07 |
| RF-15 | #171 | #186, #187, #189, #191 | CT-VIA-01 a CT-VIA-05, CT-SEG-01, CT-SEG-03 |
| RF-16 | #172 | #178, #186, #194 | CT-VIA-08 |
| RF-17 | #195 | #196, #210 | sem caso dedicado |
| RF-18 | #23 | #162 | CT-COL-01, CT-COL-02, CT-COL-03 |
| RF-19 | #24 | #180 | CT-COL-04, CT-COL-05 |
| RF-20 | #26 | #209 | sem caso dedicado |
| RF-21 | #25 | #176 | CT-ROT-05 |
| RF-22 | #22 | #94 | sem caso dedicado (sem canal de entrega) |
| RF-23 | #27 | #152 | CT-NOT-02 |
| RF-24 | #29 | #127, #218, #223, #224 | CT-NOT-01 |
| RF-25 | #30 | #158 | CT-MAP-09 |
| RF-26 | #136 | #137 | sem caso dedicado |
| RF-27 | #201 | #202 | sem caso dedicado |
| RF-28 a RF-32 | #28, #207, #115, #118, #199 | não entregues | não aplicável |

Casos transversais sem RF único: CT-SEG-02 (rotas públicas do Gateway, #149, PR #150).

## 8. Restrições e premissas

| Restrição ou premissa | Fonte |
| :--- | :--- |
| **Sem PostGIS**: geometrias em colunas JSON; a única junção espacial roda em Python na ingestão (grade de ~55 m, raio de busca de 40 m) | ADR-02 |
| **Dados da SEMOB copiados por ingestão em lote** (workflow mensal `ingestao-semob.yml`); os endpoints são públicos, sem documentação nem SLA, e o catálogo pode ficar até um mês desatualizado | ADR-03; `docs/pesquisa-integracao-onibus-df.md` |
| **Posição do ônibus lida ao vivo (cache de 20 s) e nunca persistida**; sem histórico de posições | ADR-04 |
| **Sem ambiente de homologação separado**: `homolog` publica na produção da Vercel; os quatro apps do Fly.io e o banco Neon são compartilhados entre homologação e produção, por custo | `docs/deploy-plan.md`; issue #42; `docs/guia-apresentacao.md` |
| **Raio de embarque configurável** (`RAIO_EMBARQUE_M`, padrão 100 m); em produção está em 100 km por decisão de 28/10/2026, só para a demonstração na defesa | `mobilidade/viagem_service.py`; `docs/guia-apresentacao.md`; [`qa/execucao-casos-p1.md`](qa/execucao-casos-p1.md) |
| **Escala a zero no Fly** (`min_machines_running = 0`): partida a frio na primeira requisição | ADR-12; `fly.toml` |
| **Gateway como ponto único de entrada**; cookies `SameSite=None` + `Secure` porque frontend (Vercel) e Gateway (Fly) são cross-site | ADR-07; `docs/gateway-auth-flow.md` |
| **Proteção contra XSS parcial:** a sessão real usa cookies httpOnly, mas o frontend também grava os tokens em `localStorage`, expondo-os a XSS; correção pendente | issue #253; `src/frontend/lib/api.ts` |
| **Integrações externas atrás de contrato `typing.Protocol`** (mock e real) | ADR-06 |
| **Base do mapa CARTO Voyager**, com recuo para o OSM sem a chave | ADR-11 |
| **Web Push** exige chaves VAPID no servidor; em iPhone, só com o app instalado na tela inicial | #195, PR #210 |
| **Escopo geográfico**: projeto-piloto em Taguatinga e Ceilândia (os dados da SEMOB cobrem o DF inteiro) | Documento de Visão |
| **Sem validação em campo**: raio de embarque, tolerância do ETA e regra "ônibus chegando" não foram medidos | `qa/resumo-executivo.md` |

## 9. Declaração de uso ético e responsável de inteligência artificial

O projeto adota um fluxo de trabalho com agentes de IA generativa no desenvolvimento e na documentação (metodologia "Agentic Workflow" em `AGENT.md`; regras de operação em `docs/boas-praticas-ia.md`). Este DRS foi levantado a partir de issues, PRs, código e documentos do repositório com apoio de um assistente de IA para leitura e consolidação. Ferramentas: Claude Code (modelos Claude Sonnet, Opus e Haiku, da Anthropic) e OpenCode (modelos Qwen, DeepSeek e Big Pickle, além dos do Claude). A configuração do Gemini também está no repositório, sem confirmação de uso. Período: código gerado de 15/08 a 28/10/2026; as ferramentas estão versionadas desde 15/06/2026 (Claude Code), 15/08/2026 (OpenCode) e 07/03/2026 (configuração do Gemini).

- **Supervisão humana:** todo conteúdo gerado deve ser revisado por membros do grupo, que permanecem responsáveis pela exatidão e pela conformidade acadêmica. Este documento foi revisado por Davi Eduardo Costa Miranda (orquestrador); a data da revisão não foi registrada.
- **Checagem de confiabilidade:** cada afirmação deste DRS aponta para uma fonte verificável (issue, PR, arquivo de código ou documento de QA); o que não pôde ser confirmado está dito no texto.
- **Privacidade e sigilo:** nenhum dado de usuário, credencial ou dado pessoal entra neste documento; os casos de teste usam contas de teste.
- **Integridade acadêmica:** a contribuição da ferramenta é declarada aqui, conforme a orientação do template.

## 10. Histórico de revisões

| Versão | Data | Alteração |
| :--- | :--- | :--- |
| 1.0 | 28/10/2026 | Criação do DRS a partir das issues `[US]`, dos PRs mergeados, do código de `homolog` e da documentação de QA |
| 1.1 | 29/10/2026 | Responsáveis, Termos de Uso, verificações de ambiente (secrets do Fly, produção) e uso de IA confirmados pelo grupo e por conferência no repositório |
