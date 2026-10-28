# Documento de Visão - Movecity

## 1. Introdução
O presente documento formaliza a visão estratégica do projeto **Movecity**, desenvolvido como Trabalho de Conclusão de Curso. O objetivo é apresentar a viabilidade técnica e social desta solução a possíveis stakeholders, sendo estes gestores públicos, empresas de transporte que operam no Distrito Federal ou investidores. O projeto é conduzido pelo grupo Segurança no Transporte, integrado pelos acadêmicos: Breno Santana Silva, Davi Eduardo Costa Miranda, Kelvin Rodrigues de Sousa, Luis Fernando Monteiro de Assis Lourenço, Nathalia Gualberto Lopes e Vitória Cordeiro Albuquerque.

O Movecity é um novo software, desenvolvido como um aplicativo web (versão do projeto-piloto em produção em 28/10/2026; o cliente é acadêmico, sem cliente externo contratante e sem fins lucrativos). Diferente de soluções globais, o Movecity nasce com foco regionalizado, operando inicialmente como um projeto-piloto em uma cidade satélite estratégica do Distrito Federal. A escolha por regiões de alta densidade demográfica, como Ceilândia e Taguatinga — identificadas pela Pesquisa Distrital por Amostra de Domicílios (IPEDF, 2022) como áreas de grande concentração populacional e intensa demanda por transporte público —, é fundamental para a validação da solução em um cenário de alta complexidade. A motivação do projeto é mitigar as falhas críticas de comunicação do sistema de transporte local, promovendo segurança e previsibilidade para o passageiro brasiliense por meio de uma plataforma colaborativa e transparente.

## 2. Contexto de negócio
### 2.1 Cenário Atual do Domínio e Deficiências
O domínio de aplicação deste projeto concentra-se na gestão e consumo de informações sobre a mobilidade urbana no Distrito Federal. O sistema de transporte público do DF é caracterizado por um fluxo pendular intenso, onde milhares de cidadãos se deslocam diariamente das Regiões Administrativas (como Ceilândia e Taguatinga) para o Plano Piloto e outros centros econômicos.

Atualmente, este cenário é marcado por uma profunda assimetria de informação. Embora existam frotas monitoradas, o dado real sobre a localização dos veículos raramente é transmitido de forma fidedigna ao cidadão. As principais lacunas enfrentadas são:
- **O fenômeno do "Ônibus Fantasma":** Veículos que constam no sistema oficial mas não realizam o percurso, ou que passam fora do horário previsto sem aviso prévio.
- **Insegurança Física e Psicológica:** A espera prolongada em paradas de ônibus, muitas vezes em locais isolados e com iluminação precária nas cidades-satélites, expõe o usuário a riscos de assaltos e violência.
- **Ineficiência Operacional e Econômica:** A falta de previsibilidade impede que o usuário otimize seu tempo, impactando sua pontualidade no trabalho e compromissos.

### 2.2 Usuários, Mercado-Alvo e Indicadores de Relevância
O mercado-alvo compreende os usuários dependentes do STPC/DF. O projeto-piloto será em Taguatinga e Ceilândia devido à alta densidade demográfica. Segundo o IPEDF (2022), 33,3% da população do DF utiliza o ônibus como principal meio de transporte.

**Principais usuários:**
- Trabalhadores de Turnos Críticos.
- Estudantes Universitários e de Ensino Técnico.
- Profissionais Corporativos e Autônomos.

### 2.3 Benchmarking
| Ferramenta | Pontos Fortes | Limitações | Oportunidade Movecity |
| :--- | :--- | :--- | :--- |
| **DF no Ponto** | Dados diretos do GDF. | Baixa usabilidade e bugs. | UX superior e validação ágil. |
| **Moovit/Maps** | Grande alcance. | Dependência de feeds lentos. | Precisão regional cirúrgica. |
| **Redes Sociais** | Colaboração real. | Informação desorganizada. | Colaboração georreferenciada. |

## 3. Posicionamento
### 3.1 Declaração do problema
| O problema de | A ausência de informações confiáveis e em tempo real sobre o transporte público no DF |
| :--- | :--- |
| **afeta** | Trabalhadores e estudantes de Ceilândia e Taguatinga |
| **cujo impacto é** | Insegurança física, perda de produtividade e ansiedade |
| **uma solução de sucesso deveria** | Fornecer rastreamento real, alertas de atrasos e permitir reportes colaborativos |

### 3.2 Declaração da visão do software
| Para | Usuários do transporte público do DF |
| :--- | :--- |
| **Que** | Necessitam de informações precisas para planejar deslocamentos com segurança |
| **O** | Movecity |
| **É um** | Aplicativo web de mobilidade urbana colaborativa |
| **Que** | Combina dados de GPS com informações colaborativas dos passageiros |
| **Diferente de** | DF no Ponto, Moovit e Google Maps |
| **Nosso produto** | Entrega maior precisão e foco regional nas cidades-satélite |

## 4. Descrição das partes interessadas
| Nome | Descrição | Responsabilidades |
| :--- | :--- | :--- |
| Usuário Trabalhador | Depende do transporte em horários críticos | Reportar ocorrências e validar dados |
| Equipe de Desenvolvimento | Grupo Segurança no Transporte (UCB) | Desenvolver e manter a plataforma |
| Gestores Públicos | SEMOB/GDF | Consumir dados para tomada de decisão |

## 5. Visão geral do produto
### 5.1 Necessidades e funcionalidades
Estado em 28/10/2026. "Entregue" significa mergeado em `homolog` ou `main` (a `homolog` é publicada em produção; ver seção 6). Responsável conforme [`distribuicao_us.md`](distribuicao_us.md); "a confirmar" onde a distribuição não cobre a US. O detalhamento de cada requisito, com critérios de aceite e PRs, está no [DRS](drs.md).

| Necessidade | Funcionalidade | Prioridade | Responsável | Estado |
| :--- | :--- | :--- | :--- | :--- |
| Saber onde está o ônibus (combate ao "ônibus fantasma") | Mapa com localização do usuário, busca de linha por número, trajeto e paradas, posição dos ônibus atualizada sozinha (US #14, #15, #16, #17) | Alta | @Kelvin963 (#14–#16), @davieduardo001 (#17) | Entregue |
| Saber quanto falta para o ônibus chegar | Tempo estimado de chegada (ETA) no ônibus, na parada e na rota, sempre com a origem do número: ao vivo, previsto ou "sem previsão" (US #19, #159, #173) | Alta | @louisassis (#19); #159 e #173 a confirmar | Entregue |
| Chegar de um ponto a outro | Rota por ônibus com baldeação, paradas de subir e descer, busca de parada por nome ou endereço e detalhes da parada (US #20, #21, #18, #190) | Alta | @louisassis (#18, #20, #21); #190 a confirmar | Entregue |
| Acompanhar a viagem e não perder a parada | "Peguei este ônibus", acompanhamento em viagem e alerta de proximidade, dentro do app e por Web Push com a tela bloqueada (US #171, #172, #195) | Alta | a confirmar | Entregue |
| Ser avisado de atraso e das rotas de interesse | Alerta de atraso (US #27), notificações de rotas preferidas (US #22) e preferências de notificação (US #29) | Alta | @gualbertonathalia | Parcial: sem entrega ao usuário (seção 6) |
| Contribuir com informação de campo | Reporte de ocorrência, lista de ocorrências e confirmação por outros passageiros, estilo Waze (US #23, #24, #26) | Média | @Vitoria-Albuquerque | Entregue |
| Voltar rápido a trajetos frequentes | Rota favorita (US #25) | Média | @Vitoria-Albuquerque | Entregue |
| Acesso seguro e simples | Cadastro, login por e-mail e senha ou Google, recuperação de senha por e-mail e sessão com renovação automática (US #10, #11, #12, #13, #133, #31) | Alta | @brenouchihar (#10, #11, #13), @davieduardo001 (#12, #31); #133 a confirmar | Entregue |
| Aprender a usar e ter à mão | Tutorial no primeiro acesso (US #30) e instalação como PWA (US #136) | Média | @Vitoria-Albuquerque (#30); #136 a confirmar | Entregue |

### 5.2 Arquitetura Técnica

| Camada | Tecnologia | Justificativa |
| :--- | :--- | :--- |
| **Frontend** | Next.js (React) | SSR/SSG, App Router; deploy na Vercel (a branch `homolog` publica na produção da Vercel) |
| **Mapa/GPS** | Leaflet JS + OpenStreetMap (base CARTO Voyager, com recuo para o tile padrão do OSM sem a chave) | Gratuito, open source, alta customização; ADR-11 |
| **Backend** | FastAPI (Python) + Fly.io, em quatro apps (gateway, auth, mobilidade, colaboracao) | Framework assíncrono, documentação automática via OpenAPI, deploy via Docker |
| **Banco de Dados** | PostgreSQL (Neon), **sem PostGIS** | Serverless, free tier generoso. O PostGIS foi avaliado e **não adotado**: geometrias ficam em colunas JSON e a única junção espacial roda em Python na ingestão (ADR-02 de [`documento_arquitetura.md`](documento_arquitetura.md)) |
| **CI/CD** | GitHub Actions | Integração nativa com o repositório, pipelines de teste e deploy automatizados |
| **Fonte GPS** | API do GDF (SEMOB) | Dados oficiais das frotas do STPC/DF em GeoJSON. O catálogo de linhas é copiado para o banco por ingestão em lote (ADR-03); a posição é lida ao vivo, com cache de 20 s, e nunca persistida (ADR-04) |

**Fluxo de dados:**
1. A API do GDF (SEMOB) fornece as posições GPS dos ônibus; o backend lê o feed ao vivo (cache de 20 s) e não grava posições.
2. O backend combina a posição ao vivo com o catálogo de linhas e paradas ingerido do SEMOB para calcular ETA, rotas e viagem. Os reportes dos usuários ficam em tabela própria e são exibidos na lista de ocorrências; **não alteram** o ETA nem a posição dos ônibus.
3. O frontend renderiza as informações no mapa via Leaflet JS.
4. Reportes colaborativos são validados por cruzamento: os tipos "atraso", "não passou", "lotação", "obra na via" e "ônibus quebrou" nascem como "aguardando confirmação" e viram "confirmados" com **3 confirmações de outros passageiros** (`Ocorrencia.LIMITE_CONFIRMACOES`, em `src/backend/colaboracao/models/ocorrencia.py`); "acidente" e "segurança" aparecem como confirmados de imediato. O autor não confirma o próprio reporte.

### 5.3 Requisitos não funcionais preliminares
| Requisito | Descrição | Prioridade | Situação em 28/10/2026 |
| :--- | :--- | :--- | :--- |
| **Desempenho** | Carregamento em até 3s em conexões 4G | Alta | **Não medido.** Nenhum teste de carga ou de tempo de carregamento em 4G foi executado (nem em `docs/qa/`). A [ADR-12](documento_arquitetura.md) registra que as máquinas do Fly operam com escala a zero (`min_machines_running = 0`, confirmado nos `fly.toml` de gateway e mobilidade), e a partida a frio conflita com a meta de 3 s |
| **Disponibilidade** | 99% nos horários de pico (5h-9h, 17h-20h) | Alta | **Não medida.** Não há monitoramento de disponibilidade nem medição de uptime; a escala a zero (ADR-12) e o uso de free tier tornam a meta não garantida. Houve quedas em produção por falha de deploy (defeito 1 do [relatório de defeitos](qa/relatorio-cobertura-e-defeitos.md)) |
| **LGPD** | Proteção rigorosa de dados de geolocalização | Alta | **Parcialmente verificada.** A posição dos ônibus não é persistida (ADR-04); a viagem não tem coluna de posição do usuário e a posição enviada no embarque é descartada (ADR-15). O CT-SEG-03 foi **aprovado** em produção (a resposta de `GET /viagens/ativa` não traz coordenada do usuário). Um defeito foi achado e corrigido: o "Ir" do planejador colocava as coordenadas do usuário na URL (#231, PR #239, validado em produção). Não houve auditoria formal de conformidade com a LGPD, e o texto dos Termos de Uso e da Política de Privacidade (#32) não está publicado em uma tela do aplicativo: a confirmar |
| **Validação cruzada** | Reporte colaborativo precisa de confirmação de outros passageiros | Média | **Verificada no código, com valor diferente do planejado.** A regra implementada exige **3 confirmações** (`LIMITE_CONFIRMACOES = 3`), e não 2; "acidente" e "segurança" aparecem confirmados de imediato. A confirmação pela tela (#26, PR #209) entrou em `homolog` em 27/10 e **não foi exercida nos 49 casos manuais** (o caso CT-COL-04 verificou os selos "Aguardando confirmação" e "Confirmada"; a transição por 3 confirmações tem teste automatizado, não execução em produção: a confirmar) |

### 5.4 Restrições e premissas

Conforme o template, as restrições tecnológicas e premissas que, se mudarem, alteram este documento:
- **Sem PostGIS** e **sem histórico de posições** (ADR-02 e ADR-04): qualquer busca por raio em tempo de requisição ou análise retrospectiva exige reavaliar essas decisões.
- **Dados da SEMOB** por ingestão mensal em lote (workflow `ingestao-semob.yml`) e posição ao vivo; os endpoints são públicos, sem documentação nem SLA publicados (ADR-03).
- **Sem ambiente de homologação separado**, por custo: a `homolog` publica na produção da Vercel, e o backend e o banco são compartilhados (`docs/deploy-plan.md`, issue #42).
- **Raio de embarque configurável** (`RAIO_EMBARQUE_M`, padrão 100 m). Em produção está em 100 km por decisão de 28/10/2026, só para demonstrar o "Peguei este ônibus" na defesa (`docs/guia-apresentacao.md`).
- **Plataforma:** aplicativo web (PWA instalável); o aviso com a tela bloqueada no iPhone exige instalar o app na tela inicial (#195).
- **Documentação do usuário:** não há manual do usuário nem ajuda online; o tutorial no primeiro acesso (#30) é o único material de uso dentro do app.

## 6. Escopo entregue e trabalho futuro

Levantado em 28/10/2026 a partir das issues, dos PRs mergeados e do código de `origin/homolog`.

### 6.1 Entregue

Todas as User Stories de acesso, mapa, rastreamento, ETA, rotas, parada, viagem, ocorrências, rota favorita e tutorial (lista com PRs no [DRS](drs.md), seção 2). Além do planejado no início: "pegar o ônibus" (#171), alerta de proximidade (#172) e sua entrega por Web Push (#195), paradas de subir e descer na rota (#190), ETA pela parada física (#173), PWA (#136) e e-mail de recuperação de senha por SMTP (#237). Os 49 casos manuais foram executados em produção ([resumo executivo de QA](qa/resumo-executivo.md)).

### 6.2 Não entregue (trabalho futuro)

| Item | Issue | Estado verificado | O que existe hoje |
| :--- | :--- | :--- | :--- |
| Notificações push dos alertas de atraso e das rotas preferidas | #207 | Aberta | O canal Web Push existe só para o alerta de proximidade (#195). O alerta de atraso (#27) roda no worker com `FornecedorGTFSMock` e `NotificadorNulo` (`mobilidade/main.py`, comentário "O alerta de atraso (#27) não passa por aqui") e não chega ao usuário; o CT-NOT-02 ficou "não verificável" |
| Alerta de cancelamento de viagem | #28 | Aberta | Só existe o interruptor "alerta de cancelamento" nas preferências (#29); não há detecção nem envio |
| Motor de planejamento por horário (GTFS + RAPTOR) | #115 | Aberta | A rota é calculada por linhas e posição ao vivo, sem horário de partida ou chegada |
| Horários de operação da linha | #118 | Aberta | O painel da parada mostra as saídas do terminal por linha e dia (#174); o quadro completo de horários da linha não foi entregue |
| Fallback colaborativo da posição do ônibus | #199 | Aberta | Sem código no serviço de mobilidade; o ETA depende do GPS da SEMOB |
| Validação em campo | — | Não feita | Raio de embarque, tolerância do ETA e a regra "ônibus chegando" (#191) não foram medidos em campo; CT-VIA-07 e CT-VIA-08 só se provam em campo |
| Ambiente de homologação separado | #42 | Não feito | Decisão de custo registrada |
| Testes de desempenho e disponibilidade | — | Não feitos | Ver seção 5.3 |
| Alerta de ocorrência ativa no trecho da rota (cenário 4 da #20) | #20 | Não localizado no código de `mobilidade`: a confirmar | — |

## 7. Referências
- IPEDF (2022). Pesquisa Distrital por Amostra de Domicílios.
- CGDF (2026). Painel de Ouvidoria do Distrito Federal.
- CAROLI, P. (2018). Lean Inception.

## 8. Histórico de revisões
| Versão | Data | Alteração |
| :--- | :--- | :--- |
| 1.0 | — | Versão original do Documento de Visão. Data não registrada neste arquivo: a confirmar |
| 1.1 | 28/10/2026 | Revisão para refletir o produto entregue: remoção do PostGIS (ADR-02); regra de validação cruzada corrigida para 3 confirmações; stack e fluxo de dados atualizados; tabela de funcionalidades com responsável e estado; requisitos não funcionais com a situação de verificação; restrições e premissas; escopo entregue e trabalho futuro |
