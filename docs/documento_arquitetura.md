# Documento de Arquitetura de Software — Movecity

**Grupo:** Segurança no Transporte  
**Software:** Movecity  
**Versão:** 2.0

---

## Histórico da Revisão

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 12/jun/26 | 1.0 | Versão inicial do documento | Grupo Segurança no Transporte |
| 18/set/26 | 2.0 | Atualização pós-implementação: correção das seções divergentes do código (persistência, processos, implementação, implantação e dados) e inclusão da seção 10 — Evolução Arquitetural | Grupo Segurança no Transporte |

---

## Índice Analítico

1. [Introdução](#1-introdução)
   - 1.1 [Finalidade](#11-finalidade)
   - 1.2 [Escopo](#12-escopo)
   - 1.3 [Definições, Acrônimos e Abreviações](#13-definições-acrônimos-e-abreviações)
2. [Restrições e Requisitos Arquiteturais](#2-restrições-e-requisitos-arquiteturais)
3. [Visão de Casos de Uso](#3-visão-de-casos-de-uso)
4. [Visão Lógica](#4-visão-lógica)
   - 4.1 [Representação do Domínio da Aplicação](#41-representação-do-domínio-da-aplicação)
   - 4.2 [Decisões Arquiteturais](#42-decisões-arquiteturais)
   - 4.3 [Representação da Arquitetura Lógica](#43-representação-da-arquitetura-lógica)
   - 4.4 [Representação do Funcionamento da Arquitetura](#44-representação-do-funcionamento-da-arquitetura)
5. [Visão de Processos](#5-visão-de-processos)
6. [Visão da Implementação](#6-visão-da-implementação)
7. [Visão de Implantação](#7-visão-de-implantação)
8. [Visão de Dados](#8-visão-de-dados)
9. [Volume e Desempenho](#9-volume-e-desempenho)
10. [Evolução Arquitetural — Sprint 1](#10-evolução-arquitetural--sprint-1-junho-a-setembro-de-2026)
11. [Referências](#11-referências)

---

## 1. Introdução

A introdução deste Documento de Arquitetura de Software apresenta uma visão geral da estrutura e das decisões técnicas adotadas no desenvolvimento do Movecity. Está organizada conforme o modelo "4+1" de Philippe Kruchten (1994), que descreve a arquitetura de software por meio de cinco visões complementares: Lógica, de Processos, de Implementação, de Implantação e de Casos de Uso. Este modelo permite que diferentes públicos — analistas, desenvolvedores, operadores e stakeholders — compreendam o sistema a partir de perspectivas distintas e complementares.

### 1.1 Finalidade

Este documento oferece uma visão geral arquitetural abrangente do sistema Movecity, usando diversas visões arquiteturais para representar diferentes aspectos do sistema. O objetivo é capturar e comunicar as decisões arquiteturais significativas tomadas pelo Grupo Segurança no Transporte durante a especificação do projeto. O público-alvo inclui os desenvolvedores do grupo, o orientador acadêmico e avaliadores da UCB. O documento adota a estrutura "4+1" de Kruchten (1994) como referencial metodológico.

### 1.2 Escopo

O Movecity é um aplicativo web de mobilidade urbana colaborativa voltado para o Distrito Federal, com projeto-piloto nas cidades-satélite de Ceilândia e Taguatinga. A plataforma combina dados GPS oficiais da frota do STPC/DF (via API da SEMOB/GDF) com reportes colaborativos dos próprios passageiros para mitigar o fenômeno do "ônibus fantasma" e reduzir a insegurança nas paradas de ônibus. Este documento descreve a arquitetura de software que suporta essas funcionalidades.

### 1.3 Definições, Acrônimos e Abreviações

| Termo | Definição |
|---|---|
| **DF** | Distrito Federal |
| **STPC/DF** | Sistema de Transporte Público Coletivo do Distrito Federal |
| **SEMOB** | Secretaria de Mobilidade do GDF |
| **GDF** | Governo do Distrito Federal |
| **API** | Application Programming Interface — interface de comunicação entre sistemas |
| **GPS** | Global Positioning System — sistema de posicionamento global |
| **GeoJSON** | Formato de dados geoespaciais baseado em JSON |
| **SSR** | Server-Side Rendering — renderização do lado do servidor |
| **SSG** | Static Site Generation — geração de site estático |
| **JWT** | JSON Web Token — padrão de autenticação stateless |
| **ORM** | Object-Relational Mapper — mapeador objeto-relacional |
| **CI/CD** | Continuous Integration / Continuous Delivery — integração e entrega contínua |
| **LGPD** | Lei Geral de Proteção de Dados (Lei nº 13.709/2018) |
| **PostGIS** | Extensão geoespacial para PostgreSQL. Avaliada na v1.0 e **não adotada** — ver seção 10 |
| **OSRM** | Open Source Routing Machine — serviço de roteamento sobre a malha viária do OpenStreetMap |
| **CARTO** | Provedor de tiles de mapa usado como base visual do Leaflet |
| **ETA** | Estimated Time of Arrival — tempo estimado de chegada |
| **ADR** | Architecture Decision Record — registro de decisão arquitetural |
| **UC** | Caso de Uso (Use Case) |
| **US** | User Story — história de usuário |
| **MVC** | Model-View-Controller — padrão arquitetural |
| **UCB** | Universidade Católica de Brasília |
| **TCC** | Trabalho de Conclusão de Curso |

---

## 2. Restrições e Requisitos Arquiteturais

Esta seção descreve os requisitos de negócio e de usuário com impacto sobre os atributos de qualidade da arquitetura, bem como as restrições do projeto. Os atributos de qualidade estão em conformidade com a norma NBR ISO/IEC 25010.

| Atributo de Qualidade | Requisito de Arquitetura | Solução |
|---|---|---|
| **Desempenho** | O carregamento inicial do mapa e das posições dos ônibus deve ocorrer em no máximo 3 segundos em conexões 4G. | Uso de SSR/SSG no Next.js para reduzir o tempo de interação inicial; tiles do OpenStreetMap carregados de forma lazy; posições de GPS lidas ao vivo da origem com cache em memória de 20 segundos compartilhado entre todos os usuários (ver seção 5). |
| **Interoperabilidade** | O sistema deve consumir dados GPS no formato GeoJSON provido pela API oficial da SEMOB/GDF sem necessidade de transformação proprietária. | Backend FastAPI com módulo de ingestão de GeoJSON; endpoints RESTful padronizados com documentação automática via OpenAPI 3.0. |
| **Usabilidade** | A interface deve ser responsiva e acessível para usuários com diferentes níveis de letramento digital, priorizando dispositivos móveis. | Interface construída com Next.js (App Router), componentes acessíveis e design mobile-first; componente de mapa via Leaflet JS com interação por toque. |
| **Confiabilidade** | Reportes colaborativos só devem ser confirmados quando validados por múltiplos usuários independentes. | Lógica de validação cruzada no backend: mínimo de 2 reportes independentes para confirmação de uma ocorrência; mecanismo anti-spam por sessão autenticada. |
| **Segurança** | Dados de geolocalização dos usuários devem ser tratados em conformidade com a LGPD. Sessões autenticadas devem ser gerenciadas de forma segura. | Autenticação stateless via JWT; API Gateway valida tokens localmente sem round-trip ao serviço de autenticação; dados de localização do usuário não são armazenados; HTTPS obrigatório em todos os endpoints. |
| **Facilidade de manutenção** | O código deve ser modular e permitir a adição de novas cidades-satélite sem reestruturação arquitetural. | Separação de responsabilidades por camadas (frontend, gateway, serviços de domínio, dados); serviços independentes e desacoplados; cobertura por testes automatizados via GitHub Actions. |
| **Portabilidade** | O backend deve ser implantável em diferentes provedores de nuvem sem dependência de serviços proprietários. | Deploy via Docker/Fly.io; banco de dados PostgreSQL padrão (Neon serverless); nenhuma dependência de SDKs de nuvem proprietários no código da aplicação. |
| **Escalabilidade** | O sistema deve suportar crescimento de usuários sem redesenho arquitetural, especialmente em horários de pico do transporte público (5h–9h e 17h–20h). | Arquitetura orientada a microserviços com API Gateway; banco PostgreSQL serverless no Neon escala automaticamente; Fly.io suporta auto-scaling horizontal; frontend estático pode ser distribuído via CDN. |
| **Disponibilidade** | O sistema deve ter disponibilidade mínima de 99% nos horários de pico definidos. | Deploy no Fly.io com múltiplas regiões; health checks automáticos; banco Neon com failover gerenciado; monitoramento via GitHub Actions e alertas. |

*Tabela 1 – Restrições e requisitos arquiteturais*

---

## 3. Visão de Casos de Uso

O Movecity foi especificado por meio de histórias de usuário (User Stories), organizadas por épicos funcionais. Cada item está vinculado à sua respectiva issue no GitHub, onde os comentários contêm os artefatos completos de especificação: protótipos de tela (Figma), diagramas de sequência UML e critérios de aceite BDD.

**Épico: Autenticação e Conta**
- [#11 — Criar Nova Conta de Usuário](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/11)
- [#10 — Realizar Login com E-mail e Senha](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/10)
- [#12 — Login via Provedor Social (Google)](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/12)
- [#13 — Recuperação de Senha (Esqueci minha senha)](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/13)
- [#31 — Gerenciar Ciclo de Vida da Sessão (logout e renovação de token)](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/31)

**Épico: Exploração do Mapa**
- [#14 — Visualizar Mapa com Localização Atual](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/14)
- [#15 — Buscar Linha por Número](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/15)
- [#16 — Rastrear Posição do Ônibus em Tempo Real](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/16)
- [#17 — Visualizar Trajeto e Paradas da Linha no Mapa](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/17)
- [#18 — Ver Detalhes de uma Parada](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/18)
- [#19 — Ver Tempo Estimado de Chegada do Ônibus até Minha Parada](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/19)
- [#20 — Calcular Rota de Origem até Destino por Ônibus](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/20)
- [#21 — Buscar Parada por Nome ou Endereço](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/21)

**Épico: Colaboração e Reportes**
- [#22 — Receber Notificações de Rotas Preferidas](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/22)
- [#23 — Reportar Ocorrência em uma Linha](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/23)
- [#24 — Visualizar Ocorrências Reportadas por Outros Passageiros](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/24)
- [#25 — Salvar Rota Favorita](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/25)
- [#26 — Confirmar Ocorrência Reportada por Outro Passageiro](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/26)
- [#27 — Receber Alerta de Atraso na Linha Acompanhada](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/27)
- [#28 — Receber Alerta de Cancelamento de Viagem](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/28)
- [#29 — Gerenciar Preferências de Notificação](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/29)

**Épico: Onboarding**
- [#30 — Visualizar Tutorial no Primeiro Acesso](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/30)

---

## 4. Visão Lógica

Esta seção descreve os componentes significativos da arquitetura do Movecity, sua organização em camadas e pacotes, as principais classes do domínio e as decisões técnicas que definem o design do sistema.

### 4.1 Representação do Domínio da Aplicação

O diagrama de classes da UML é uma representação estática da estrutura do sistema, mostrando as entidades do domínio, seus atributos, operações e os relacionamentos entre elas. Para o Movecity, o diagrama de classes representa as principais entidades de negócio e como elas se relacionam para sustentar as funcionalidades da plataforma.

**Principais entidades do domínio:**

> **[Anexar imagem]** Diagrama de classes UML do domínio do Movecity — entidades: `Usuario`, `Sessao`, `LinhaNibus`, `Parada`, `RotaFavorita`, `Ocorrencia`, `PosicaoOnibus`.
> Rascunho ASCII disponível em `docs/diagramas/rascunhos-ascii.md` (Figura 1).

*Figura 1 — Diagrama de classes simplificado do domínio do Movecity*

### 4.2 Decisões Arquiteturais

Esta subseção documenta as principais decisões técnicas tomadas para o Movecity, com suas justificativas.

| Item Arquitetural | Decisão | Justificativa |
|---|---|---|
| **Estilo arquitetural** | Microserviços com API Gateway (padrão Gateway API) | Permite escalabilidade independente por serviço, isolamento de falhas e evolução incremental da plataforma sem redesenho total. |
| **Linguagem — Frontend** | TypeScript (v5.x) | Tipagem estática reduz erros em tempo de desenvolvimento; suporte nativo no Next.js e vasto ecossistema. |
| **Framework — Frontend** | Next.js 14 (React 18, App Router) | Suporte a SSR e SSG melhora desempenho e SEO; roteamento baseado em arquivos simplifica a estrutura; deploy na Vercel ou Fly.io. |
| **Linguagem — Backend** | Python 3.12 | Equipe familiarizada com a linguagem; ecossistema maduro para o tratamento dos dados geoespaciais da SEMOB. Na prática, a junção espacial foi implementada com a biblioteca padrão (sem Shapely), o que manteve a imagem Docker enxuta. |
| **Framework — Backend** | FastAPI (v0.110+) | Framework assíncrono de alto desempenho; documentação automática via OpenAPI 3.0; validação com Pydantic. |
| **Componente de mapa** | Leaflet JS (v1.9) com base CARTO Voyager e recuo automático para o tile padrão do OpenStreetMap | Leaflet é gratuito, open source e suporta GeoJSON nativamente. A base do CARTO tem contraste mais baixo que o tile padrão do OSM, deixando legível o que importa na tela (linha, parada, veículo); passou a exigir chave, que é gratuita (5 milhões de tiles/mês). Sem a chave configurada, o app recua para o tile padrão do OSM — nenhuma tela quebra por falta de credencial. |
| **Formas de persistência** | Banco relacional para o domínio; cache em memória de processo para o feed de posições; cache em tabela para o catálogo de linhas | Três naturezas de dado, três estratégias: entidades do domínio são relacionais; posição de GPS muda a cada poucos segundos e não vale persistir (cache em memória, TTL de 20 s); dados de linha são estáticos e caros de obter (cache na tabela `linha`, populado em lote). |
| **Banco de dados** | PostgreSQL (Neon serverless), **sem PostGIS** | Free tier generoso e escalabilidade automática. A extensão PostGIS foi avaliada na v1.0 e não adotada: as consultas geoespaciais do produto se resumem a uma junção por proximidade entre traçado e abrigos de parada, resolvida em Python com índice de grade na ingestão (seção 10, ADR-02). Geometrias são guardadas em colunas `JSON`. |
| **Serviços de terceiros** | SEMOB/GDF (`dados.semob.df.gov.br`): `/espaciais`, `/horario`, `/pontos` e `/posicao`; OSRM; Google Routes API; CARTO Basemaps; Google OAuth 2.0 | Dados oficiais das frotas e da rede, sem chave e sem billing — são os mesmos endpoints que alimentam o app oficial "DF no Ponto". OSRM ajusta o traçado à malha viária real. Google OAuth reduz o atrito no cadastro. |
| **Integração com fontes externas** | Padrão *provider*: contrato declarado como `typing.Protocol` em `providers/contratos.py`, com implementação mock e implementação real | Permite desenvolver e testar sem rede e sem cota de API, e trocar a fonte em um único ponto (o service), sem reescrever rota HTTP nem regra de negócio. Foi o que permitiu sair do mock para os dados reais do SEMOB sem tocar no `LinhaService`. |
| **Dependências** | Um `requirements.txt` por serviço, além do combinado na raiz | Cada imagem Docker instala apenas o que o serviço usa, reduzindo o tamanho da imagem. Ver a armadilha correspondente na seção 10 (ADR-08). |
| **Deploy — Backend** | Fly.io — **quatro aplicações independentes** (`movecity-gateway`, `movecity-auth`, `movecity-mobilidade`, `movecity-colaboracao`), cada uma com seu `Dockerfile` e `fly.toml` | Deploy simples via Dockerfile e escala independente por serviço. Separar as aplicações mantém a promessa de isolamento de falhas do estilo de microserviços: a queda de um serviço não derruba os demais. |
| **Deploy — Frontend** | Vercel | Integração nativa com Next.js e deploy automático por push. `homolog` publica em `--prod` no domínio público da Vercel, usado como ambiente de homologação e para as demonstrações. |
| **CI/CD** | GitHub Actions | Integração nativa com o repositório; pipelines de teste e deploy automatizados sem custo adicional. |
| **Autenticação** | JWT (stateless) + httpOnly cookies | Tokens em cookies httpOnly protegem contra XSS; Gateway valida localmente sem round-trip; refresh token permite renovação transparente. |

*Tabela 2 – Decisões arquiteturais*

### 4.3 Representação da Arquitetura Lógica

O diagrama de pacotes da UML representa a organização lógica do sistema em camadas e seus relacionamentos de dependência. O Movecity segue uma arquitetura de microserviços com API Gateway, organizada nas seguintes camadas:

> **[Anexar imagem]** Diagrama de pacotes UML da arquitetura lógica — camadas: Apresentação (Next.js), API Gateway, Serviços de domínio (Autenticação, Mobilidade, Colaboração) e Dados (PostgreSQL + API SEMOB/GDF).
> Rascunho ASCII disponível em `docs/diagramas/rascunhos-ascii.md` (Figura 2).

*Figura 2 — Diagrama de pacotes da arquitetura lógica do Movecity*

**Descrição das camadas:**

- **Camada de Apresentação (`<<interface usuario>>`):** Responsável pela interface com o usuário. Implementada em Next.js (React 18, App Router). Contém as páginas, componentes reutilizáveis e o módulo de mapa (Leaflet JS + OpenStreetMap). Não contém lógica de negócio — comunica-se exclusivamente com o API Gateway.

- **API Gateway (`<<servico gateway>>`):** Ponto único de entrada para todas as requisições do frontend. Responsável por rotear chamadas aos microserviços corretos, validar tokens JWT localmente (sem round-trip ao serviço de autenticação) e gerenciar o ciclo de sessão (renovação transparente de tokens expirados).

- **Serviço de Autenticação (`<<servico autenticacao>>`):** Gerencia o ciclo de vida de usuários e sessões. Emite e valida credenciais; suporta login por e-mail/senha e OAuth 2.0 (Google).

- **Serviço de Mobilidade (`<<servico mobilidade>>`):** Núcleo funcional da plataforma. Lê as posições de GPS do feed da SEMOB, mantém o catálogo de linhas, paradas e trajetos, e calcula rotas de origem a destino (com baldeação) apoiado no OSRM.

- **Serviço de Colaboração (`<<servico colaboracao>>`):** Gerencia o fluxo de reportes colaborativos, validação cruzada, rotas favoritas, notificações e alertas.

- **Camada de Dados (`<<modelo>>`):** PostgreSQL (Neon) para dados persistentes — usuários, sessões, catálogo de linhas, rotas e preferências — e a API externa da SEMOB/GDF para as posições de GPS, lidas ao vivo e nunca persistidas.

### 4.4 Representação do Funcionamento da Arquitetura

O diagrama de sequência da UML descreve a colaboração temporal entre os objetos do sistema para um determinado cenário. Ele é fundamental para que os desenvolvedores compreendam como as camadas da arquitetura interagem em tempo de execução, especialmente o papel do API Gateway na validação de sessão e no roteamento de requisições.

O cenário escolhido é o **rastreamento de posição de ônibus em tempo real (UC16)** com token JWT válido, pois demonstra o fluxo completo entre todas as camadas da arquitetura:

> **[Anexar imagem]** Diagrama de sequência UML — UC16: Rastrear Posição do Ônibus em Tempo Real.
> Arquivo fonte: `docs/diagramas/sequencia/UC16-rastrear-posicao-onibus-tempo-real.puml`

*Figura 3 — Diagrama de sequência: UC16 – Rastrear posição do ônibus em tempo real*

> Os diagramas de sequência completos para todos os casos de uso (UC14–UC30) estão disponíveis em `docs/diagramas/sequencia/` no formato PlantUML.

---

## 5. Visão de Processos

O Movecity separa o tratamento dos dados externos segundo a **frequência com que eles mudam**. Dado estático entra em lote e fica no banco; dado volátil é lido ao vivo e nunca é persistido. Essa distinção define os quatro processos descritos a seguir.

**1. Ingestão em lote do catálogo de linhas (fora do ciclo de requisição).** Um job agendado no GitHub Actions (`.github/workflows/ingestao-semob.yml`) baixa os conjuntos `/espaciais` (1.408 trajetos), `/horario` e `/pontos` (7.140 abrigos de parada) da SEMOB — cerca de 37 MB — e popula a tabela `linha`. O job roda mensalmente (todo dia 1º, às 4h UTC) e sob demanda via `workflow_dispatch`.

A ingestão faz a **junção espacial** entre o traçado de cada linha e os abrigos de parada, associando o abrigo à linha quando está a até 40 metros do eixo da via. Para evitar a comparação de todos os traçados contra todos os abrigos, é construído um índice de grade em memória (células de ~55 m); a busca examina apenas as 9 células vizinhas de cada ponto.

> O processamento roda no CI, e não no deploy nem em uma *thread* do FastAPI, por três motivos: são minutos de execução que não devem repetir-se a cada deploy; dado de linha é estático e não justifica polling; e manter isso fora do contêiner evita que o serviço precise de memória para um pico que ocorre uma vez por mês.

**2. Leitura ao vivo das posições da frota (dentro do ciclo de requisição).** O endpoint `/posicao` da SEMOB devolve a frota inteira do DF (~3.500 veículos) em uma única resposta, sem aceitar filtro por linha. O `posicao_service` baixa o feed completo, mantém-no em **cache de processo por 20 segundos** e filtra a linha pedida em memória. Como o cache é do feed inteiro, um download atende simultaneamente todos os usuários e todas as linhas.

Posições com mais de 15 minutos são descartadas como desatualizadas — um veículo em garagem mantém a última posição registrada por dias. **Nenhuma posição é gravada no banco:** o dado perde validade antes de qualquer consulta posterior justificar o custo de escrita.

**3. Cache sob demanda do detalhe de linha.** Quando o usuário busca uma linha ainda não cacheada (ou cujo registro está velho), o `LinhaService` consulta o `LinhaProvider` configurado e grava o resultado na tabela `linha`, com `atualizado_em` definindo quando o registro deve ser renovado. Buscas seguintes da mesma linha são servidas do banco, sem tocar a fonte externa.

**4. Ciclo de monitoramento de rotas preferidas (serviço de colaboração).** O `monitoring_worker` percorre os favoritos ativos com notificação habilitada, consulta o ETA e dispara a notificação quando os limiares configurados pelo usuário são cruzados, com deduplicação para não repetir o mesmo aviso. O worker **não contém lógica de agendamento** — expõe apenas `executar_ciclo()`, e suas dependências (`FavoritosProvider`, `ETAService`, `PushSender`, `Deduplicador`) chegam por injeção. O agendamento fica em `main.py`, o que mantém o ciclo testável sem relógio, sem rede e sem banco.

**Processo de atendimento a requisições.** Cada serviço executa um servidor FastAPI assíncrono (`asyncio`), atendendo requisições sem bloqueio de I/O. A comunicação entre os serviços é sempre HTTP, via Gateway; não há chamadas diretas entre serviços de domínio nem fila de mensagens.

---

## 6. Visão da Implementação

O código-fonte do Movecity está organizado nos seguintes módulos principais:

**Frontend (`/src/frontend/`):**
- `app/` — Páginas, layouts e componentes de tela (Next.js App Router). Cada rota concentra seus próprios componentes: `app/mapa/` reúne `AppShell`, `MapaInterativo` e `PlanejadorViagem`.
- `app/globals.css` — Fundação visual: *design tokens* da identidade, tipografia e estilos de base compartilhados por todas as telas.
- `lib/` — Cliente HTTP do Gateway (`api.ts`) e tipos compartilhados.
- `public/` — Assets estáticos (logotipo e ícone).
- `__tests__/` — Testes de componente (Jest + Testing Library), colocados ao lado do código que testam.

**Backend (`/src/backend/`):** cada serviço é um pacote autocontido e segue a mesma anatomia interna — `main.py` (aplicação FastAPI), `routes.py` (endpoints), `schemas.py` (contratos Pydantic), `models/` (entidades SQLAlchemy), `providers/` (integrações externas por trás de um `Protocol`) e `tests/`.

- `gateway/` — API Gateway: `middleware.py`, `jwt_validator.py`, `dependencies.py`, `proxy.py`, `cookies.py`, `config.py`, `routes.py`.
- `auth/` — Autenticação: `security.py` (hash e JWT), `google_auth.py` (OAuth 2.0), `email_service.py` (recuperação de senha) e os modelos `Usuario`, `Sessao` e `TokenResetSenha`.
- `mobilidade/` — Mobilidade: `linha_service.py`, `rota_service.py`, `posicao_service.py`, `geocode_service.py`, `semob_source.py`, `ingestao_semob.py` e os providers `linha_mock`, `linha_google_maps`, `osrm_router` e `polyline_decoder`.
- `colaboracao/` — Colaboração: `monitoring_worker.py`, `eta_service.py`, `push_service.py`, `deduplicador.py` e os providers `eta_mock` e `favoritos_mock`.
- `shared/` — Configuração (`config.py`) e sessão de banco (`database.py`) compartilhadas entre os serviços.
- `models/base.py` — `Base` declarativa do SQLAlchemy, comum a todos os modelos.
- `alembic/` — Migrations versionadas; um único encadeamento para todo o banco, mesmo com os serviços separados.

> **Nota de estrutura:** não existe pacote `core/`, e o pacote `models/` da raiz contém apenas a `Base` declarativa — os modelos de cada domínio vivem dentro do próprio serviço. A v1.0 deste documento antecipava uma estrutura que a implementação não seguiu.

---

## 7. Visão de Implantação

O Movecity é implantado em infraestrutura de nuvem, com cada componente em seu ambiente adequado:

> **[Anexar imagem]** Diagrama de implantação UML — nós: CDN/Vercel Edge (frontend), Fly.io (backend FastAPI + API Gateway + serviços), Neon PostgreSQL e API externa SEMOB/GDF.
> Rascunho ASCII disponível em `docs/diagramas/rascunhos-ascii.md` (Figura 4).

*Figura 4 — Diagrama de implantação do Movecity*

**Nós físicos/lógicos:**

| Nó | O que executa | Observações |
|---|---|---|
| **Vercel** | Frontend Next.js, distribuído por CDN global | Publicado em `movecity-frontend.vercel.app`. O deploy dispara no push para `homolog`, em modo `--prod`: nesta fase, `homolog` **é** o ambiente público, usado para homologação e demonstrações. `main` ainda não tem domínio próprio de frontend. |
| **Fly.io — `movecity-gateway`** | API Gateway (FastAPI) | Região primária `gru` (São Paulo). Único serviço que o navegador acessa diretamente. |
| **Fly.io — `movecity-auth`** | Serviço de autenticação | Acessa o banco. Recebe `GOOGLE_CLIENT_ID` como secret no deploy. |
| **Fly.io — `movecity-mobilidade`** | Serviço de mobilidade | Acessa o banco e as APIs externas (SEMOB, OSRM). |
| **Fly.io — `movecity-colaboracao`** | Serviço de colaboração | Acessa o banco. |
| **Neon (PaaS gerenciado)** | PostgreSQL serverless | Instância única compartilhada pelos serviços; escala automaticamente e faz backup diário. Sem PostGIS. |
| **SEMOB/GDF, OSRM, CARTO, Google** | Serviços externos | Não gerenciados pelo Movecity. Cada um tem uma degradação prevista quando indisponível (seção 10). |

*Tabela 3 – Nós de implantação*

**Pipeline de implantação (GitHub Actions):**

```
push em homolog ou main (src/backend/**)
        │
        ▼
   [migrate]  alembic upgrade head   ← roda uma vez, antes de tudo
        │
        ├──► [deploy-auth]         ──► smoke test GET /health
        ├──► [deploy-mobilidade]   ──► smoke test GET /health   (em paralelo)
        └──► [deploy-colaboracao]  ──► smoke test GET /health
        
   [deploy-gateway] ──► smoke test GET /health   (independente: não usa banco)

push em homolog (src/frontend/**)
        │
        ▼
   [deploy-homolog]  vercel build --prod  →  vercel deploy --prod
```

Cada `deploy-*` tem seu próprio grupo de concorrência, com `cancel-in-progress: false`: dois merges seguidos enfileiram, em vez de um cancelar o deploy do outro pela metade. O **smoke test** consulta `GET /health` do serviço recém-publicado por até 10 tentativas com 5 segundos de intervalo, e falha o job se nenhuma retornar 200 — um contêiner que sobe e morre no boot reprova o deploy em vez de passar despercebido.

**Escala a zero.** As máquinas do Fly estão configuradas com `auto_stop_machines = true` e `min_machines_running = 0`: sem tráfego, o serviço desliga. Isso mantém o custo do projeto-piloto próximo de zero, ao preço de uma latência de partida a frio na primeira requisição após um período ocioso — aceitável em avaliação acadêmica, mas incompatível com a meta de 3 segundos da seção 2 se o produto for a público. A mitigação (manter uma máquina viva por serviço) é uma mudança de configuração, não de arquitetura.

**Outros fluxos automatizados:**

| Workflow | Gatilho | Função |
|---|---|---|
| `ci.yml` | Todo PR e push | Testes de backend (pytest), de frontend (Jest) e lint — incluindo a validação do título do PR como Conventional Commit. |
| `ingestao-semob.yml` | Mensal (dia 1º, 4h UTC) e manual | Baixa os dados da SEMOB e popula a tabela `linha`, conferindo ao final que vieram centenas de linhas. |

---

## 8. Visão de Dados

O Movecity persiste dados estruturados no PostgreSQL. A seguir, a descrição das entidades principais e seus relacionamentos.

**Minimundo:** Um `Usuario` pode ter várias `Sessao` ativas, um conjunto de `PreferenciaNotificacao` e múltiplas `RotaFavorita`. Cada `RotaFavorita` referencia uma `Linha`. Uma `Linha` guarda o próprio trajeto e a lista ordenada de paradas. Um `Usuario` autenticado pode criar `Ocorrencia` vinculada a uma `Linha`, e outros usuários podem confirmá-la, incrementando seu contador de confirmações — regra da validação cruzada (mínimo de dois reportes independentes).

**Tabelas implementadas:**

| Tabela | Conteúdo | Origem |
|---|---|---|
| `usuarios` | Conta do usuário: nome, e-mail, hash de senha, `provider`, `google_id`, `avatar_url` | US #10–13, #92 |
| `sessoes` | Sessões emitidas, para revogação e renovação de token | US #10, #31 |
| `tokens_reset_senha` | Tokens de uso único para recuperação de senha | US #13 |
| `linha` | Catálogo de linhas: número, nome, sentido, `paradas`, `trajeto` e `horarios_previstos` | US #15, #17 |
| `rota` / `rota_celula` | Rotas calculadas e o índice de grade que acelera a busca por proximidade | US #20 |
| `preferencias_notificacao` | Antecedência do aviso e chaves de ativação por tipo de alerta | US #29 |

*Tabela 4 – Tabelas persistidas*

**Entidades ainda não persistidas:** `Ocorrencia`, `RotaFavorita` e `Parada` fazem parte do modelo conceitual, mas ainda não têm tabela — as USs correspondentes (#23–26) não foram implementadas, e as paradas vivem hoje como documento JSON dentro de `linha`. `PosicaoOnibus` **não será persistida por decisão de projeto**: a posição é lida ao vivo e descartada (seção 5, processo 2).

**Representação de geometria.** Trajetos e paradas são armazenados em colunas `JSON` — `list[[lat, lng]]` para o traçado e `list[{nome, lat, lng}]` para as paradas —, e não em tipos geoespaciais. O consumidor desses dados é o Leaflet no navegador, que recebe coordenadas em JSON de qualquer forma; guardá-las no formato final evita conversão a cada leitura. A única operação genuinamente espacial do sistema — associar abrigos de parada ao traçado de uma linha — ocorre uma vez por mês, na ingestão, e é resolvida em Python com índice de grade (seção 10, ADR-02).

**Modelo Entidade-Relacionamento (MER):**

> **[Anexar imagem]** MER do Movecity — entidades: `USUARIO`, `SESSAO`, `ROTA_FAVORITA`, `OCORRENCIA`, `LINHA_ONIBUS`, `PARADA`, `POSICAO_ONIBUS`.
> Rascunho textual disponível em `docs/diagramas/rascunhos-ascii.md` (seção MER).

> As coordenadas seguem o sistema de referência WGS84 (o mesmo do GeoJSON da SEMOB/GDF e do Leaflet), porém guardadas como pares numéricos em colunas `JSON`, sem tipo geoespacial nem índice espacial no banco.

---

## 9. Volume e Desempenho

Estimativas de dimensionamento para o projeto-piloto em Ceilândia e Taguatinga:

| Métrica | Valor Estimado |
|---|---|
| **Usuários cadastrados (fase piloto)** | 5.000 |
| **Usuários simultâneos (média)** | 500 |
| **Pico de usuários simultâneos** (horários de pico) | 1.500 |
| **Requisições por segundo** (pico) | 150 req/s |
| **Frequência de atualização GPS** | Leitura ao vivo, com cache de 20 s compartilhado |
| **Linhas no catálogo** (ingestão SEMOB) | 923 linhas / 1.408 trajetos |
| **Abrigos de parada no catálogo** | 7.140 |
| **Volume do catálogo de linhas** | ~37 MB baixados por ingestão |
| **Retenção de posições GPS** | Não persistidas (cache em memória, 20 s) |
| **Retenção de ocorrências** | 30 dias |
| **Backup** | Diário (gerenciado pelo Neon) |
| **Disponibilidade mínima** | 99% nos horários de pico (5h–9h e 17h–20h) |
| **Tempo de carregamento inicial** | ≤ 3 segundos em conexão 4G |

> **Ressalva sobre as estimativas de volume.** Os números de crescimento de dados desta tabela foram projetados na v1.0 supondo um histórico de posições de GPS em banco. Com a ADR-04 (posição lida ao vivo e não persistida), o crescimento real do banco é governado pelo catálogo de linhas — estático — e pelas tabelas de usuário, o que o torna substancialmente menor que o projetado. As metas de desempenho e disponibilidade seguem válidas, com a ressalva da ADR-12 sobre partida a frio.

---

## 10. Evolução Arquitetural — Sprint 1 (junho a setembro de 2026)

Esta seção registra as decisões arquiteturais tomadas **durante a implementação**, entre a versão 1.0 deste documento (12/jun/26) e o fechamento da sprint. Cada registro segue o formato ADR (*Architecture Decision Record*): a decisão, o que a motivou e a consequência assumida. Onde a decisão contraria a v1.0, isso está dito explicitamente.

### 10.1 Registro de decisões

| ID | Decisão | Motivação | Consequência assumida |
|---|---|---|---|
| **ADR-01** | O Gateway alcança os serviços pelas **URLs públicas HTTPS** (`movecity-*.fly.dev`), e não pela rede privada `.internal` do Fly.io. | A rede privada do Fly é IPv6-only. Para usá-la, os serviços precisariam de bind dual-stack, o que causou instabilidade com o proxy público do próprio Fly. | Os serviços ficam expostos publicamente. O risco é contido: fora do que passa pelo Gateway, eles só expõem `/health` e `/hello`, sem dado sensível. Se o projeto crescer, a separação de rede volta à pauta. |
| **ADR-02** | **PostGIS não foi adotado.** Geometrias ficam em colunas `JSON`; a única junção espacial é resolvida em Python com índice de grade (células de ~55 m, raio de busca de 40 m). | O produto tem uma só operação espacial de verdade — associar abrigos de parada ao traçado da linha — e ela roda uma vez por mês, na ingestão. Adotar PostGIS acrescentaria uma extensão, um tipo de coluna e um vocabulário de consulta para atender a um caso único e offline. | **Contraria a v1.0**, que previa PostGIS em várias seções. Se surgir busca por raio em tempo de requisição (ex.: "paradas perto de mim" no servidor), a decisão deve ser reavaliada — hoje esse cálculo acontece no navegador. |
| **ADR-03** | Os dados da SEMOB são **copiados para o banco** por ingestão em lote, em vez de consultados a cada busca. | Os endpoints não aceitam filtro: devolvem sempre o payload inteiro (~37 MB somados). Consultar por usuário seria inviável. Além disso, são endpoints públicos sem documentação nem SLA publicados. | Se a SEMOB sair do ar, a busca continua funcionando com o último snapshot. Em troca, o catálogo pode ficar até um mês desatualizado — aceitável para dado que muda raramente. |
| **ADR-04** | Posições de GPS são **lidas ao vivo com cache de 20 s e nunca persistidas**. | O feed traz a frota inteira do DF em uma resposta só; um download serve todos os usuários simultaneamente. Posição perde validade em segundos. | **Contraria a v1.0**, que previa persistir posições a cada 30 s com retenção de 24 h. Não há histórico de posições — se análises retrospectivas entrarem no escopo, será preciso um processo de arquivamento à parte. |
| **ADR-05** | O traçado exibido no mapa passa pelo **OSRM**, e não pela linha reta entre paradas. | A geometria bruta ligava paradas em linha reta, atravessando quadras. O OSRM ajusta o traçado à malha viária real do OpenStreetMap. | Mais uma dependência externa no caminho do usuário. O trajeto é cacheado junto com a linha, então a chamada não se repete a cada visualização. |
| **ADR-06** | Integrações externas ficam atrás de um **contrato `typing.Protocol`**, com implementação mock e implementação real. | Permite desenvolver e testar sem rede e sem cota de API, e trocar a fonte em um ponto só. | Foi o que permitiu migrar do mock para os dados reais do SEMOB sem reescrever `LinhaService`, rota HTTP nem teste. Custo: uma camada de indireção a mais em cada integração. |
| **ADR-07** | Cookies de sessão usam **`SameSite=None` com `Secure`**, e não `Lax`/`Strict`. | Frontend (Vercel) e Gateway (Fly) estão em domínios diferentes — é cross-site de fato. Com `Lax`/`Strict`, o navegador não envia o cookie em `fetch()` cross-site, e toda chamada autenticada caía em 401 logo após um login bem-sucedido. | **Corrige a v1.0**, cuja tabela de cookies indicava `Lax`/`Strict`. `SameSite=None` amplia a exposição a CSRF; a mitigação atual é o escopo restrito de `path` por cookie e a obrigatoriedade de HTTPS. Unificar frontend e Gateway sob um mesmo domínio permitiria voltar a `Lax`. |
| **ADR-08** | Cada serviço tem seu **próprio `requirements.txt`**, além do combinado na raiz. | Cada imagem Docker instala só o que o serviço usa, reduzindo o tamanho da imagem e o tempo de build. | Criou uma armadilha real: o CI instala o combinado da raiz, e o contêiner instala o do serviço. Dependência ausente no arquivo do serviço **passa no CI e derruba o contêiner no boot**. Aconteceu duas vezes (PR #102, no mobilidade; PR #127/#128, no colaboração). O smoke test em `/health` no pipeline existe justamente para transformar esse erro em deploy reprovado. |
| **ADR-09** | O `CORSMiddleware` é o **middleware mais externo** da pilha do Gateway. | O Starlette executa primeiro o último middleware adicionado. Com o CORS abaixo do middleware de autenticação, o preflight `OPTIONS` — que nunca carrega cookie — era barrado com 401 antes de o CORS responder. | Todo 401 legítimo passa a chegar ao frontend como 401, e não como "bloqueado por CORS". A ordem virou regra verificada por teste (`test_cors_ordem_middleware.py`). |
| **ADR-10** | As **migrations rodam no pipeline**, em um job único que antecede os deploys dos serviços. | Com quatro serviços e um banco só, deixar cada contêiner migrar no boot causaria corrida entre eles. | Um encadeamento único do Alembic para todo o banco, mesmo com os serviços separados — o que exige atenção ao `down_revision` quando duas USs criam migration em paralelo (aconteceu na US #29). |
| **ADR-11** | A base do mapa é o **CARTO Voyager**, com recuo automático para o tile padrão do OpenStreetMap. | O tile padrão do OSM é denso e saturado, e disputa atenção com o que importa na tela. A base do CARTO tem contraste menor e deixa legíveis linha, parada e veículo. | A CARTO passou a exigir chave. A chave é gratuita (5 milhões de tiles/mês), mas virou uma variável de ambiente a mais. Sem ela, o mapa recua para o OSM e continua funcionando — nenhuma tela quebra por falta de credencial. |
| **ADR-12** | As máquinas do Fly operam com **escala a zero** (`min_machines_running = 0`). | Mantém o custo do projeto-piloto próximo de zero. | Partida a frio na primeira requisição após ociosidade. Conflita com a meta de 3 segundos da seção 2 em um cenário real de produção; a correção é configuração, não arquitetura. |
| **ADR-13** | O proxy do Gateway repassa a **query string** e **não repassa o `Accept-Encoding`** do cliente. | Descartar a query string quebrava toda rota com parâmetro. Repassar o `Accept-Encoding` fazia o serviço de destino devolver corpo comprimido que o proxy entregava sem descomprimir. | O proxy deixou de ser transparente por acidente e passou a ser transparente por contrato, com teste cobrindo os dois comportamentos. |

*Tabela 5 – Registro de decisões arquiteturais da Sprint 1*

### 10.2 Degradação prevista por dependência externa

Uma consequência de somar quatro serviços externos ao caminho do usuário é que a indisponibilidade de cada um precisa ter resposta definida. O quadro abaixo registra o comportamento atual:

| Dependência | Se ficar indisponível | Comportamento do sistema |
|---|---|---|
| SEMOB `/espaciais`, `/horario`, `/pontos` | Ingestão mensal falha | Busca de linha continua servindo o último snapshot do banco. |
| SEMOB `/posicao` | Sem posições ao vivo | O mapa exibe o trajeto e as paradas; o rastreamento informa que não há veículo com posição recente — mesma tela do caso, normal, em que a linha não tem veículo em viagem. |
| OSRM | Sem ajuste à malha viária | O trajeto já cacheado continua sendo exibido; linhas novas ficam sem traçado ajustado. |
| CARTO | Sem base visual do mapa | Recuo automático para o tile padrão do OpenStreetMap. |
| Google OAuth | Sem login social | Login por e-mail e senha permanece disponível. |

*Tabela 6 – Degradação prevista por dependência externa*

### 10.3 Divergências entre a v1.0 e a implementação

Três previsões da v1.0 não se confirmaram, e o registro delas é parte do valor deste documento:

1. **PostGIS e persistência de posições (ADR-02 e ADR-04).** A v1.0 dimensionou o banco para armazenar posições de GPS em tipos geoespaciais, com retenção de 24 horas. A implementação não persiste posição alguma, e a única operação espacial saiu do banco. As estimativas de volume da seção 9 devem ser lidas com essa ressalva: o crescimento projetado de ~2 GB/mês pressupunha um histórico de posições que não existe.
2. **Estrutura de pacotes do backend (seção 6).** A v1.0 previa `models/` e `core/` centralizados. A implementação organizou modelos e configuração por serviço, com apenas a `Base` declarativa e a configuração compartilhada na raiz — coerente com o isolamento pretendido pelo estilo de microserviços.
3. **Ingestão como thread do FastAPI (seção 5).** A v1.0 previa um worker assíncrono dentro do backend. A ingestão foi para o CI, e o único worker que restou no backend — o de monitoramento de rotas preferidas — deliberadamente não tem agendador próprio.

---

## 11. Referências

CAROLI, Paulo. **Lean Inception: como alinhar pessoas e construir o produto certo**. São Paulo: Caroli.org, 2018.

GDF — GOVERNO DO DISTRITO FEDERAL. **Secretaria de Mobilidade Urbana (SEMOB)**. API de rastreamento de frota do STPC/DF. Disponível em: portal de dados abertos do GDF. Acesso em: jun. 2026.

IPEDF — INSTITUTO DE PESQUISA E ESTATÍSTICA DO DISTRITO FEDERAL. **Pesquisa Distrital por Amostra de Domicílios — PDAD 2022**. Brasília: IPEDF, 2022.

ISO/IEC 25010:2011. **Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models**. Geneva: ISO, 2011. Adotada como ABNT NBR ISO/IEC 25010.

KRUCHTEN, Philippe. The 4+1 view model of architecture. **IEEE Software**, v. 12, n. 6, p. 42–50, nov. 1994.

CGDF — CONTROLADORIA GERAL DO DISTRITO FEDERAL. **Painel de Ouvidoria do Distrito Federal**. Brasília: CGDF, 2026.

SOMMERVILLE, Ian. **Engenharia de Software**. 10. ed. São Paulo: Pearson, 2019.

---

## Atualização — Gateway como Proxy (US #31)

### Visão Geral

O Gateway é o **ponto único de entrada** para todas as requisições do frontend.
Nenhum serviço backend se comunica com o banco diretamente — tudo passa pelo Gateway.

```
[Browser]
    │  cookies: access_token + refresh_token
    ▼
[Next.js Frontend]
    │  envia cookies automaticamente
    ▼
[API Gateway — Ponto Único de Entrada]
    │  lê access_token do cookie
    │  valida JWT localmente
    │  extrai identidadeUsuario
    │  roteia para serviços backend
    ├──► [Auth Service] ──► [PostgreSQL]
    ├──► [Mobilidade Service] ──► [PostgreSQL]
    └──► [Colaboracao Service] ──► [PostgreSQL]
```

### Endpoints de Proxy

| Endpoint | Método | Destino |
|----------|--------|---------|
| `/api/auth/login` | POST | Auth Service |
| `/api/auth/registrar` | POST | Auth Service |
| `/api/auth/refresh` | POST | Auth Service |
| `/api/auth/logout` | POST | Auth Service |
| `/api/mobilidade/*` | GET/POST/PUT/DELETE | Mobilidade Service |
| `/api/colaboracao/*` | GET/POST/PUT/DELETE | Colaboracao Service |

### Fluxo de Proxy

```
1. Browser envia request para /api/*
2. Gateway recebe e valida JWT (middleware)
3. Gateway roteia para serviço backend correspondente
4. Serviço backend processa e retorna response
5. Gateway retorna response para Browser
```

### Configuração dos Serviços

```python
# gateway/config.py
class GatewaySettings(BaseSettings):
    AUTH_SERVICE_URL: str = "https://movecity-auth.fly.dev"
    MOBILIDADE_SERVICE_URL: str = "https://movecity-mobilidade.fly.dev"
    COLABORACAO_SERVICE_URL: str = "https://movecity-colaboracao.fly.dev"

    class Config:
        env_prefix = "GATEWAY_"
        env_file = ".env"
```

> URLs públicas HTTPS, e não nomes de rede interna — ver ADR-01 na seção 10.

### Cookies

| Cookie | HttpOnly | Secure | SameSite | Path | Max Age |
|--------|----------|--------|----------|------|---------|
| `access_token` | ✅ | ✅ | **None** | `/api` | 60 min |
| `refresh_token` | ✅ | ✅ | **None** | `/api/auth` | 7 dias |

> `SameSite=None` (e não `Lax`/`Strict`) porque o frontend e o Gateway estão em domínios diferentes — ver ADR-07 na seção 10. `Secure=True` é obrigatório junto com `SameSite=None`: sem ele, o navegador ignora o cookie.

### Arquivos do Gateway

| Arquivo | Responsabilidade |
|---------|------------------|
| `middleware.py` | Valida JWT do cookie em cada request |
| `jwt_validator.py` | Decodifica e valida tokens JWT |
| `dependencies.py` | `get_usuario_atual` para endpoints protegidos |
| `proxy.py` | Proxy genérico para serviços backend |
| `cookies.py` | Helper para setar/limpar cookies httpOnly |
| `config.py` | Configuração das URLs dos serviços |
| `routes.py` | Endpoints de proxy (auth, mobilidade, colaboracao) |
