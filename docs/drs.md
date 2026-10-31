# Documento de Requisitos de Software (DRS) - Movecity

> **Versão 1.1 · 31/10/2026.** Descreve o produto **como está entregue**, não como foi planejado. "Entregue" significa mergeado em `homolog` ou `main`; o código em produção é o de `homolog`. Estrutura conforme o `Template_DRS` da disciplina.

## 1. Introdução

### 1.1 Propósito do documento
Definir e consolidar os requisitos do Movecity (aplicativo web de mobilidade urbana colaborativa para o DF, projeto-piloto em Taguatinga e Ceilândia) para servir de base ao projeto, aos testes e à manutenção. Cada requisito aponta para a User Story (issue `[US]`) de origem.

### 1.2 Link para o Documento de Visão
[`docs/documento_visao.md`](documento_visao.md).

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
| LGPD | Lei Geral de Proteção de Dados |
| RF / RNF / RN | Requisito funcional / requisito não funcional / regra de negócio |
| ADR | Registro de decisão arquitetural, no [Documento de Arquitetura](documento_arquitetura.md), seção 10 |

### 1.4 Metodologia de elicitação
- **Lean Inception** (CAROLI, 2018), que originou o [Documento de Visão](documento_visao.md) e o backlog.
- **Histórias de usuário com cenários BDD**, escritas como issues `[US]` e refinadas ao longo das sprints.
- **Protótipo de alta fidelidade** (issue #33), adaptado depois à identidade visual v3.
- **Pesquisa de integração** com os dados de ônibus do DF.
- **Teste real e execução de casos manuais em produção**, que geraram defeitos e requisitos corrigidos.

## 2. Visão geral dos requisitos funcionais

**Abordagem:** histórias de usuário (US), com a lista de casos de uso (diagramas de sequência) na seção 6. O backlog é o conjunto de issues `[US]` do GitHub. A prioridade (Alta, Média ou Baixa) é a do Documento de Visão, mantida por funcionalidade, sem técnica formal de priorização (MoSCoW, WSJF).

| Necessidade (Visão) | Requisitos |
| :--- | :--- |
| Saber onde está o ônibus | RF-06 a RF-09, RF-30 |
| Saber quanto falta | RF-10, RF-11 |
| Chegar de um ponto a outro | RF-12, RF-13, RF-14, RF-29 |
| Acompanhar a viagem | RF-15, RF-16, RF-17 |
| Contribuir com informação de campo | RF-18 a RF-20 |
| Ser avisado de atraso e rotas | RF-22, RF-23, RF-24, RF-28 |
| Acesso seguro | RF-01 a RF-05 |
| Voltar a trajetos frequentes; aprender a usar | RF-21, RF-25, RF-26, RF-27 |

São **30 requisitos funcionais**, todos entregues.

## 3. Especificação dos requisitos funcionais

Responsáveis conforme [`distribuicao_us.md`](distribuicao_us.md). Para as USs criadas depois do plano, o responsável é o autor da issue e o atribuído.

### 3.1 Acesso (autenticação e sessão)

**RF-01 — Criar nova conta** · US #11 · Alta · @brenouchihar
- Como novo passageiro, quero criar uma conta com nome, e-mail e senha, para personalizar minha experiência.
- Aceite: (1) cadastro com todos os campos cria a conta; (2) campo obrigatório ausente é recusado; (3) e-mail já cadastrado é recusado; (4) a senha precisa ter 8 caracteres, maiúscula, número e símbolo, e a tela mostra o medidor; (5) sem aceite dos termos, o cadastro é recusado.
- Notas: não há confirmação de conta por e-mail; a conta entra direto.

**RF-02 — Login com e-mail e senha** · US #10 · Alta · @brenouchihar
- Aceite: (1) credenciais corretas autenticam e levam ao mapa; (2) senha incorreta mostra "Usuário ou senha inválidos"; (3) a sessão persiste por cookies httpOnly.
- Notas: a conta é bloqueada por 15 min após 5 tentativas falhas.

**RF-03 — Login com Google** · US #12 · Média · @davieduardo001
- Aceite: no primeiro acesso via Google a conta é criada e o usuário entra.

**RF-04 — Recuperação de senha** · US #13 e #133 · Média · @brenouchihar
- Aceite: (1) solicitar a redefinição por e-mail; (2) a resposta é a mesma para e-mail existente e inexistente, sem revelar quem tem conta; (3) excesso de tentativas é limitado; (4) token válido redefine a senha; (5) token inválido ou expirado é recusado; (6) confirmação de senha divergente é recusada.
- Notas: o link vale 60 minutos, uso único; o e-mail é enviado por SMTP.

**RF-05 — Ciclo de vida da sessão** · US #31 · Alta · @davieduardo001
- Aceite: (1) recurso protegido com sessão válida responde normalmente; (2) sessão expirada é renovada automaticamente com o refresh token; (3) sessão inválida sem renovação volta ao login; (4) logout encerra a sessão.
- Notas: access token de 1 h e refresh token de 7 dias, em cookies `HttpOnly; Secure; SameSite=None`. O Gateway ignora o `X-User-Id` enviado pelo cliente.

### 3.2 Mapa, linha e rastreamento

**RF-06 — Mapa com localização atual** · US #14 · Alta · @Kelvin963
- Aceite: (1) com permissão, o mapa centra na posição do usuário; (2) com a localização negada, aparece "Não foi possível obter sua localização"; (3) o marcador acompanha a movimentação.

**RF-07 — Buscar linha por número** · US #15 · Alta · @Kelvin963
- Aceite: (1) a busca devolve a linha com nome, sentido e itinerário; (2) linha inexistente mostra erro; (3) a resposta vem em tempo adequado. A busca aceita também nome ou destino (autocomplete).

**RF-08 — Rastrear a posição do ônibus em tempo real** · US #16 · Alta · @Kelvin963
- Aceite: (1) ícones dos ônibus sobre o trajeto; (2) atualização automática sem recarregar; (3) sem veículo em operação, aviso e próxima saída prevista do terminal.
- Notas: posição lida ao vivo da SEMOB com cache de 20 s, nunca guardada.

**RF-09 — Trajeto e paradas da linha** · US #17 · Alta · @davieduardo001
- Aceite: (1) trajeto desenhado pela malha viária; (2) paradas marcadas, com nome ao tocar; (3) seta indica o sentido de operação.

**RF-10 — Detalhes de uma parada** · US #18 e #174 · Média · @louisassis
- Aceite: (1) painel com nome, código, linhas e próximas saídas; (2) parada sem horários mostra mensagem; (3) fechar o painel volta ao mapa.
- Notas: a seção "Chegando nesta parada" fica oculta durante uma viagem, em erro ou com lista vazia.

**RF-11 — Tempo estimado de chegada (ETA)** · US #19, #159 e #173 · Alta · @louisassis (#19), @Vitoria-Albuquerque (#159), @davieduardo001 (#173)
- Aceite: (1) ETA calculado pela posição do veículo; (2) atualizado sem recarregar; (3) sem dado, mostra "Sem previsão no momento"; (4) ETA exibido no marcador do ônibus; (5) marcador sem ETA calculável fica sem número.
- Notas: todo tempo exibido declara a origem (ao vivo ou previsto); o ETA é medido até a parada física, no sentido dela.

**RF-12 — Calcular rota de origem a destino por ônibus** · US #20 e #159 · Alta · @louisassis
- Aceite: (1) rota simples; (2) rota com baldeação e ponto de troca; (3) nenhuma rota: mensagem; (4) destino por endereço ou ponto de referência (geocodificação).

**RF-13 — Buscar parada por nome ou endereço** · US #21 · Média · @louisassis
- Aceite: (1) busca por nome com resultado; (2) busca por endereço mostra as paradas num raio de 500 m; (3) sem resultado, mensagem orientando a tentar outro nome, bairro ou ponto de referência.

**RF-14 — Paradas de subir e descer na rota, com o tempo do ônibus** · US #190 · Média · @davieduardo001
- Aceite: (1) só as paradas de embarque e desembarque de cada trecho em destaque; (2) tempo do ônibus na parada de embarque, com a origem; (3) tempo até a parada de desembarque; (4) sem ônibus, horário previsto ou "Sem previsão no momento"; (5) baldeação mostra as paradas de cada trecho; (6) "Peguei este ônibus" no trecho já define o destino; (7) ponto sem parada cadastrada aparece como "Parada sem nome"; (8) "chega na sua parada em N min" no popup do ônibus.

**RF-29 — Planejar a viagem por horário de partida ou chegada** · US #115 · Média · @davieduardo001
- Aceite: (1) "sair às X" mostra as opções com o horário de cada trecho; (2) "chegar até X" calcula o horário de saída necessário; (3) a baldeação mostra o tempo de espera no ponto de troca; (4) usa a tabela do dia da semana escolhido; (5) sem viagem possível, explica o motivo (sem linha para o trajeto, sem tabela de horários ou fora do horário de operação), em vez de uma lista vazia.
- Notas: parte das opções do RF-12; o horário de passagem em cada parada é **estimado** (saída do terminal pela tabela da SEMOB mais o tempo de percurso, proporcional ao ponto do trajeto) e a tela avisa isso; feriados não são considerados; espera acima de 3 h não conta como viagem.

**RF-30 — Posição colaborativa do ônibus (fallback do GPS oficial)** · US #199 · Alta · @ngualbertolopes
- Aceite: (1) ao pegar o ônibus, a pessoa pode aceitar compartilhar a posição do ônibus; o compartilhamento vem **desligado**, separado do aceite dos Termos; (2) com o ônibus fora do GPS da SEMOB, a posição informada entra no mapa e no ETA com o selo "colaborativo"; (3) "Parar" revoga a qualquer momento e apaga a leitura na hora; "Cheguei" também encerra o compartilhamento; (4) leituras fora do traçado da linha, com salto de velocidade impossível ou enviadas com menos de 10 s de intervalo são recusadas; (5) quando o ônibus volta ao feed da SEMOB, a posição oficial vale.
- Notas: nenhuma coordenada vai para o banco; cada leitura vive só na memória do servidor, por no máximo 2 minutos (RN-024). O banco guarda apenas o instante e a versão do texto aceito.

### 3.3 Viagem e alertas de proximidade

**RF-15 — Pegar o ônibus (embarcar, acompanhar e encerrar a viagem)** · US #171 · Alta · @Kelvin963 (atribuída), entregue por @Vitoria-Albuquerque
- Aceite: (1) "Peguei este ônibus" registra a viagem e ativa o modo "em viagem"; (2) em viagem, mostra o veículo, a próxima parada e as paradas restantes; (3) "Cheguei" encerra; (4) sem veículo identificável, avisa e não registra.
- Notas: uma viagem ativa por usuário; a viagem expira em 4 h; o embarque exige um ônibus da linha por perto, e a posição do usuário só valida o embarque e é descartada.

**RF-16 — Alerta de proximidade da parada (dentro do app)** · US #172 · Alta · @gualbertonathalia, concluída por @davieduardo001
- Aceite: (1) alerta quando o ônibus chega à distância ou tempo configurado; (2) uma única vez por parada e viagem; (3) respeita as preferências (RF-24); (4) sem posição do veículo, não emite alerta impreciso.

**RF-17 — Alerta de proximidade com a tela bloqueada (Web Push)** · US #195 · Alta · @davieduardo001
- Aceite: (1) ativar com consentimento explícito em Configurações; (2) receber com o app fechado, e o toque abre o mapa; (3) não receber duas vezes; (4) respeita as preferências; (5) remover a inscrição; (6) servidor sem chaves de push: controle indisponível, sem erro; (7) no iPhone, exige instalar o app (PWA); (8) permissão negada é explicada.

### 3.4 Colaboração

**RF-18 — Reportar ocorrência em uma linha** · US #23 · Média · @Vitoria-Albuquerque
- Aceite: (1) reporte com sucesso é registrado e exibido; (2) sem autenticação, pede login; (3) limite de **3 reportes por hora** por usuário, com aviso.
- Notas: tipos atraso, não passou, lotação, obra na via, ônibus quebrou, acidente e segurança.

**RF-19 — Ver ocorrências reportadas por outros passageiros** · US #24 · Média · @Vitoria-Albuquerque
- Aceite: (1) ocorrência confirmada exibida; (2) pendente exibida como "Aguardando confirmação"; (3) expirada some da lista.
- Notas: a lista não mostra quem reportou; a validade varia por tipo (RN-014).

**RF-20 — Confirmar ocorrência de outro passageiro** · US #26 · Média · @Vitoria-Albuquerque
- Aceite: (1) confirmação de ocorrência pendente; (2) o autor não confirma a própria; (3) não é possível confirmar após a expiração; (4) cada usuário confirma uma vez; (5) com **3 confirmações** a ocorrência vira "confirmada".

**RF-21 — Salvar e visualizar rota favorita** · US #25 · Média · @Vitoria-Albuquerque
- Aceite: (1) salvar a rota; (2) acesso rápido: "Ir" recalcula com origem e destino preenchidos; (3) remover. Máximo de 20 favoritos por usuário.

### 3.5 Notificações

**RF-22 — Notificações de rotas preferidas** · US #22 · Alta · @gualbertonathalia
- Aceite: (1) notificação de ônibus próximo; (2) com a antecedência configurada; (3) desabilitada respeita a preferência.

**RF-23 — Alerta de atraso na linha acompanhada** · US #27 · Alta · @gualbertonathalia
- Aceite: (1) alerta automático acima do limiar de atraso; (2) atualizado quando o atraso aumenta; (3) cancelado quando o ônibus normaliza.

**RF-24 — Preferências de notificação** · US #29 · Média · @gualbertonathalia
- Aceite: (1) antecedência de 5, 10, 30 ou 60 min; (2) desativar um tipo; (3) desativar todas.

**RF-28 — Alerta de cancelamento de viagem** · US #28 · Alta · @Kelvin963
- Aceite: (1) a linha acompanhada (favoritos e linhas seguidas) sem ônibus no feed 15 minutos depois do horário previsto de saída gera um alerta de cancelamento; (2) o alerta sugere uma linha alternativa quando outra cobre ao menos 70% das paradas do trecho; (3) respeita a preferência de notificação de cancelamento (RF-24); (4) com o feed inteiro da SEMOB vazio, não alerta.
- Notas: detecta o cancelamento pela **ausência** do ônibus; a SEMOB não informa cancelamento operacional, então esse caso não existe. A notificação sai por Web Push (RF-17).

### 3.6 Onboarding e instalação

**RF-25 — Tutorial no primeiro acesso** · US #30 · Média · @Vitoria-Albuquerque
- Aceite: (1) tutorial automático no primeiro acesso; (2) "Pular" não o reabre; (3) rever pelas Configurações.

**RF-26 — Instalar o Movecity na tela inicial (PWA)** · US #136 · Média · @davieduardo001
- Aceite: (1) instalar pelo Android; (2) instalar pelo iPhone; (3) abre no mapa; (4) dado de transporte nunca vem de cache; (5) oscilação de rede não quebra a casca do app; (6) ícone recortado pelo sistema.

**RF-27 — Navegação sem itens mortos** · issue #201 (UX) · Baixa · @davieduardo001
- Aceite: a barra lateral não mostra "Nova Viagem".

## 4. Lista de regras de negócio

| ID | Descrição | Requisitos |
| :--- | :--- | :--- |
| RN-001 | O passageiro está **Aguardando** ou **Em viagem**; só assume "Em viagem" por indicação explícita confirmada no servidor, nunca por suposição | RF-15 |
| RN-002 | Em viagem, o ETA de espera some; mostram-se a próxima parada e as paradas restantes | RF-15 |
| RN-003 | LGPD na viagem: guarda-se o mínimo (usuário, linha, sentido, veículo, parada de destino, horários, e o aceite do compartilhamento quando houver), **sem trilha de posição**; a posição do usuário valida o embarque e é descartada; nenhuma coordenada do usuário vai para o endereço da página | RF-12, RF-15, RF-30 |
| RN-004 | Confirmar o embarque exige veículo **da linha**, com posição recente (até 5 min), a até o raio de embarque do usuário (padrão 100 m); com vários, vale o mais próximo | RF-14, RF-15 |
| RN-005 | Uma viagem ativa por usuário, garantida por índice único no banco | RF-15 |
| RN-006 | Viagem esquecida expira sozinha em 4 h e não gera alerta | RF-15, RF-16 |
| RN-007 | O ETA é medido ao longo do trajeto até a **parada física**, no sentido dela; paradas de lados opostos são diferentes | RF-10, RF-11 |
| RN-008 | Horário previsto nunca mistura dia útil, sábado e domingo | RF-10, RF-11 |
| RN-009 | **Não inventar:** sem posição válida (até 15 min) nem horário confiável, a resposta é "sem previsão" | RF-11, RF-14, RF-16 |
| RN-010 | Todo número de tempo declara a origem: ao vivo, previsto ou saída do terminal; saída do terminal nunca é exibida como "passa aqui" | RF-10, RF-11, RF-14 |
| RN-011 | Ônibus que já passou, de sentido oposto ou com dado velho não entra como "chegando" | RF-11 |
| RN-012 | Posição do ônibus lida ao vivo (cache de 20 s) e nunca guardada | RF-08, RF-11 |
| RN-013 | Limite de **3 reportes por hora** por usuário | RF-18 |
| RN-014 | Validade da ocorrência por tipo: lotação 15 min; atraso, acidente e segurança 30 min; não passou e ônibus quebrou 60 min; obra na via 120 min. Expirada não aparece; o registro não é apagado | RF-19 |
| RN-015 | Ocorrência dos tipos que exigem validação nasce "pendente" e vira "confirmada" com **3 confirmações** de outros usuários; acidente e segurança nascem confirmadas | RF-18, RF-19, RF-20 |
| RN-016 | O autor não confirma a própria ocorrência; um usuário confirma uma vez; ocorrência expirada não é confirmada | RF-20 |
| RN-017 | Máximo de 20 rotas favoritas por usuário | RF-21 |
| RN-018 | Antecedência do alerta: 5, 10, 30 ou 60 min (padrão 30); notificações e alerta de chegada são ativáveis separadamente | RF-16, RF-17, RF-24 |
| RN-019 | O alerta de proximidade dispara uma vez por parada e viagem, respeita as preferências e não dispara sem posição do veículo | RF-16, RF-17 |
| RN-020 | Conta bloqueada por 15 min após 5 tentativas de login falhas | RF-02 |
| RN-021 | Cadastro exige aceite dos termos; a recuperação de senha responde igual para e-mail existente e inexistente | RF-01, RF-04 |
| RN-022 | O servidor ignora o `X-User-Id` enviado pelo cliente; a identidade vem do JWT validado no Gateway | todas as rotas protegidas |
| RN-023 | O compartilhamento da posição do ônibus é **opt-in**, desligado por padrão e separado do aceite dos Termos; exige a versão do texto aceito, que fica guardada como prova; é revogável a qualquer momento ("Parar") e termina com "Cheguei" | RF-30 |
| RN-024 | A posição colaborativa nunca é gravada: cada leitura vale até 2 minutos, só em memória, sem identificador do usuário; o banco guarda apenas o instante do aceite e a versão do texto | RF-30 |
| RN-025 | A posição da SEMOB sempre vence a colaborativa (no empate de ETA também); a colaborativa só entra quando não há ônibus da SEMOB equivalente, e o selo declara a origem | RF-30, RF-11 |
| RN-026 | Leitura colaborativa só é aceita se encaixar no traçado da linha (150 m), sem salto acima da velocidade máxima de ônibus e a cada 10 s no mínimo por viagem | RF-30 |
| RN-027 | No planejamento por horário, cada trecho usa a tabela do dia da semana (nunca mistura dia útil, sábado e domingo); sem opção viável, a resposta diz o motivo | RF-29, RN-008 |
| RN-028 | O cancelamento só é declarado quando a linha está sem ônibus e outras linhas reportam posição no mesmo ciclo; com o feed inteiro vazio, a causa pode ser a fonte, e não se alerta | RF-28, RN-009 |

## 5. Lista de requisitos não funcionais

Classificação ISO/IEC 25010.

| ID | Requisito | Classificação | Situação |
| :--- | :--- | :--- | :--- |
| RNF-01 | Carregamento em até 3 s em conexão 4G | Eficiência de desempenho | Meta; não medida |
| RNF-02 | Disponibilidade de 99% nos horários de pico (5h–9h, 17h–20h) | Confiabilidade | Meta; sem monitoramento de uptime |
| RNF-03 | Proteção de dados de geolocalização (LGPD) | Segurança | Atendida no desenho (RN-003, RN-023, RN-024); sem auditoria formal |
| RNF-04 | Sessão por cookies httpOnly, Secure, SameSite=None; JWT validado no Gateway; rotas públicas restritas | Segurança | Atendido |
| RNF-05 | Validação cruzada do reporte colaborativo (3 confirmações) | Confiabilidade | Atendido (RN-015) |
| RNF-06 | Não inventar dado: sem posição ou horário confiável, mostrar "sem previsão" | Confiabilidade | Atendido (RN-009) |
| RNF-07 | Acessibilidade WCAG 2.2 AA e avaliação por heurísticas de Nielsen | Usabilidade | Contraste das cores calculado e coberto por teste; avaliação de Nielsen feita por um avaliador |
| RNF-08 | Aplicativo web responsivo e instalável (PWA) | Portabilidade | Atendido |
| RNF-09 | Tolerância a falha de integração externa (SEMOB, OSRM, geocodificação, CARTO) | Confiabilidade | Definida no Documento de Arquitetura, seção 10.3 |
| RNF-10 | Manutenibilidade: testes automatizados e CI | Manutenibilidade | 1.792 testes automatizados passando no CI; resultados no Documento de Testes e Implementação |
| RNF-11 | Frescor da posição: feed lido ao vivo com cache de 20 s, ETA atualizado sozinho | Eficiência de desempenho | Atendido |

## 6. Casos de uso

Os diagramas de sequência (PlantUML) ficam em [`docs/diagramas/sequencia/`](diagramas/sequencia/). Os UC10 a UC30, UC115, UC171, UC172, UC173, UC190, UC195 e UC199 usam o número da US como identificador.

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
| UC28 Receber alerta de cancelamento de viagem | #28 / RF-28 | [`UC28`](diagramas/sequencia/UC28-receber-alerta-cancelamento-viagem.puml) |
| UC29 Gerenciar preferências de notificação | #29 / RF-24 | [`UC29`](diagramas/sequencia/UC29-gerenciar-preferencias-notificacao.puml) |
| UC30 Visualizar tutorial no primeiro acesso | #30 / RF-25 | [`UC30`](diagramas/sequencia/UC30-visualizar-tutorial-primeiro-acesso.puml) |
| UC115 Planejar viagem por horário | #115 / RF-29 | [`UC115`](diagramas/sequencia/UC115-planejar-viagem-por-horario.puml) |
| UC171 Pegar o ônibus | #171 / RF-15 | [`UC171`](diagramas/sequencia/UC171-pegar-onibus.puml) |
| UC172 Alerta de proximidade da parada | #172 / RF-16 | [`UC172`](diagramas/sequencia/UC172-alerta-proximidade-parada.puml) |
| UC173 ETA: mapeamento entre paradas | #173 / RF-11 | [`UC173`](diagramas/sequencia/UC173-corrigir-eta-mapeamento-paradas.puml) |
| UC190 Paradas de subir e descer na rota | #190 / RF-14 | [`UC190`](diagramas/sequencia/UC190-paradas-subir-descer-rota-pegar-onibus.puml) |
| UC195 Alerta de proximidade com a tela bloqueada | #195 / RF-17 | [`UC195`](diagramas/sequencia/UC195-alerta-proximidade-tela-bloqueada.puml) |
| UC199 Fallback colaborativo de posição | #199 / RF-30 | [`UC199`](diagramas/sequencia/UC199-fallback-colaborativo.puml) |

Sem diagrama de sequência: #31 (RF-05, descrito em [`gateway-auth-flow.md`](gateway-auth-flow.md)), #133 (RF-04), #136 (RF-26), #159 (RF-12), #174 (RF-10) e #201 (RF-27). A especificação textual de cada caso é o conjunto de cenários BDD de cada US, na seção 3.

## 7. Matriz de rastreabilidade

RF → US → caso de uso. A rastreabilidade completa, com PRs, casos de teste e arquivos de teste automatizado, está na matriz do Documento de Testes e Implementação.

| RF | US | Caso de uso |
| :--- | :--- | :--- |
| RF-01 | #11 | UC11 |
| RF-02 | #10 | UC10 |
| RF-03 | #12 | UC12 |
| RF-04 | #13, #133 | UC13 |
| RF-05 | #31 | — |
| RF-06 | #14 | UC14 |
| RF-07 | #15 | UC15 |
| RF-08 | #16 | UC16 |
| RF-09 | #17 | UC17 |
| RF-10 | #18, #174 | UC18 |
| RF-11 | #19, #159, #173 | UC19, UC173 |
| RF-12 | #20, #159 | UC20 |
| RF-13 | #21 | UC21 |
| RF-14 | #190 | UC190 |
| RF-15 | #171 | UC171 |
| RF-16 | #172 | UC172 |
| RF-17 | #195 | UC195 |
| RF-18 | #23 | UC23 |
| RF-19 | #24 | UC24 |
| RF-20 | #26 | UC26 |
| RF-21 | #25 | UC25 |
| RF-22 | #22 | UC22 |
| RF-23 | #27 | UC27 |
| RF-24 | #29 | UC29 |
| RF-25 | #30 | UC30 |
| RF-26 | #136 | — |
| RF-27 | #201 | — |
| RF-28 | #28 | UC28 |
| RF-29 | #115 | UC115 |
| RF-30 | #199 | UC199 |

## 8. Restrições e premissas

| Restrição ou premissa | Fonte |
| :--- | :--- |
| **Sem PostGIS**: geometrias em colunas JSON; a única junção espacial roda em Python na ingestão | ADR-02 |
| **Dados da SEMOB copiados por ingestão mensal em lote**; os endpoints são públicos, sem documentação nem SLA, e o catálogo pode ficar até um mês desatualizado | ADR-03 |
| **Posição do ônibus lida ao vivo (cache de 20 s) e nunca guardada**; sem histórico de posições | ADR-04 |
| **Sem ambiente de homologação separado**: `homolog` publica na produção da Vercel; os quatro apps do Fly.io e o banco Neon são compartilhados, por custo | ADR-19 |
| **Escala a zero no Fly**: partida a frio na primeira requisição após ociosidade | ADR-12 |
| **Gateway como ponto único de entrada**; cookies `SameSite=None` + `Secure`, porque frontend (Vercel) e Gateway (Fly) são cross-site | ADR-07 |
| **Integrações externas atrás de contrato `typing.Protocol`** (mock e real) | ADR-06 |
| **Posição colaborativa só em memória do processo**: com mais de uma máquina no Fly.io, o fallback pode não aparecer para quem consulta em outra máquina; trocar por armazenamento compartilhado é uma mudança só de implementação | ADR-25 |
| **Horário planejado é estimado** (saída do terminal mais tempo de percurso proporcional); feriados não são considerados | ADR-26 |
| **Web Push** exige chaves VAPID no servidor; no iPhone, só com o app instalado | ADR-16 |
| **Escopo geográfico**: projeto-piloto em Taguatinga e Ceilândia (os dados da SEMOB cobrem o DF inteiro) | Documento de Visão |
| **Sem validação em campo**: raio de embarque, tolerância do ETA e regra "ônibus chegando" não foram medidos com ônibus real | Documento de Testes e Implementação |

## 9. Declaração de uso ético e responsável de inteligência artificial

O projeto adota um fluxo de trabalho com agentes de IA generativa no desenvolvimento e na documentação (metodologia "Agentic Workflow"; regras de operação em `docs/boas-praticas-ia.md`). Todo o código foi gerado por agentes de IA, conduzidos pelos seis integrantes do grupo, que especificaram, revisaram e aprovaram. Este DRS foi levantado a partir de issues, PRs, código e documentos do repositório, com apoio de um assistente de IA. Ferramentas: Claude Code (modelos Claude Sonnet, Opus e Haiku, da Anthropic) e OpenCode (modelos Qwen, DeepSeek e Big Pickle, além dos do Claude). Período: de 15/08 a 30/10/2026.

- **Supervisão humana:** todo conteúdo gerado é revisado por membros do grupo, que permanecem responsáveis pela exatidão e pela conformidade acadêmica. Este documento foi revisado por Davi Eduardo Costa Miranda (orquestrador).
- **Checagem de confiabilidade:** cada afirmação deste DRS aponta para uma fonte verificável (issue, PR, arquivo de código ou documento de testes).
- **Privacidade e sigilo:** nenhum dado de usuário, credencial ou dado pessoal entra neste documento; os casos de teste usam contas de teste.
- **Integridade acadêmica:** a contribuição da ferramenta é declarada aqui, conforme a orientação do template.

## 10. Histórico de revisões

| Versão | Data | Alteração |
| :--- | :--- | :--- |
| 1.0 | 30/10/2026 | Versão entregue, criada a partir das issues `[US]`, dos PRs mergeados, do código de `homolog` e da documentação de testes |
| 1.1 | 31/10/2026 | Inclusão de RF-28 (alerta de cancelamento, #28), RF-29 (planejamento por horário, #115) e RF-30 (posição colaborativa, #199), com RN-023 a RN-028 |
