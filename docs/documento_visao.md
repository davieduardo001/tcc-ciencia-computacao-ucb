# Documento de Visão - Movecity

## 1. Introdução
O presente documento formaliza a visão estratégica do projeto **Movecity**, desenvolvido como Trabalho de Conclusão de Curso. O objetivo é apresentar a viabilidade técnica e social desta solução a possíveis stakeholders, sendo estes gestores públicos, empresas de transporte que operam no Distrito Federal ou investidores. O projeto é conduzido pelo grupo Segurança no Transporte, integrado pelos acadêmicos: Breno Santana Silva, Davi Eduardo Costa Miranda, Kelvin Rodrigues de Sousa, Luis Fernando Monteiro de Assis Lourenço, Nathalia Gualberto Lopes e Vitória Cordeiro Albuquerque.

O Movecity será um novo software, desenvolvido como um aplicativo web. Diferente de soluções globais, o Movecity nasce com foco regionalizado, operando inicialmente como um projeto-piloto em uma cidade satélite estratégica do Distrito Federal. A escolha por regiões de alta densidade demográfica, como Ceilândia e Taguatinga — identificadas pela Pesquisa Distrital por Amostra de Domicílios (IPEDF, 2022) como áreas de grande concentração populacional e intensa demanda por transporte público —, é fundamental para a validação da solução em um cenário de alta complexidade. A motivação do projeto é mitigar as falhas críticas de comunicação do sistema de transporte local, promovendo segurança e previsibilidade para o passageiro brasiliense por meio de uma plataforma colaborativa e transparente.

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
| Funcionalidade | Descrição | Prioridade |
| :--- | :--- | :--- |
| Consultar Horários/GPS | Rastreamento em tempo real da linha | Alta |
| Notificações de Atraso | Alertas baseados em rotas preferidas | Alta |
| Reporte Colaborativo | Usuário informa problemas na linha (estilo Waze) | Média |
| Mapa em Tempo Real | Visualização do ônibus e paradas | Alta |
| Autenticação | Login via Google ou E-mail/Senha | Alta |

### 5.2 Arquitetura Técnica

| Camada | Tecnologia | Justificativa |
| :--- | :--- | :--- |
| **Frontend** | Next.js (React) | SSR/SSG, App Router, deploy na Vercel ou Fly.io |
| **Mapa/GPS** | Leaflet JS + OpenStreetMap | Gratuito, open source, alta customização, sem risco de custo em produção |
| **Backend** | FastAPI (Python) + Fly.io | Framework assíncrono, alta performance, documentação automática via OpenAPI, deploy via Docker |
| **Banco de Dados** | PostgreSQL (Neon) | Serverless, free tier generoso, suporte a dados geoespaciais via PostGIS |
| **CI/CD** | GitHub Actions | Integração nativa com o repositório, pipelines de teste e deploy automatizados |
| **Fonte GPS** | API do GDF (SEMOB) | Dados oficiais das frotas do STPC/DF em formato GeoJSON |

**Fluxo de dados:**
1. API do GDF fornece posições GPS dos ônibus em tempo real.
2. Backend consolida dados oficiais com reportes dos usuários.
3. Frontend renderiza as informações no mapa via Leaflet JS.
4. Reportes colaborativos são validados por cruzamento (mínimo 2 reportes para confirmação).

### 5.3 Requisitos não funcionais preliminares
| Requisito | Descrição | Prioridade |
| :--- | :--- | :--- |
| **Desempenho** | Carregamento em até 3s em conexões 4G | Alta |
| **Disponibilidade** | 99% nos horários de pico (5h-9h, 17h-20h) | Alta |
| **LGPD** | Proteção rigorosa de dados de geolocalização | Alta |
| **Validação Cruzada** | Alerta colaborativo precisa de >1 reporte para ser confirmado | Média |

## 6. Referências
- IPEDF (2022). Pesquisa Distrital por Amostra de Domicílios.
- CGDF (2026). Painel de Ouvidoria do Distrito Federal.
- CAROLI, P. (2018). Lean Inception.
