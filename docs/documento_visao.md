# Documento de Visão - Movecity

## 1. Introdução
O presente documento formaliza a visão estratégica do projeto **Movecity**, desenvolvido como Trabalho de Conclusão de Curso. O objetivo é apresentar a viabilidade técnica e social desta solução a possíveis stakeholders, sendo estes gestores públicos, empresas de transporte que operam no Distrito Federal ou investidores. O projeto é conduzido pelo grupo Segurança no Transporte, integrado pelos acadêmicos: Breno Santana Silva, Davi Eduardo Costa Miranda, Kelvin Rodrigues de Sousa, Luis Fernando Monteiro de Assis Lourenço, Nathalia Gualberto Lopes e Vitória Cordeiro Albuquerque.

O Movecity é um novo software, desenvolvido como um aplicativo web. O cliente é acadêmico: não há cliente externo contratante nem fins lucrativos. Diferente de soluções globais, o Movecity nasce com foco regionalizado, operando como projeto-piloto em duas cidades satélites do Distrito Federal. A escolha de regiões de alta densidade demográfica, como Ceilândia e Taguatinga — identificadas pela Pesquisa Distrital por Amostra de Domicílios (IPEDF, 2022) como áreas de grande concentração populacional e intensa demanda por transporte público —, é fundamental para a validação da solução em um cenário de alta complexidade. A motivação do projeto é mitigar as falhas críticas de comunicação do sistema de transporte local, promovendo segurança e previsibilidade para o passageiro brasiliense por meio de uma plataforma colaborativa e transparente.

## 2. Contexto de negócio
### 2.1 Cenário Atual do Domínio e Deficiências
O domínio de aplicação deste projeto concentra-se na gestão e consumo de informações sobre a mobilidade urbana no Distrito Federal. O sistema de transporte público do DF é caracterizado por um fluxo pendular intenso, onde milhares de cidadãos se deslocam diariamente das Regiões Administrativas (como Ceilândia e Taguatinga) para o Plano Piloto e outros centros econômicos.

Atualmente, este cenário é marcado por uma profunda assimetria de informação. Embora existam frotas monitoradas, o dado real sobre a localização dos veículos raramente é transmitido de forma fidedigna ao cidadão. As principais lacunas enfrentadas são:
- **O fenômeno do "Ônibus Fantasma":** veículos que constam no sistema oficial mas não realizam o percurso, ou que passam fora do horário previsto sem aviso prévio.
- **Insegurança física e psicológica:** a espera prolongada em paradas de ônibus, muitas vezes em locais isolados e com iluminação precária nas cidades satélites, expõe o usuário a riscos de assaltos e violência.
- **Ineficiência operacional e econômica:** a falta de previsibilidade impede que o usuário otimize seu tempo, impactando sua pontualidade no trabalho e compromissos.

### 2.2 Usuários, Mercado-Alvo e Indicadores de Relevância
O mercado-alvo compreende os usuários dependentes do STPC/DF. O projeto-piloto é em Taguatinga e Ceilândia devido à alta densidade demográfica. Segundo o IPEDF (2022), 33,3% da população do DF utiliza o ônibus como principal meio de transporte.

**Principais usuários:**
- Trabalhadores de turnos críticos.
- Estudantes universitários e de ensino técnico.
- Profissionais corporativos e autônomos.

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
| **Nosso produto** | Entrega maior precisão e foco regional nas cidades satélites |

## 4. Descrição das partes interessadas
| Nome | Descrição | Responsabilidades |
| :--- | :--- | :--- |
| Usuário Trabalhador | Depende do transporte em horários críticos | Reportar ocorrências e validar dados |
| Equipe de Desenvolvimento | Grupo Segurança no Transporte (UCB) | Desenvolver e manter a plataforma |
| Gestores Públicos | SEMOB/GDF | Consumir dados para tomada de decisão |

## 5. Visão geral do produto
### 5.1 Necessidades e funcionalidades
O detalhamento de cada requisito, com critérios de aceite, está no [DRS](drs.md). Responsáveis conforme [`distribuicao_us.md`](distribuicao_us.md).

| Necessidade | Funcionalidade | Prioridade | Responsável |
| :--- | :--- | :--- | :--- |
| Saber onde está o ônibus (combate ao "ônibus fantasma") | Mapa com a localização do usuário, busca de linha por número, trajeto e paradas, posição dos ônibus atualizada sozinha (US #14, #15, #16, #17) | Alta | @Kelvin963 (#14–#16), @davieduardo001 (#17) |
| Saber quanto falta para o ônibus chegar | Tempo estimado de chegada (ETA) no ônibus, na parada e na rota, sempre com a origem do número: ao vivo, previsto ou "sem previsão" (US #19, #159, #173) | Alta | @louisassis (#19), @Vitoria-Albuquerque (#159), @davieduardo001 (#173) |
| Chegar de um ponto a outro | Rota por ônibus com baldeação, paradas de subir e descer, busca de parada por nome ou endereço e detalhes da parada (US #18, #20, #21, #190) | Alta | @louisassis (#18, #20, #21), @davieduardo001 (#190) |
| Acompanhar a viagem e não perder a parada | "Peguei este ônibus", acompanhamento em viagem e alerta de proximidade, dentro do app e por Web Push com a tela bloqueada (US #171, #172, #195) | Alta | @Kelvin963 (#171, entregue por @Vitoria-Albuquerque), @gualbertonathalia (#172, concluída por @davieduardo001), @davieduardo001 (#195) |
| Ser avisado de atraso e das rotas de interesse | Alerta de atraso, notificações de rotas preferidas e preferências de notificação (US #22, #27, #29) | Alta | @gualbertonathalia |
| Contribuir com informação de campo | Reporte de ocorrência, lista de ocorrências e confirmação por outros passageiros, estilo Waze (US #23, #24, #26) | Média | @Vitoria-Albuquerque |
| Voltar rápido a trajetos frequentes | Rota favorita (US #25) | Média | @Vitoria-Albuquerque |
| Acesso seguro e simples | Cadastro, login por e-mail e senha ou Google, recuperação de senha por e-mail e sessão com renovação automática (US #10, #11, #12, #13, #31, #133) | Alta | @brenouchihar (#10, #11, #13, #133), @davieduardo001 (#12, #31) |
| Aprender a usar e ter à mão | Tutorial no primeiro acesso e instalação como aplicativo (PWA) (US #30, #136) | Média | @Vitoria-Albuquerque (#30), @davieduardo001 (#136) |

### 5.2 Arquitetura Técnica

| Camada | Tecnologia | Justificativa |
| :--- | :--- | :--- |
| **Frontend** | Next.js (React), na Vercel | SSR/SSG, App Router, deploy automático a cada push |
| **Mapa/GPS** | Leaflet JS + OpenStreetMap (base CARTO Voyager) | Gratuito, open source e com alta customização |
| **Backend** | FastAPI (Python) no Fly.io, em quatro apps: gateway, auth, mobilidade e colaboração | Framework assíncrono, documentação automática via OpenAPI, deploy via Docker |
| **Banco de Dados** | PostgreSQL (Neon), sem PostGIS | Serverless e free tier generoso. O PostGIS foi avaliado e não adotado: as geometrias ficam em colunas JSON (ver Documento de Arquitetura, ADR-02) |
| **CI/CD** | GitHub Actions | Integração nativa com o repositório; testes e deploy automatizados |
| **Fonte GPS** | API do GDF (SEMOB) | Dados oficiais das frotas do STPC/DF em GeoJSON: catálogo de linhas copiado por ingestão em lote, posição lida ao vivo e nunca guardada |

**Fluxo de dados:**
1. A API do GDF (SEMOB) fornece as posições GPS dos ônibus; o backend as lê ao vivo (cache de 20 s) e não as grava.
2. O backend combina a posição ao vivo com o catálogo de linhas e paradas para calcular ETA, rotas e viagem. Os reportes dos usuários ficam em tabela própria e aparecem na lista de ocorrências; não alteram o ETA nem a posição dos ônibus.
3. O frontend renderiza as informações no mapa via Leaflet JS.
4. Os reportes colaborativos são validados por cruzamento: atraso, não passou, lotação, obra na via e ônibus quebrou ficam "aguardando confirmação" até receberem **3 confirmações de outros passageiros**; acidente e segurança aparecem confirmados de imediato. O autor não confirma o próprio reporte.

### 5.3 Requisitos não funcionais preliminares
| Requisito | Descrição | Prioridade | Situação |
| :--- | :--- | :--- | :--- |
| **Desempenho** | Carregamento em até 3 s em conexões 4G | Alta | Meta; não medida em rede 4G. |
| **Disponibilidade** | 99% nos horários de pico (5h–9h, 17h–20h) | Alta | Meta; sem monitoramento de uptime. |
| **LGPD** | Proteção rigorosa de dados de geolocalização | Alta | A posição do usuário não é guardada: a viagem não tem coluna de posição e a posição enviada no embarque é descartada; nenhuma coordenada do usuário vai para o endereço das páginas. Sem auditoria formal. |
| **Validação cruzada** | Reporte colaborativo precisa de confirmação de outros passageiros | Média | Implementada com 3 confirmações (o planejamento inicial previa 2). |

### 5.4 Restrições e premissas
- **Sem PostGIS e sem histórico de posições:** busca por raio no servidor ou análise retrospectiva exigiriam reavaliar essas decisões.
- **Dados da SEMOB** por ingestão mensal em lote e posição ao vivo; os endpoints são públicos, sem documentação nem SLA.
- **Sem ambiente de homologação separado**, por custo: a `homolog` publica na produção da Vercel, e backend e banco são compartilhados.
- **Plataforma:** aplicativo web instalável (PWA); no iPhone, o aviso com a tela bloqueada exige instalar o app na tela inicial.
- **Ajuda ao usuário:** o tutorial do primeiro acesso é o único material de uso dentro do app.

## 6. Escopo entregue
Estão entregues todas as funcionalidades da tabela 5.1: acesso, mapa e rastreamento, ETA, rotas, parada, viagem, ocorrências, rota favorita, tutorial, alertas e instalação como PWA. Além do planejado no início, o produto ganhou "pegar o ônibus" (#171), alerta de proximidade (#172) por Web Push (#195), paradas de subir e descer na rota (#190), ETA pela parada física (#173), PWA (#136) e e-mail de recuperação de senha (#237).

Não foi feita validação em campo: o raio de embarque, a tolerância do ETA e a regra "ônibus chegando" não foram medidos com um ônibus real. O texto dos Termos de Uso e da Política de Privacidade (#32) ainda precisa ser publicado numa tela do aplicativo; hoje o cadastro exige apenas o aceite. Os resultados dos testes estão no Documento de Testes e Implementação.

## 7. Referências
- IPEDF (2022). Pesquisa Distrital por Amostra de Domicílios.
- CGDF (2026). Painel de Ouvidoria do Distrito Federal.
- CAROLI, P. (2018). Lean Inception.

## 8. Histórico de revisões
| Versão | Data | Alteração |
| :--- | :--- | :--- |
| 1.0 | 30/10/2026 | Versão entregue, refletindo o produto implementado |
