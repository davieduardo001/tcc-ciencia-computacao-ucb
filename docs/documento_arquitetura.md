# Documento de Arquitetura de Software — Movecity

**Grupo:** Segurança no Transporte  
**Software:** Movecity  
**Versão:** 1.0

---

## Histórico da Revisão

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 12/jun/26 | 1.0 | Versão inicial do documento | Grupo Segurança no Transporte |

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
10. [Referências](#10-referências)

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
| **PostGIS** | Extensão geoespacial para PostgreSQL |
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
| **Desempenho** | O carregamento inicial do mapa e das posições dos ônibus deve ocorrer em no máximo 3 segundos em conexões 4G. | Uso de SSR/SSG no Next.js para reduzir o tempo de interação inicial; tiles do OpenStreetMap carregados de forma lazy; dados GPS consumidos via WebSocket ou polling com intervalo configurável. |
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
| **Linguagem — Backend** | Python 3.12 | Maturidade do ecossistema científico/geoespacial (Shapely, PostGIS); equipe familiarizada com a linguagem. |
| **Framework — Backend** | FastAPI (v0.110+) | Framework assíncrono de alto desempenho; documentação automática via OpenAPI 3.0; validação com Pydantic. |
| **Componente de mapa** | Leaflet JS (v1.9) + OpenStreetMap | Gratuito e open source; sem risco de custos em produção; altamente customizável; suporte a GeoJSON nativo. |
| **Formas de persistência** | Banco de dados relacional + cache em memória (futuro) | Dados relacionais para entidades do domínio; cache para posições GPS em alta frequência de atualização. |
| **Banco de dados** | PostgreSQL 15 + extensão PostGIS (Neon serverless) | Free tier generoso para TCC; suporte a dados geoespaciais via PostGIS; escalabilidade serverless automática. |
| **Serviços de terceiros** | API GPS SEMOB/GDF (GeoJSON), Google OAuth 2.0 | Dados oficiais das frotas; autenticação social reduz atrito no cadastro. |
| **Deploy — Backend** | Fly.io (Docker) | Deploy simples via Dockerfile; suporte a múltiplas regiões; free tier adequado para projeto-piloto. |
| **Deploy — Frontend** | Vercel ou Fly.io | Integração nativa com Next.js; deploy automático por push. |
| **CI/CD** | GitHub Actions | Integração nativa com o repositório; pipelines de teste e deploy automatizados sem custo adicional. |
| **Autenticação** | JWT (stateless) | Elimina estado de sessão no servidor; validação local no API Gateway sem round-trip ao serviço de autenticação. |

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

- **Serviço de Mobilidade (`<<servico mobilidade>>`):** Núcleo funcional da plataforma. Processa dados GPS da API GDF, calcula ETAs, gerencia linhas, paradas e rotas.

- **Serviço de Colaboração (`<<servico colaboracao>>`):** Gerencia o fluxo de reportes colaborativos, validação cruzada, rotas favoritas, notificações e alertas.

- **Camada de Dados (`<<modelo>>`):** PostgreSQL com PostGIS para dados persistentes e API externa da SEMOB/GDF para posições GPS em tempo real.

### 4.4 Representação do Funcionamento da Arquitetura

O diagrama de sequência da UML descreve a colaboração temporal entre os objetos do sistema para um determinado cenário. Ele é fundamental para que os desenvolvedores compreendam como as camadas da arquitetura interagem em tempo de execução, especialmente o papel do API Gateway na validação de sessão e no roteamento de requisições.

O cenário escolhido é o **rastreamento de posição de ônibus em tempo real (UC16)** com token JWT válido, pois demonstra o fluxo completo entre todas as camadas da arquitetura:

> **[Anexar imagem]** Diagrama de sequência UML — UC16: Rastrear Posição do Ônibus em Tempo Real.
> Arquivo fonte: `docs/diagramas/sequencia/UC16-rastrear-posicao-onibus-tempo-real.puml`

*Figura 3 — Diagrama de sequência: UC16 – Rastrear posição do ônibus em tempo real*

> Os diagramas de sequência completos para todos os casos de uso (UC14–UC30) estão disponíveis em `docs/diagramas/sequencia/` no formato PlantUML.

---

## 5. Visão de Processos

O Movecity opera com dois processos principais em execução concorrente no backend:

**Processo de Ingestão GPS (thread de background):** Um worker assíncrono do FastAPI realiza polling periódico na API da SEMOB/GDF (intervalo configurável, padrão: 30 segundos) para obter as posições atualizadas dos veículos em formato GeoJSON. Os dados são normalizados e persistidos no PostgreSQL com PostGIS. Este processo é independente das requisições dos usuários e comunica-se com o serviço de mobilidade via chamadas internas.

**Processo de Atendimento a Requisições (processo principal):** O servidor FastAPI atende requisições HTTP/HTTPS dos clientes de forma assíncrona (via `asyncio`), permitindo alta concorrência sem bloqueio de I/O. Inclui os endpoints RESTful do API Gateway, dos serviços de mobilidade, colaboração e autenticação.

A comunicação entre os processos ocorre pelo banco de dados compartilhado (PostgreSQL), garantindo consistência sem acoplamento direto entre os processos.

---

## 6. Visão da Implementação

O código-fonte do Movecity está organizado nos seguintes módulos principais:

**Frontend (`/src/frontend/`):**
- `app/` — Páginas e layouts (Next.js App Router)
- `components/` — Componentes React reutilizáveis
- `lib/` — Utilitários, clientes HTTP e hooks customizados
- `public/` — Assets estáticos

**Backend (`/src/backend/`):**
- `gateway/` — Módulo do API Gateway (roteamento, validação JWT)
- `auth/` — Serviço de autenticação (usuários, sessões, OAuth)
- `mobilidade/` — Serviço de mobilidade (linhas, paradas, GPS, rotas)
- `colaboracao/` — Serviço de colaboração (reportes, notificações, favoritos)
- `models/` — Modelos ORM (SQLAlchemy) e schemas Pydantic
- `core/` — Configurações, dependências e utilitários compartilhados

---

## 7. Visão de Implantação

O Movecity é implantado em infraestrutura de nuvem, com cada componente em seu ambiente adequado:

> **[Anexar imagem]** Diagrama de implantação UML — nós: CDN/Vercel Edge (frontend), Fly.io (backend FastAPI + API Gateway + serviços), Neon PostgreSQL e API externa SEMOB/GDF.
> Rascunho ASCII disponível em `docs/diagramas/rascunhos-ascii.md` (Figura 4).

*Figura 4 — Diagrama de implantação do Movecity*

**Nós físicos/lógicos:**
- **Vercel / Fly.io Edge:** Hospeda o frontend Next.js com suporte a SSR. Distribui conteúdo estático via CDN global.
- **Fly.io (backend):** Executa o backend FastAPI em contêiner Docker. Suporta auto-scaling horizontal e health checks automáticos.
- **Neon (managed PaaS):** PostgreSQL serverless com extensão PostGIS. Escala automaticamente conforme a demanda.
- **API SEMOB/GDF:** Serviço externo fornecido pelo Governo do Distrito Federal. Não gerenciado pelo Movecity.

---

## 8. Visão de Dados

O Movecity persiste dados estruturados no PostgreSQL. A seguir, a descrição das entidades principais e seus relacionamentos.

**Minimundo:** Um `Usuario` pode ter várias `Sessao` ativas e múltiplas `RotaFavorita`. Cada `RotaFavorita` referencia uma `LinhaNibus`. Uma `LinhaNibus` possui várias `Parada` e pode ter registros de `PosicaoOnibus` (atualizada continuamente pelo worker de ingestão GPS). Um `Usuario` autenticado pode criar `Ocorrencia` vinculada a uma `LinhaNibus`. Outras instâncias de `Usuario` podem confirmar uma `Ocorrencia` existente, incrementando seu contador de confirmações.

**Modelo Entidade-Relacionamento (MER):**

> **[Anexar imagem]** MER do Movecity — entidades: `USUARIO`, `SESSAO`, `ROTA_FAVORITA`, `OCORRENCIA`, `LINHA_ONIBUS`, `PARADA`, `POSICAO_ONIBUS`.
> Rascunho textual disponível em `docs/diagramas/rascunhos-ascii.md` (seção MER).

> Os campos geoespaciais (`geom POINT`) utilizam a extensão PostGIS com o sistema de referência WGS84 (SRID 4326), compatível com o formato GeoJSON da API da SEMOB/GDF.

---

## 9. Volume e Desempenho

Estimativas de dimensionamento para o projeto-piloto em Ceilândia e Taguatinga:

| Métrica | Valor Estimado |
|---|---|
| **Usuários cadastrados (fase piloto)** | 5.000 |
| **Usuários simultâneos (média)** | 500 |
| **Pico de usuários simultâneos** (horários de pico) | 1.500 |
| **Requisições por segundo** (pico) | 150 req/s |
| **Frequência de atualização GPS** | A cada 30 segundos por linha |
| **Linhas de ônibus monitoradas** (piloto) | ~50 linhas |
| **Volume inicial de dados** | ~5 GB |
| **Crescimento de dados** | ~2 GB/mês |
| **Retenção de posições GPS** | 24 horas (janela deslizante) |
| **Retenção de ocorrências** | 30 dias |
| **Backup** | Diário (gerenciado pelo Neon) |
| **Disponibilidade mínima** | 99% nos horários de pico (5h–9h e 17h–20h) |
| **Tempo de carregamento inicial** | ≤ 3 segundos em conexão 4G |

---

## 10. Referências

CAROLI, Paulo. **Lean Inception: como alinhar pessoas e construir o produto certo**. São Paulo: Caroli.org, 2018.

GDF — GOVERNO DO DISTRITO FEDERAL. **Secretaria de Mobilidade Urbana (SEMOB)**. API de rastreamento de frota do STPC/DF. Disponível em: portal de dados abertos do GDF. Acesso em: jun. 2026.

IPEDF — INSTITUTO DE PESQUISA E ESTATÍSTICA DO DISTRITO FEDERAL. **Pesquisa Distrital por Amostra de Domicílios — PDAD 2022**. Brasília: IPEDF, 2022.

ISO/IEC 25010:2011. **Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models**. Geneva: ISO, 2011. Adotada como ABNT NBR ISO/IEC 25010.

KRUCHTEN, Philippe. The 4+1 view model of architecture. **IEEE Software**, v. 12, n. 6, p. 42–50, nov. 1994.

CGDF — CONTROLADORIA GERAL DO DISTRITO FEDERAL. **Painel de Ouvidoria do Distrito Federal**. Brasília: CGDF, 2026.

SOMMERVILLE, Ian. **Engenharia de Software**. 10. ed. São Paulo: Pearson, 2019.
