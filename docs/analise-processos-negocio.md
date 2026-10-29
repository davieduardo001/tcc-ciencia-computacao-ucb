# Análise e Modelagem de Processos de Negócio — AS-IS, TO-BE com o Movecity e Desenvolvimento com Agentes de IA (Versão Completa)

**Projeto:** Movecity — Mobilidade Urbana Colaborativa no DF
**Disciplina:** Análise de Processos de Negócio — Universidade Católica de Brasília (UCB)
**Professor orientador (disciplina):** Oscar Galdino de Oliveira Junior
**Autores deste documento:** Vitória Cordeiro Albuquerque, Davi Eduardo Costa Miranda e Nathalia Gualberto Lopes
**Versão:** 3.0 — estado do produto em **28/10/2026**

> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/analise-processos-negocio.md>

> **Nota — esta é a versão completa (material de apoio):** a disciplina exige um documento de no máximo 25 páginas. A **entrega oficial** é a versão resumida, em `docs/analise-processos-negocio-resumo.md` (<https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/analise-processos-negocio-resumo.md>). Este documento — com o detalhamento elemento-a-elemento de cada diagrama BPMN — vai anexado como material complementar, junto com os arquivos `.bpmn`.

> **Regra de leitura desta versão:** o documento descreve o Movecity **como ele está hoje**, e não como foi planejado. "Entregue" significa **mergeado em `homolog` ou `main`**; o que está em produção é o código de `homolog` (o frontend e o Gateway publicados rodam essa branch; ver `docs/qa/resumo-executivo.md`). Toda afirmação sobre o produto tem fonte: o código, uma issue ou PR do repositório, ou o registro de testes em `docs/qa/`. O que não foi feito ou não foi medido está escrito como tal e como trabalho futuro. Os números do repositório foram consultados com `gh` em 28/10/2026.

> **Nota sobre autoria:** este documento é entregável da disciplina de Análise de Processos de Negócio, cursada por apenas 3 dos 6 integrantes do grupo Segurança no Transporte, sob orientação do Prof. Oscar Galdino de Oliveira Junior. O restante do time do TCC Movecity — Breno Santana Silva, Kelvin Rodrigues de Sousa e Luis Fernando Monteiro de Assis Lourenço — e o orientador do TCC têm participação ativa no projeto Movecity como um todo (ver `docs/distribuicao_us.md`), mas não neste documento específico.

> **Nota sobre uso de IA na elaboração deste documento:** ferramentas de IA (Claude Code) foram utilizadas como apoio em três frentes pontuais: (1) **correção e revisão textual** do documento; (2) **pesquisa de apoio** sobre notação BPMN 2.0 e boas práticas de modelagem; e (3) **verificação técnica dos diagramas** — checagem de que os fluxos de mensagem seguem a notação corretamente e geração dos arquivos-fonte `.bpmn` a partir da especificação já definida pelos autores. Na versão 3.0, a IA também apoiou a conferência das afirmações sobre o produto contra o código, as issues e os PRs. A identificação dos processos, a análise das disfunções, as decisões de modelagem e o conteúdo intelectual do trabalho são dos autores listados acima. (Isto é distinto do desenvolvimento do software, tratado nas seções 4 e 5: lá, todo o código do Movecity foi gerado por agentes de IA conduzidos pelos seis estudantes.)

---

## Histórico da Revisão

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 18/set/26 | 1.0 | Versão inicial — contextualização, identificação e classificação dos processos e modelagem AS-IS | Grupo Segurança no Transporte |
| 27/set/26 | 2.0 | Correção de autoria (documento é da disciplina de Análise de Processos de Negócio, não do TCC coletivo); correção de fluxos de mensagem e recalibração de escopo em P01 e P04; adição do processo de desenvolvimento assistido por IA e da defesa do seu uso | Vitória Cordeiro Albuquerque, Davi Eduardo Costa Miranda e Nathalia Gualberto Lopes |
| 28/out/26 | 3.0 | Atualização ao estado do produto em 28/10/2026: situação real do desenvolvimento (1.4); o TO-BE com o Movecity (3.4) passa a descrever o que foi entregue, não o planejado, e o diagrama `02-processo-com-movecity.bpmn` foi corrigido (removidos o fallback colaborativo, a notificação do cancelamento pela operadora e o alerta push de cancelamento, que não existem); novo quadro AS-IS × TO-BE ligado às nove disfunções (3.5); seções 4 e 5 com fatos reais de volume, qualidade e limites do desenvolvimento com agentes de IA; síntese das disfunções (6) e próximos passos (7) atualizados | Davi Eduardo Costa Miranda |

---

## Índice Analítico

1. [Contextualização do Projeto](#1-contextualização-do-projeto)
   - 1.1 [Descrição do sistema](#11-descrição-do-sistema)
   - 1.2 [Problema que o sistema resolve](#12-problema-que-o-sistema-resolve)
   - 1.3 [Beneficiários](#13-beneficiários)
   - 1.4 [Situação atual do desenvolvimento](#14-situação-atual-do-desenvolvimento)
   - 1.5 [Delimitação do escopo desta entrega](#15-delimitação-do-escopo-desta-entrega)
2. [Identificação dos Processos de Negócio](#2-identificação-dos-processos-de-negócio)
   - 2.1 [Critério de classificação adotado](#21-critério-de-classificação-adotado)
   - 2.2 [Visão macro da cadeia de valor](#22-visão-macro-da-cadeia-de-valor)
   - 2.3 [Inventário de processos](#23-inventário-de-processos)
   - 2.4 [Processos críticos para a geração de valor](#24-processos-críticos-para-a-geração-de-valor)
   - 2.5 [Processos selecionados para modelagem](#25-processos-selecionados-para-modelagem)
3. [Modelagem dos Processos Atuais (AS-IS)](#3-modelagem-dos-processos-atuais-as-is)
   - 3.1 [Convenções de modelagem](#31-convenções-de-modelagem)
   - 3.2 [Processo P01 — Planejar e realizar deslocamento por ônibus (AS-IS manual)](#32-processo-p01--planejar-e-realizar-deslocamento-por-ônibus-as-is)
   - 3.3 [Processo P04 — Registrar e tratar ocorrência no serviço (AS-IS manual)](#33-processo-p04--registrar-e-tratar-ocorrência-no-serviço-as-is)
   - 3.4 [TO-BE com o Movecity — o processo com o sistema entregue](#34-to-be-com-o-movecity--o-processo-com-o-sistema-entregue)
   - 3.5 [Quadro comparativo AS-IS × TO-BE por disfunção](#35-quadro-comparativo-as-is--to-be-por-disfunção)
4. [Processo de Desenvolvimento Assistido por Agentes de IA](#4-processo-de-desenvolvimento-assistido-por-agentes-de-ia)
   - 4.1 [Ficha do processo](#41-ficha-do-processo)
   - 4.2 [Stakeholders envolvidos](#42-stakeholders-envolvidos)
   - 4.3 [Recursos atuais utilizados](#43-recursos-atuais-utilizados)
   - 4.4 [Estrutura do diagrama: pools e raias](#44-estrutura-do-diagrama-pools-e-raias)
   - 4.5 [Elementos do diagrama](#45-elementos-do-diagrama)
   - 4.6 [Fluxos de sequência](#46-fluxos-de-sequência)
   - 4.7 [Fluxos de mensagem entre pools](#47-fluxos-de-mensagem-entre-pools)
   - 4.8 [Narrativa do fluxo](#48-narrativa-do-fluxo)
   - 4.9 [Riscos de governança e mitigação](#49-riscos-de-governança-e-mitigação)
   - 4.10 [O processo na prática: volume, qualidade e falhas](#410-o-processo-na-prática-volume-qualidade-e-falhas)
5. [Defesa do Uso de Agentes de IA no Desenvolvimento](#5-defesa-do-uso-de-agentes-de-ia-no-desenvolvimento)
   - 5.1 [Legitimidade acadêmica](#51-legitimidade-acadêmica)
   - 5.2 [Rastreabilidade e governança](#52-rastreabilidade-e-governança)
   - 5.3 [Qualidade e produtividade: o que os números sustentam](#53-qualidade-e-produtividade-o-que-os-números-sustentam)
   - 5.4 [Limites e riscos assumidos](#54-limites-e-riscos-assumidos)
6. [Síntese das Disfunções Identificadas](#6-síntese-das-disfunções-identificadas)
7. [Próximos Passos](#7-próximos-passos)
8. [Referências](#8-referências)

---

## 1. Contextualização do Projeto

### 1.1 Descrição do sistema

O **Movecity** é um aplicativo web de mobilidade urbana colaborativa desenvolvido como Trabalho de Conclusão de Curso pelo grupo Segurança no Transporte da UCB. A plataforma combina duas fontes de informação que hoje existem de forma isolada:

1. **Dados oficiais de GPS** da frota do Sistema de Transporte Público Coletivo do Distrito Federal (STPC/DF), consumidos dos endpoints públicos da SEMOB/GDF (`dados.semob.df.gov.br`, em GeoJSON), que não têm documentação nem SLA publicados;
2. **Reportes colaborativos** dos próprios passageiros, no modelo de inteligência coletiva popularizado pelo Waze, submetidos a validação cruzada (no produto entregue, os tipos que dependem de confirmação só passam a "Confirmada" quando 3 outros passageiros a confirmam; "acidente" e "segurança" são exibidos de imediato; ver 3.4.7).

O resultado é um mapa em tempo real, com previsão de chegada, itinerário, paradas, planejador de rota e ocorrências reportadas (atraso, ônibus que não passou, risco de segurança). Os alertas de atraso e de cancelamento fazem parte da proposta, mas **não chegam ao usuário nesta versão** (seção 1.4). O sistema opera como projeto-piloto em **Taguatinga e Ceilândia**, regiões administrativas escolhidas por concentrarem alta densidade demográfica e intensa demanda por transporte público.

### 1.2 Problema que o sistema resolve

O domínio de atuação é a **gestão e o consumo de informação sobre a mobilidade urbana no DF**, marcado por uma profunda assimetria de informação: embora a frota seja monitorada por GPS, o dado real sobre a localização dos veículos raramente chega ao cidadão de forma fidedigna. Disso decorrem três problemas centrais:

| Problema | Descrição | Consequência para o cidadão |
|---|---|---|
| **"Ônibus fantasma"** | Veículos que constam na programação oficial mas não realizam o percurso, ou que passam fora do horário previsto sem aviso prévio. | Espera indefinida, perda de compromissos, desconfiança no sistema. |
| **Insegurança física e psicológica** | Espera prolongada em paradas isoladas e com iluminação precária nas cidades-satélites. | Exposição a assaltos e violência; ansiedade durante a espera. |
| **Ineficiência operacional e econômica** | Ausência de previsibilidade impede o planejamento do deslocamento. | Margens de segurança de 15 a 30 minutos por trajeto, perda de produtividade e gasto extra com transporte alternativo. |

*Tabela 1 – Problemas atacados pelo Movecity*

### 1.3 Beneficiários

| Beneficiário | Tipo | Como é beneficiado |
|---|---|---|
| **Trabalhador de turnos críticos** | Direto (primário) | Previsibilidade em horários de baixa oferta (madrugada e noite), quando o risco da espera é maior. |
| **Estudante de ensino superior e técnico** | Direto (primário) | Planejamento do deslocamento entre casa, trabalho e instituição de ensino. |
| **Profissional corporativo e autônomo** | Direto (primário) | Redução da margem de segurança embutida no trajeto e do custo com transporte alternativo. |
| **Passageiro com mobilidade reduzida e idosos** | Direto (primário) | Redução do tempo de exposição na parada e informação sobre acessibilidade do veículo. |
| **Empresas operadoras do STPC/DF** | Indireto (secundário) | Redução de reclamações no SAC e evidências para apuração de ocorrências. |
| **SEMOB/GDF e órgãos de fiscalização** | Indireto (secundário) | Base de dados sobre falhas percebidas pelo usuário, útil para fiscalização e planejamento da oferta. |
| **Sociedade do DF** | Indireto (terciário) | Maior transparência sobre a qualidade do serviço público de transporte. |

*Tabela 2 – Beneficiários do projeto*

Segundo a Pesquisa Distrital por Amostra de Domicílios (IPEDF, 2022), **33,3% da população do DF utiliza o ônibus como principal meio de transporte**, o que dimensiona a população potencialmente impactada pela solução.

### 1.4 Situação atual do desenvolvimento

**Estado em 28/10/2026** (fontes: `gh issue list` e `gh pr list` de 28/10; `docs/guia-apresentacao.md`, seção 3; `docs/qa/`). A defesa do TCC é em 13/11/2026.

**Volume.** O repositório tem 101 issues (70 fechadas e 31 abertas) e 146 PRs (132 mergeados, 11 fechados sem merge e 3 abertos) na consulta de 28/10. O guia de apresentação, de 27/10, registrava 84 issues e 126 PRs; a diferença é o trabalho das últimas 24 horas (correções, validação em produção e documentação). Das 24 histórias de usuário distribuídas entre os integrantes (`docs/distribuicao_us.md`), organizadas em três épicos (Autenticação, Mapa e Rastreamento, Colaboração), o repositório tem 38 issues com rótulo de épico, das quais 30 fechadas e 8 abertas. O trabalho foi organizado em cinco sprints (issues #38, #90, #144, #175 e #206; a Sprint 4, de fechamento e apresentação, segue aberta).

**Arquitetura implementada.** API Gateway como ponto único de entrada (JWT validado localmente, cookies httpOnly), três serviços de domínio em FastAPI (autenticação, mobilidade e colaboração), frontend em Next.js com Leaflet, banco PostgreSQL (Neon), quatro apps no Fly.io e frontend na Vercel (`docs/documento_arquitetura.md`, seção 10). Decisões que contrariaram o plano inicial estão registradas nessa seção: sem PostGIS (ADR-02), dados da SEMOB copiados para o banco por ingestão em lote (ADR-03) e posições de GPS lidas ao vivo com cache de 20 s e nunca persistidas (ADR-04).

**O que foi entregue** (mergeado em `homolog` ou `main`; entre parênteses, a issue e o PR principal):

| Épico | Entregue |
|---|---|
| Autenticação | Login com e-mail e senha (#10, PR #75); cadastro (#11, PR #52) com aceite dos termos (validado no servidor desde o PR #218); login com Google (#12, PRs #91 e #93); recuperação de senha com telas e rota no Gateway (#13 e #133, PRs #87 e #153) e envio do e-mail por SMTP (#237, PR #238); ciclo de vida da sessão, com cookies httpOnly e renovação automática (#31, PRs #56 e #66; rota de refresh e renovação no frontend em #212 e #221, PRs #218 e #222); termos de uso e política de privacidade (#32) |
| Mapa e rastreamento | Mapa com a localização atual (#14, PR #85); busca de linha por número (#15, PR #99), com autocomplete por nome ou destino (PR #108); ônibus em tempo real, com rumo e idade da posição (#16, PRs #120 e #124); trajeto e paradas da linha (#17, PRs #105 e #111); detalhes da parada (#18, PRs #169 e #192); tempo estimado de chegada com a fonte declarada (#19, #159 e #179, PRs #154, #160 e #181 a #185); rota de origem a destino, com baldeação (#20, PRs #116 e #119); busca de parada por nome ou endereço (#21, PR #197); "Peguei este ônibus" com acompanhamento da viagem (#171, PRs #186 e #187); paradas de subir e descer na rota, com o tempo do ônibus (#190, PRs #191 e #193); aviso de proximidade da parada de destino (#172, PRs #178 e #194) e por Web Push com a tela bloqueada (#195, PR #196) |
| Colaboração | Reportar ocorrência em uma linha (#23, PR #162); ver as ocorrências reportadas por outros passageiros (#24, PR #180); confirmar a ocorrência de outro passageiro (#26, PR #209); rota favorita (#25, PR #176); preferências de notificação, com a tela em `/alertas` (#29, PRs #127 e #223); tutorial no primeiro acesso (#30, PR #158); protótipo de alta fidelidade (#33) |
| Transversal | Instalação como PWA (#136, PR #137); identidade visual v3 (#143, PRs #131 e #166); correção do `X-User-Id` repassado pelo cliente, caso de segurança (#188, PR #189) |

**O que foi entregue com limites** (a funcionalidade existe no código, mas não chega ao usuário como a história descreve):

| Item | Limite, com fonte |
|---|---|
| Notificações de rotas preferidas (#22, PR #94) | O worker e a deduplicação existem, mas o envio é um registro em memória (`colaboracao/push_service.py`: "deliberadamente desacoplada do Firebase") e o worker não é agendado no serviço de colaboração (`colaboracao/main.py`). Não há notificação ao usuário. |
| Alerta de atraso na linha acompanhada (#27, PR #152) | O monitoramento roda em `mobilidade/main.py` com o fornecedor de horários simulado e o notificador nulo (`NotificadorNulo`). A lógica é coberta por testes unitários, mas não há canal de entrega; o caso CT-NOT-02 está como "não verificável" (`docs/qa/execucao-casos-p1.md`). |
| Web Push do aviso de proximidade (#195, PR #196) | Implementado; as chaves VAPID são aplicadas pelo pipeline (PR #210), mas a validação em aparelho real segue aberta (#200) e o caso CT-VIA-08 só pode ser provado em campo. |
| Confirmar ocorrência (#26) e preferências de notificação (#29) | Código mergeado em `homolog`, mas as issues seguem abertas. A #29 tem caso manual aprovado (CT-NOT-01); a #26 não tem caso manual executado. |
| Embarque ("Peguei este ônibus") | Em produção o raio de embarque está em 100 km (`RAIO_EMBARQUE_M`), por decisão do grupo em 28/10 para demonstrar o recurso de qualquer lugar. A regra de uso real é 100 m. Por isso o caso CT-VIA-01 consta como "reprovado por configuração" (`docs/qa/resumo-executivo.md`). |

**O que ficou de fora** (issues abertas, sem entrega): alerta de cancelamento de viagem (#28); notificações push dos alertas de atraso e das rotas preferidas (#207); motor de planejamento por horário de partida ou chegada, GTFS + RAPTOR (#115); horários de operação da linha (#118); fallback colaborativo, com a posição do ônibus informada por passageiros (#199). Também não existem: confirmação de conta por e-mail (a conta entra direto; o texto do cadastro foi corrigido no PR #238), ambiente de homologação separado da produção (decisão de custo) e qualquer integração com o centro de controle das operadoras.

**Qualidade medida** (`docs/qa/resumo-executivo.md`): 1.640 testes automatizados passando (844 de backend e 796 de frontend, no CI de 28/10; eram 1.260 na medição de 16/10), cobertura de 93,7% no backend e 89,1% no frontend (medida em 16/10, não refeita), 26 defeitos catalogados e os 49 casos manuais executados em produção (32 aprovados, 11 aprovados em parte ou com ressalva, 1 reprovado por configuração, 3 não verificáveis hoje e 2 pendentes de simulação de posição no navegador). Há um risco de segurança conhecido e aberto: o frontend grava os tokens de sessão em `localStorage` (#253). Além disso, a tela de reporte anuncia 2 confirmações enquanto o servidor exige 3 (#249). Não houve validação em campo (tolerância do ETA, regra do ônibus chegando) nem teste com usuários reais.

### 1.5 Delimitação do escopo desta entrega

Esta entrega analisa e modela os processos de negócio do deslocamento por ônibus e do tratamento de ocorrências em **três momentos**: como acontecem **hoje, sem sistema dedicado** (AS-IS); como passam a acontecer **com o Movecity, no estado em que ele foi entregue** (TO-BE); e como o próprio produto foi construído, com agentes de IA (seções 4 e 5). O objetivo é evidenciar, com rigor de notação, onde estão as rupturas de informação que justificam o produto e quais delas o produto efetivamente trata.

A unidade de análise não é uma empresa isolada, mas a **jornada informacional do passageiro do STPC/DF** e o conjunto de processos que a sustentam, envolvendo quatro atores: o passageiro, as empresas operadoras, o poder público (SEMOB/GDF e ouvidoria) e os canais digitais de informação existentes.

Os dois retratos de processo de mobilidade são:

1. **AS-IS manual** (seções 3.2 e 3.3) — o processo sem nenhum sistema dedicado: DF no Ponto, Google Maps, Moovit, grupos de WhatsApp, ouvidoria do GDF, SAC das operadoras.
2. **TO-BE com o Movecity** (seção 3.4) — o mesmo processo com o Movecity ocupando o lugar dos canais fragmentados, **limitado ao que foi entregue** (seção 1.4). Não é uma proposta hipotética: o que não existe no produto não aparece no diagrama e está listado como lacuna na seção 3.5.

---

## 2. Identificação dos Processos de Negócio

### 2.1 Critério de classificação adotado

Adotou-se a classificação proposta pelo **BPM CBOK (ABPMP)**, que distingue três categorias de processos:

| Categoria | Definição | Critério prático de enquadramento |
|---|---|---|
| **Primário** | Processo ponta a ponta que entrega valor diretamente ao cliente final. É o que o beneficiário percebe e pelo qual avalia o serviço. | O passageiro sente o resultado do processo de forma direta e imediata. |
| **De suporte** | Processo que não gera valor percebido diretamente pelo cliente, mas viabiliza a execução dos processos primários. | Se falhar, um processo primário deixa de funcionar, mesmo que o passageiro não saiba por quê. |
| **De gestão** | Processo de planejamento, medição, monitoramento e controle. Assegura que os demais operem dentro das metas e das normas. | Produz decisões, metas, indicadores ou sanções — não produz o serviço em si. |

*Tabela 3 – Categorias de processo conforme o BPM CBOK*

> **Convenção de códigos:** cada processo tem um prefixo de categoria + um número sequencial **dentro daquela categoria** — os números não se relacionam entre categorias diferentes. **P** = processo **Primário** (P01 a P05) · **S** = processo de **Suporte** (S01 a S06) · **G** = processo de **Gestão** (G01 a G05). Na matriz de criticidade (seção 2.4), cada processo recebe nota de 1 (baixo) a 3 (alto) em três critérios — **I**mpacto no beneficiário, **F**requência de execução e grau de **D**isfunção atual — somados na coluna Total.

### 2.2 Visão macro da cadeia de valor

A cadeia de valor do ecossistema de informação da mobilidade no DF se organiza em três camadas. No topo, a **gestão** define metas, quadros de horário e sanções que orientam os processos primários. No centro, os **processos primários** realizam a jornada do passageiro: P01 (planejar e realizar o deslocamento) engloba P02 (consultar a situação da linha) e P03 (aguardar e embarcar na parada) em sequência, com P05 (executar a viagem, do lado da operadora) ocorrendo em paralelo; P04 (registrar e tratar ocorrência) é um processo independente, acionado sempre que uma falha é percebida em qualquer ponto da jornada. Na base, a **camada de suporte** fornece os insumos — dados, cadastro e infraestrutura — que sustentam os processos primários.

| Camada | Processos |
|---|---|
| **Gestão** | G01 Planejar a oferta · G02 Monitorar e fiscalizar a execução · G03 Gerir a qualidade · G04 Gerir contratos · G05 Gerir transparência |
| **Primários** (jornada do passageiro) | P01 Planejar e realizar deslocamento → P02 Consultar a situação da linha → P03 Aguardar e embarcar na parada → P05 Executar a viagem (operadora) · P04 Registrar e tratar ocorrência (paralelo, acionado sob demanda) |
| **Suporte** | S01 Coletar dados de GPS · S02 Manter cadastro de linhas e paradas · S03 Operar canais de atendimento · S04 Manter paradas e terminais · S05 Operar a bilhetagem · S06 Manter canais digitais oficiais |

> **Observação:** P02 e P03 são subprocessos naturais de P01, mas foram mantidos destacados no inventário por possuírem gatilhos, atores e falhas próprias.

### 2.3 Inventário de processos

| ID | Processo | Descrição sucinta | Classificação | Ator responsável (dono) | Gatilho |
|---|---|---|---|---|---|
| **P01** | Planejar e realizar deslocamento por ônibus | Da decisão de sair de casa até a chegada ao destino, incluindo escolha de linha, espera e embarque. | **Primário** | Passageiro | Necessidade de deslocamento |
| **P02** | Consultar a situação da linha em tempo real | Obter posição do veículo, previsão de chegada e confirmação de que a viagem ocorrerá. | **Primário** | Passageiro / canais digitais | Dúvida sobre o horário do ônibus |
| **P03** | Aguardar e embarcar na parada | Permanência na parada, identificação do veículo, embarque e validação da passagem. | **Primário** | Passageiro | Chegada à parada |
| **P04** | Registrar e tratar ocorrência no serviço | Comunicação de falha (viagem não realizada, atraso, superlotação, insegurança) e sua apuração. | **Primário** | Passageiro / Ouvidoria | Ocorrência vivenciada |
| **P05** | Executar a viagem programada | Operação da viagem pela empresa: escala, saída da garagem, cumprimento do itinerário. | **Primário** | Empresa operadora | Início da programação diária |
| **S01** | Coletar e disponibilizar dados de GPS da frota | Captura da posição dos veículos e publicação para os canais de consulta. | **Suporte** | Empresa operadora / SEMOB | Veículo em operação |
| **S02** | Manter cadastro de linhas, itinerários, paradas e horários | Manutenção da base estática que descreve a rede de transporte. | **Suporte** | SEMOB | Alteração na rede ou no quadro de horários |
| **S03** | Operar canais de atendimento ao usuário | Recebimento, triagem e encaminhamento de manifestações (ouvidoria e SAC). | **Suporte** | Ouvidoria do GDF / SAC das operadoras | Manifestação recebida |
| **S04** | Manter a infraestrutura física de paradas e terminais | Abrigo, iluminação, sinalização e identificação de itinerários. | **Suporte** | GDF / administrações regionais | Demanda de manutenção ou obra |
| **S05** | Operar a bilhetagem eletrônica | Emissão, recarga e validação do cartão de transporte. | **Suporte** | SEMOB / operadoras | Embarque ou recarga |
| **S06** | Manter os canais digitais oficiais | Desenvolvimento e sustentação do aplicativo oficial e dos portais de consulta. | **Suporte** | SEMOB | Evolução ou incidente no canal |
| **G01** | Planejar a oferta e programar a operação | Definição de frequências, quadros de horário e dimensionamento da frota. | **Gestão** | SEMOB | Ciclo de planejamento / revisão de demanda |
| **G02** | Monitorar e fiscalizar a execução do serviço | Verificação do cumprimento das viagens programadas e da qualidade do serviço. | **Gestão** | SEMOB | Ciclo de monitoramento |
| **G03** | Gerir a qualidade a partir das manifestações | Consolidação das manifestações em indicadores e ações de melhoria. | **Gestão** | Ouvidoria / SEMOB | Fechamento do período de apuração |
| **G04** | Gerir os contratos de concessão | Acompanhamento do desempenho contratual das operadoras e aplicação de penalidades. | **Gestão** | SEMOB / GDF | Ciclo contratual |
| **G05** | Gerir a transparência e a abertura de dados | Publicação de dados operacionais em formato aberto para a sociedade. | **Gestão** | SEMOB / CGDF | Política de dados abertos |

*Tabela 4 – Inventário de processos de negócio relacionados ao Movecity*

### 2.4 Processos críticos para a geração de valor

Para identificar os processos críticos, aplicaram-se três critérios de avaliação, pontuados de 1 (baixo) a 3 (alto):

- **Impacto no beneficiário (I):** quanto o resultado do processo afeta diretamente a experiência do passageiro.
- **Frequência (F):** com que regularidade o processo é executado.
- **Grau de disfunção atual (D):** o quanto o processo, hoje, falha em entregar o resultado esperado.

| ID | Processo | Classificação | I | F | D | Total | Criticidade |
|---|---|---|:-:|:-:|:-:|:-:|---|
| **P02** | Consultar a situação da linha em tempo real | Primário | 3 | 3 | 3 | **9** | **Crítico** |
| **P01** | Planejar e realizar deslocamento por ônibus | Primário | 3 | 3 | 3 | **9** | **Crítico** |
| **P03** | Aguardar e embarcar na parada | Primário | 3 | 3 | 2 | **8** | **Crítico** |
| **S01** | Coletar e disponibilizar dados de GPS da frota | Suporte | 3 | 3 | 3 | **9** | **Crítico** |
| **P04** | Registrar e tratar ocorrência no serviço | Primário | 2 | 2 | 3 | **7** | **Crítico** |
| **G02** | Monitorar e fiscalizar a execução do serviço | Gestão | 2 | 2 | 3 | **7** | Alta |
| **P05** | Executar a viagem programada | Primário | 3 | 3 | 2 | **8** | Alta |
| **S02** | Manter cadastro de linhas, itinerários e paradas | Suporte | 2 | 1 | 2 | **5** | Média |
| **S06** | Manter os canais digitais oficiais | Suporte | 2 | 2 | 2 | **6** | Média |
| **S03** | Operar canais de atendimento ao usuário | Suporte | 1 | 2 | 3 | **6** | Média |
| **G01** | Planejar a oferta e programar a operação | Gestão | 2 | 1 | 2 | **5** | Média |
| **G03** | Gerir a qualidade a partir das manifestações | Gestão | 1 | 1 | 3 | **5** | Média |
| **S04** | Manter a infraestrutura física de paradas | Suporte | 2 | 1 | 3 | **6** | Média |
| **S05** | Operar a bilhetagem eletrônica | Suporte | 2 | 3 | 1 | **6** | Baixa |
| **G05** | Gerir a transparência e a abertura de dados | Gestão | 1 | 1 | 2 | **4** | Baixa |
| **G04** | Gerir os contratos de concessão | Gestão | 1 | 1 | 2 | **4** | Baixa |

*Tabela 5 – Matriz de criticidade dos processos*

**Justificativa dos processos críticos:**

- **P01, P02 e P03** concentram a experiência percebida pelo passageiro. Uma falha aqui não é compensável depois: o tempo perdido na parada e o compromisso perdido não se recuperam. São, portanto, os processos onde o valor do Movecity se materializa.
- **S01 (coleta e disponibilização do GPS)** é o único processo de suporte classificado como crítico. A razão é que ele é a **causa raiz** da disfunção em P01, P02 e P03: o dado de posição existe na operadora, mas não chega de forma confiável ao passageiro. Sem resolver S01 — ou contorná-lo com uma fonte alternativa, que é exatamente o papel do reporte colaborativo —, nenhum ganho nos processos primários é sustentável.
- **P04 (registro e tratamento de ocorrência)** é crítico não pela frequência, mas pelo **grau de disfunção**: o ciclo atual é tão lento e tão pouco responsivo que a maioria das ocorrências simplesmente não é registrada. Essa subnotificação impede que G02 e G03 disponham de dados reais sobre a qualidade percebida do serviço.

### 2.5 Processos selecionados para modelagem

Foram selecionados para modelagem AS-IS os dois processos que, somados, cobrem os dois lados da proposta de valor do Movecity — o consumo e a produção de informação:

| Processo modelado | Justificativa da escolha |
|---|---|
| **P01 — Planejar e realizar deslocamento por ônibus** (engloba P02 e P03) | É o processo primário de maior criticidade e o que materializa as três dores do projeto. Ao englobar a consulta (P02) e a espera (P03) como partes do fluxo, evidencia a ruptura de informação no exato ponto em que ela dói. |
| **P04 — Registrar e tratar ocorrência no serviço** | É o contraponto de P01: trata do fluxo de informação que sai do passageiro. Modelá-lo evidencia por que a colaboração, hoje, se perde — fundamento do módulo de reportes colaborativos do Movecity. |

*Tabela 6 – Processos selecionados para a modelagem AS-IS*

> **Sobre P05:** o processo P05 (execução da viagem pela operadora) não recebe modelagem própria — ele aparece nos diagramas de P01 e do TO-BE com o Movecity como o processo paralelo do lado da empresa operadora (pool "Empresa operadora"), necessário para o fluxo do passageiro fazer sentido (é o motorista chegando à parada que ele espera), mas não é um dos dois processos escolhidos como foco desta modelagem.

---

## 3. Modelagem dos Processos Atuais (AS-IS)

### 3.1 Convenções de modelagem

Os processos foram modelados segundo a notação **BPMN 2.0 (OMG)**. Para permitir a construção dos diagramas em qualquer ferramenta aderente à norma (Bizagi Modeler, Camunda Modeler, bpmn.io, Draw.io), cada processo é especificado em seis blocos:

1. **Ficha do processo** — objetivo, gatilho, resultado, dono e fronteiras;
2. **Stakeholders** — quem participa e qual o interesse de cada um;
3. **Recursos atuais** — humanos, tecnológicos e físicos;
4. **Estrutura do diagrama** — pools (piscinas) e lanes (raias);
5. **Elementos e fluxos** — tabelas com identificador, tipo BPMN, rótulo e conexões;
6. **Disfunções** — gargalos ancorados em elementos específicos do diagrama.

**Elementos da notação utilizados:**

| Elemento BPMN | Representação | Uso neste documento |
|---|---|---|
| Pool (piscina) | Retângulo externo nomeado | Cada organização/ator autônomo. Pools se comunicam **apenas** por fluxo de mensagem. |
| Lane (raia) | Subdivisão interna do pool | Papéis distintos dentro do mesmo ator. |
| Evento de início | Círculo de borda fina | Simples (sem marcador), de mensagem (envelope) ou de temporizador (relógio). |
| Evento intermediário | Círculo de borda dupla | De mensagem (envio/recebimento) ou de temporizador. |
| Evento de borda | Círculo na borda de uma atividade | Interrompe (borda contínua) a atividade quando disparado. |
| Evento de fim | Círculo de borda grossa | Cada desfecho possível recebe um evento de fim próprio. |
| Tarefa de usuário | Retângulo arredondado, marcador de pessoa | Executada por pessoa com apoio de sistema. |
| Tarefa manual | Retângulo arredondado, marcador de mão | Executada por pessoa sem apoio de sistema. |
| Tarefa de serviço | Retângulo arredondado, marcador de engrenagem | Executada automaticamente por sistema. |
| Tarefa de recebimento | Retângulo arredondado, marcador de envelope | A execução fica bloqueada até a chegada de uma mensagem. |
| Gateway exclusivo (XOR) | Losango com "X" | Escolha de um único caminho. |
| Gateway inclusivo (OR) | Losango com círculo | Um ou mais caminhos simultâneos. |
| Fluxo de sequência | Seta de linha contínua | Ordem de execução **dentro** de um mesmo pool. |
| Fluxo de mensagem | Seta de linha tracejada | Comunicação **entre** pools distintos. |
| Anotação de texto | Colchete com linha pontilhada | Observação analítica associada a um elemento. |

*Tabela 7 – Elementos BPMN 2.0 empregados*

> **Convenção de identificadores:** `E` = evento, `A` = atividade, `G` = gateway, `F` = fluxo de sequência, `M` = fluxo de mensagem, `N` = anotação. A numeração é única dentro de cada processo.

---

### 3.2 Processo P01 — Planejar e Realizar Deslocamento por Ônibus (AS-IS)

> **Este diagrama abrange os processos P01, P02 e P03** (planejar o deslocamento, consultar a situação da linha e aguardar/embarcar na parada) — modelados como um único fluxo por serem sequenciais e do mesmo ator (o passageiro). O processo **P05** (execução da viagem pela operadora) também aparece, no pool "Empresa operadora", como contexto paralelo — não é o foco da modelagem, mas o fluxo depende dele. **P04 não está neste diagrama** — é modelado separadamente na seção 3.3.

#### 3.2.1 Ficha do processo

| Atributo | Descrição |
|---|---|
| **Nome** | Planejar e realizar deslocamento por ônibus |
| **Classificação** | Primário (crítico) |
| **Objetivo** | Levar o passageiro da origem ao destino por transporte público coletivo, no menor tempo e com a maior previsibilidade possíveis. |
| **Dono do processo** | Passageiro (executor); a previsibilidade do resultado, porém, depende da empresa operadora e da SEMOB. |
| **Gatilho (evento inicial)** | Necessidade de deslocamento identificada pelo passageiro. |
| **Resultado esperado** | Passageiro no destino, dentro do tempo planejado. |
| **Resultados possíveis (AS-IS)** | (a) deslocamento concluído no tempo previsto; (b) concluído com atraso e custo adicional; (c) não realizado / compromisso perdido; (d) espera abandonada por insegurança. |
| **Fronteira inicial** | Decisão de se deslocar. |
| **Fronteira final** | Chegada ao destino ou desistência do deslocamento. |
| **Frequência** | Duas ou mais execuções por dia útil, por passageiro. |
| **Duração média (AS-IS)** | Tempo de viagem acrescido de 15 a 30 minutos de margem de segurança embutida pelo próprio passageiro. |

*Tabela 8 – Ficha do processo P01*

#### 3.2.2 Stakeholders envolvidos

| Stakeholder | Tipo | Papel no processo | Interesse / expectativa |
|---|---|---|---|
| **Passageiro** | Externo — primário | Executa o processo de ponta a ponta: planeja, consulta, espera, embarca e viaja. | Chegar ao destino no horário, com segurança e sem custo extra. |
| **Motorista** | Externo — primário | Executa o itinerário e realiza o embarque. | Cumprir a viagem programada dentro do tempo de ciclo. |
| **Centro de Controle Operacional (CCO) da operadora** | Externo — primário | Escala veículos e motoristas; decide cancelar ou remanejar viagens. | Manter a operação viável com os recursos disponíveis do dia. |
| **Empresa operadora** | Externo — primário | Presta o serviço de transporte sob concessão. | Cumprir o contrato minimizando custo operacional. |
| **SEMOB/GDF** | Externo — secundário | Define o quadro de horários, fiscaliza a execução e mantém os canais oficiais de informação. | Que o serviço seja prestado conforme programado. |
| **Canais digitais de informação** (aplicativo oficial, Google Maps, Moovit) | Externo — secundário | Intermediam a informação sobre linhas, itinerários e posições. | Entregar a consulta com o dado de que dispõem. |
| **Outros passageiros / redes sociais** | Externo — secundário | Fonte informal e não verificada de informação sobre a linha. | Ajudar e ser ajudado com informação de última hora. |
| **Empregadores e instituições de ensino** | Externo — terciário | Recebem o impacto do atraso do passageiro. | Pontualidade e assiduidade. |

*Tabela 9 – Stakeholders do processo P01*

#### 3.2.3 Recursos atuais utilizados

| Categoria | Recurso | Onde é utilizado no processo |
|---|---|---|
| **Humanos** | Passageiro | Todo o processo. |
| | Motorista | Execução do itinerário e embarque. |
| | Operador do CCO | Escala da frota e decisão de cancelamento. |
| | Outros passageiros na parada | Fonte informal de informação durante a espera. |
| **Tecnológicos** | Smartphone com plano de dados móveis | Consulta aos canais digitais durante todo o processo. |
| | Aplicativo oficial de transporte do DF (DF no Ponto) | Consulta de linha, itinerário e posição. |
| | Google Maps / Moovit | Consulta alternativa, baseada em horário programado. |
| | Aplicativos de mensagem e redes sociais (WhatsApp, X, grupos de bairro) | Verificação informal da situação da linha. |
| | Equipamento de GPS embarcado no veículo | Geração da posição do veículo (consumida pela operadora). |
| | Rádio e sistema de telemetria da operadora | Acompanhamento da operação pelo CCO. |
| | Sistema de bilhetagem eletrônica (validador e cartão) | Validação da passagem no embarque. |
| | Aplicativo de transporte por aplicativo / táxi | Alternativa acionada quando a espera se frustra. |
| **Físicos** | Parada de ônibus (abrigo, banco, sinalização) | Local da espera. |
| | Iluminação pública no entorno da parada | Condição de segurança da espera. |
| | Terminal rodoviário | Ponto de origem, destino ou baldeação. |
| | Veículo (ônibus) | Execução da viagem. |
| | Via pública e corredores de transporte | Percurso do itinerário. |
| | Quadro de horários afixado na parada ou no terminal | Consulta presencial da programação. |

*Tabela 10 – Recursos do processo P01*

#### 3.2.4 Estrutura do diagrama: pools e raias

| Pool | Tipo | Raias | Observação |
|---|---|---|---|
| **1. Passageiro** | Aberto (detalhado) | Raia única | Contém o fluxo principal do processo. |
| **2. Canais digitais de informação** | Aberto (detalhado) | Raia única | Representa, de forma consolidada, o aplicativo oficial e os aplicativos de terceiros. |
| **3. Empresa operadora** | Aberto (detalhado) | 3.1 Centro de Controle Operacional (CCO) · 3.2 Motorista | Duas raias, pois as decisões e a execução ocorrem em papéis distintos. |
| **4. Rede informal de passageiros** | Fechado (caixa-preta) | — | Modelado como pool fechado: o processo interno é desconhecido e não estruturado. Comunica-se somente por fluxo de mensagem. |

*Tabela 11 – Pools e raias do processo P01*

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/01-processos-as-is.bpmn` (recorte da parte referente a P01)]

#### 3.2.5 Elementos do diagrama

**Pool 1 — Passageiro**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E01 | Evento de início (simples) | Necessidade de deslocamento identificada |
| A01 | Tarefa de usuário | Definir origem, destino e horário de chegada desejado |
| A02 | Tarefa de usuário | Consultar linha, itinerário e horário nos canais digitais |
| E14 | Evento intermediário de mensagem (recebimento) | Receber resposta dos canais digitais |
| G01 | Gateway exclusivo (divergente) | A informação obtida é suficiente e confiável? |
| A03 | Tarefa manual | Perguntar em grupo de mensagens, rede social ou a outro passageiro |
| E15 | Evento intermediário de mensagem (recebimento) | Receber resposta da rede informal |
| A04 | Tarefa manual | Estimar o horário com base na experiência própria |
| G02 | Gateway exclusivo (convergente) | — (junção) |
| A05 | Tarefa de usuário | Escolher a linha e definir o horário de saída, com margem de segurança |
| A06 | Tarefa manual | Deslocar-se até a parada |
| A07 | Tarefa de recebimento | Aguardar a chegada do ônibus na parada |
| E02 | Evento de borda — temporizador (interruptivo, em A07) | Tempo de espera excede a margem prevista (≈ 15 min) |
| E03 | Evento de borda — condicional (interruptivo, em A07) | Percepção de risco ou insegurança na parada |
| A08 | Tarefa de usuário | Reconsultar o aplicativo e checar com outros passageiros na parada |
| E16 | Evento intermediário de mensagem (recebimento) | Receber resposta durante a espera (canal digital ou rede informal) |
| G03 | Gateway exclusivo (divergente) | Há confirmação de que o ônibus ainda virá? |
| G04 | Gateway exclusivo (divergente) | Qual alternativa adotar? |
| A09 | Tarefa manual | Contratar transporte por aplicativo ou táxi |
| A10 | Tarefa manual | Tentar outra linha ou outro itinerário |
| A11 | Tarefa de usuário | Avisar sobre o atraso ou a ausência (trabalho, escola, compromisso) |
| A12 | Tarefa manual | Deixar a parada e procurar local mais seguro |
| G05 | Gateway exclusivo (divergente) | O veículo atende (linha correta e com espaço)? |
| A13 | Tarefa manual | Embarcar e validar a passagem |
| A14 | Tarefa manual | Realizar a viagem até o destino |
| E04 | Evento de fim | Deslocamento concluído no tempo previsto |
| E05 | Evento de fim | Deslocamento concluído com atraso e custo adicional |
| E06 | Evento de fim | Deslocamento não realizado — compromisso perdido |
| E07 | Evento de fim | Espera abandonada por insegurança |

**Pool 2 — Canais digitais de informação**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E08 | Evento de início de mensagem | Consulta do passageiro recebida |
| A15 | Tarefa de serviço | Consultar posição de GPS e horário programado da linha na base cadastral |
| E09 | Evento de fim de mensagem | Resposta devolvida ao passageiro (posição real, se houver, ou apenas horário programado) |

> **Nota de modelagem (Pool 2):** o roteamento interno do canal digital (existência ou não de posição de GPS recente) não é detalhado como gateway, pois não é uma decisão do canal, e sim um atributo do dado que ele consulta — resultado incorporado como uma variação da própria resposta enviada em E09. Detalhar esse roteamento internamente infla o diagrama sem acrescentar entendimento sobre a disfunção central do processo (N01), que está no dado em si, não no canal.

**Pool 3 — Empresa operadora**

| ID | Raia | Tipo BPMN | Rótulo |
|---|---|---|---|
| E10 | CCO | Evento de início de temporizador | Início da programação diária de operação |
| A19 | CCO | Tarefa de usuário | Escalar veículos e motoristas conforme o quadro de horários |
| G08 | CCO | Gateway exclusivo (divergente) | Há veículo e motorista disponíveis para a viagem? |
| A20 | CCO | Tarefa de usuário | Cancelar ou remanejar a viagem |
| E11 | CCO | Evento de fim | Viagem não realizada |
| A21 | CCO | Tarefa de usuário | Registrar a viagem realizada e encerrar a operação do dia |
| E12 | CCO | Evento de fim | Viagem concluída e operação do dia encerrada |
| A22 | Motorista | Tarefa manual | Executar o itinerário da linha |
| E13 | Motorista | Evento intermediário de mensagem (envio) | Chegada do veículo à parada |
| A23 | Motorista | Tarefa manual | Realizar embarque e desembarque |
| G09 | Motorista | Gateway exclusivo (divergente) | Fim do itinerário? |

**Pool 4 — Rede informal de passageiros** — pool fechado, sem elementos internos.

#### 3.2.6 Fluxos de sequência

| ID | Origem → Destino | Condição / rótulo |
|---|---|---|
| F01 | E01 → A01 | — |
| F02 | A01 → A02 | — |
| F03 | A02 → E14 | — |
| F47 | E14 → G01 | — |
| F04 | G01 → G02 | Sim — informação suficiente |
| F05 | G01 → A03 | Não — dado ausente, genérico ou desatualizado |
| F06 | A03 → E15 | — |
| F49 | E15 → A04 | — |
| F07 | A04 → G02 | — |
| F08 | G02 → A05 | — |
| F09 | A05 → A06 | — |
| F10 | A06 → A07 | — |
| F11 | A07 → G05 | Ônibus chegou à parada |
| F12 | E02 → A08 | Espera excedida |
| F13 | A08 → E16 | — |
| F48 | E16 → G03 | — |
| F14 | G03 → A07 | Sim — há indício de que o ônibus virá (retorna à espera) |
| F15 | G03 → G04 | Não — permanece a incerteza |
| F16 | G04 → A09 | Pagar transporte alternativo |
| F17 | G04 → A10 | Tentar outra linha |
| F18 | G04 → A11 | Desistir do deslocamento |
| F19 | A09 → E05 | — |
| F20 | A10 → A05 | Retorna ao replanejamento |
| F21 | A11 → E06 | — |
| F22 | E03 → A12 | Risco percebido |
| F23 | A12 → E07 | — |
| F24 | G05 → A13 | Sim |
| F25 | G05 → A07 | Não — veículo lotado ou linha diferente (retorna à espera) |
| F26 | A13 → A14 | — |
| F27 | A14 → E04 | — |
| F28 | E08 → A15 | — |
| F35 | A15 → E09 | — |
| F36 | E10 → A19 | — |
| F37 | A19 → G08 | — |
| F38 | G08 → A22 | Sim |
| F39 | G08 → A20 | Não |
| F40 | A20 → E11 | — |
| F41 | A22 → E13 | — |
| F42 | E13 → A23 | — |
| F43 | A23 → G09 | — |
| F44 | G09 → A22 | Não — segue para a próxima parada |
| F45 | G09 → A21 | Sim — itinerário concluído |
| F46 | A21 → E12 | — |

*Tabela 12 – Fluxos de sequência do processo P01*

> **Nota de modelagem (F45):** o fluxo entre a raia do Motorista e a raia do CCO é um fluxo de sequência, e não de mensagem, porque as duas raias pertencem ao mesmo pool (Empresa operadora). Fluxo de mensagem só é admitido entre pools distintos.

#### 3.2.7 Fluxos de mensagem entre pools

| ID | Origem → Destino | Conteúdo |
|---|---|---|
| M01 | A02 (Passageiro) → E08 (Canais digitais) | Consulta de linha, itinerário e horário |
| M02 | E09 (Canais digitais) → E14 (Passageiro) | Posição estimada ou apenas horário programado |
| M03 | A03 (Passageiro) → Pool 4 (Rede informal) | Pergunta sobre a situação da linha |
| M04 | Pool 4 (Rede informal) → E15 (Passageiro) | Resposta de outro passageiro, não verificada |
| M05 | E13 (Motorista) → A07 (Passageiro) | Chegada do veículo à parada |
| M06 | A08 (Passageiro) → E08 (Canais digitais) | Nova consulta durante a espera |
| M07 | Pool 4 (Rede informal) → E16 (Passageiro) | Informação informal de outros passageiros |

*Tabela 13 – Fluxos de mensagem do processo P01*

> **Nota de modelagem (M02, M04, M07 e E14/E15/E16):** em BPMN 2.0, um fluxo de mensagem só pode terminar em um evento de captura de mensagem ou em uma tarefa de recebimento — nunca diretamente em uma tarefa de usuário ou manual. Na versão anterior deste documento, M02, M04 e M07 chegavam respectivamente em A02, A03 e A08, o que violava essa regra. A correção introduz os eventos intermediários de captura E14, E15 e E16, cada um imediatamente após a tarefa que envia a consulta correspondente (A02, A03 e A08), preservando a mesma lógica de negócio sem violar a notação.

#### 3.2.8 Narrativa do fluxo

**Caminho principal (feliz).** O passageiro identifica a necessidade de se deslocar (E01) e define origem, destino e horário de chegada desejado (A01). Consulta os canais digitais (A02) e aguarda a resposta (E14), que os canais preparam consultando a base cadastral e a última posição de GPS conhecida (A15) — a resposta traz a posição real, se houver, ou apenas o horário programado, quando não há posição recente (E09). Com informação considerada suficiente (G01 = Sim), o passageiro escolhe a linha e define a hora de sair de casa, sempre acrescentando uma margem de segurança (A05). Desloca-se até a parada (A06) e aguarda (A07). Em paralelo, a operadora iniciou a programação diária (E10), escalou veículos e motoristas (A19) e, havendo recursos (G08 = Sim), o motorista executa o itinerário (A22) e chega à parada (E13, que envia M05). O passageiro verifica que o veículo atende (G05 = Sim), embarca e valida a passagem (A13), realiza a viagem (A14) e chega ao destino (E04).

**Primeiro desvio — informação insuficiente.** Quando a resposta recebida (E14) não traz posição de GPS recente, apenas o horário programado, o passageiro considera a informação insuficiente (G01 = Não) e recorre à rede informal (A03, com M03, aguardando a resposta em E15) ou estima o horário com base na própria experiência (A04). É aqui que a assimetria de informação se converte em trabalho manual do passageiro.

**Segundo desvio — a espera se frustra.** Se o tempo de espera excede a margem prevista, o evento de borda E02 interrompe a espera. O passageiro reconsulta o aplicativo e pergunta a outros passageiros na parada (A08), aguardando a resposta em E16. Se há confirmação de que o ônibus virá (G03 = Sim), retorna à espera (F14); caso contrário, escolhe uma alternativa (G04): pagar transporte por aplicativo, com custo não planejado (A09 → E05); tentar outra linha, retornando ao replanejamento (A10 → A05); ou desistir e avisar sobre o atraso (A11 → E06). **Este é o desvio que caracteriza o "ônibus fantasma" na perspectiva do passageiro.**

**Terceiro desvio — insegurança.** A qualquer momento durante a espera, a percepção de risco (E03) pode interromper o processo: o passageiro deixa a parada (A12) e o deslocamento não se realiza (E07). O gatilho não é o tempo em si, mas a combinação de espera prolongada, isolamento e ausência de informação sobre quando a espera terminará.

**Desvio na operadora — a causa raiz.** Quando não há veículo ou motorista disponível (G08 = Não), o CCO cancela ou remaneja a viagem (A20) e o processo se encerra em E11. **Não existe, nesse ponto, qualquer fluxo de mensagem em direção ao passageiro.** A informação de que a viagem não ocorrerá existe, é conhecida e está registrada — mas permanece dentro do pool da operadora. O passageiro continua esperando em A07 por um veículo que nunca sairá da garagem.

#### 3.2.9 Disfunções identificadas

| ID | Elemento ancorado | Disfunção | Efeito sobre o beneficiário |
|---|---|---|---|
| N01 | A15 / E09 | Dados de GPS frequentemente indisponíveis ou desatualizados; o canal exibe o horário programado como se fosse o horário real. | O passageiro planeja com base em uma promessa, não em um fato. |
| N02 | A03 / E15 | Informação da rede informal não é estruturada, georreferenciada nem validada; some do feed em minutos. | O esforço de um passageiro não beneficia o próximo. |
| N03 | A05 | Margem de segurança de 15 a 30 minutos embutida pelo próprio passageiro em cada trajeto. | Perda direta e diária de produtividade e de tempo de descanso. |
| N04 | A07 / E03 | A espera é o ponto de maior exposição: o passageiro permanece imóvel, em local previsível, sem saber por quanto tempo ainda ficará ali. | Risco de segurança física e desgaste psicológico. |
| N05 | A20 / E11 | O cancelamento da viagem é decidido e registrado internamente, mas nenhum fluxo de mensagem informa quem está na parada. | Causa raiz do "ônibus fantasma": a informação existe, mas não circula. |
| N06 | E13 / M05 | A posição do veículo é conhecida pela operadora em tempo real, porém só chega ao passageiro quando o ônibus aparece fisicamente na parada. | A informação chega tarde demais para ser útil à decisão. |
| N07 | F14 / F25 | Dois laços de retorno à espera (ônibus ainda pode vir; veículo lotado ou de outra linha) sem qualquer novo dado que fundamente a decisão de continuar esperando. | Decisão repetida sob incerteza, sem melhora de informação a cada ciclo. |

*Tabela 14 – Disfunções do processo P01*

---

### 3.3 Processo P04 — Registrar e Tratar Ocorrência no Serviço (AS-IS)

#### 3.3.1 Ficha do processo

| Atributo | Descrição |
|---|---|
| **Nome** | Registrar e tratar ocorrência no serviço de transporte |
| **Classificação** | Primário (crítico) |
| **Objetivo** | Comunicar uma falha vivenciada no serviço e obter apuração, resposta e correção. |
| **Dono do processo** | Compartilhado: o passageiro inicia; a ouvidoria e a empresa operadora conduzem a apuração. Não há um dono único — o que, por si, já é uma disfunção. |
| **Gatilho (evento inicial)** | Ocorrência vivenciada durante o deslocamento: viagem não realizada, atraso relevante, superlotação, veículo em más condições ou situação de insegurança. |
| **Resultado esperado** | Ocorrência registrada, apurada, respondida e corrigida. |
| **Resultados possíveis (AS-IS)** | (a) ocorrência não registrada; (b) registrada e respondida com solução; (c) registrada e respondida sem solução efetiva; (d) registrada sem retorno dentro do prazo. |
| **Fronteira inicial** | Percepção da falha pelo passageiro. |
| **Fronteira final** | Recebimento da resposta, esgotamento do prazo ou desistência do registro. |
| **Frequência** | Baixa em relação à ocorrência real dos fatos — a maior parte das falhas nunca é registrada. |
| **Duração média (AS-IS)** | De dias a 30 dias, prorrogáveis por igual período (Lei nº 13.460/2017, art. 16). |

*Tabela 15 – Ficha do processo P04*

#### 3.3.2 Stakeholders envolvidos

| Stakeholder | Tipo | Papel no processo | Interesse / expectativa |
|---|---|---|---|
| **Passageiro reclamante** | Externo — primário | Identifica a ocorrência, decide se registra e escolhe o canal. | Ser ouvido, obter explicação e ver a falha corrigida. |
| **Demais passageiros da mesma linha** | Externo — primário | Vivenciam a mesma ocorrência, mas em geral não a registram. | Não repetir a experiência no dia seguinte. |
| **Atendente da ouvidoria (1º nível)** | Externo — primário | Registra, classifica e encaminha a manifestação. | Cumprir o prazo legal de resposta. |
| **Área técnica da SEMOB** | Externo — primário | Apura a ocorrência junto à operadora e elabora a resposta técnica. | Fundamentar a resposta e subsidiar a fiscalização. |
| **SAC / área de operação da empresa operadora** | Externo — primário | Apura internamente e responde. | Encerrar a demanda com o menor impacto contratual. |
| **Motorista envolvido** | Externo — secundário | É ouvido durante a apuração interna. | Não ser penalizado indevidamente. |
| **Órgãos de controle (CGDF)** | Externo — secundário | Consolidam as manifestações em indicadores públicos. | Transparência e melhoria do serviço. |
| **Redes sociais e grupos de mensagem** | Externo — secundário | Canal informal de denúncia e de alerta entre passageiros. | Repercussão imediata. |

*Tabela 16 – Stakeholders do processo P04*

#### 3.3.3 Recursos atuais utilizados

| Categoria | Recurso | Onde é utilizado no processo |
|---|---|---|
| **Humanos** | Passageiro reclamante | Identificação, registro e acompanhamento da manifestação. |
| | Atendente da ouvidoria | Registro, classificação e encaminhamento. |
| | Analista técnico da SEMOB | Apuração e elaboração da resposta. |
| | Atendente de SAC da operadora | Apuração interna e resposta. |
| | Motorista e equipe de operação | Fonte de informação na apuração interna. |
| **Tecnológicos** | Portal e canal telefônico de ouvidoria do GDF | Registro formal da manifestação. |
| | Sistema de gestão de manifestações | Protocolo, classificação, prazo e resposta. |
| | Canal de SAC da empresa operadora (telefone, e-mail, site) | Registro direto junto ao prestador. |
| | Redes sociais e aplicativos de mensagem | Registro informal e alerta entre passageiros. |
| | Sistema de telemetria e escala da operadora | Evidência na apuração interna. |
| | Smartphone do passageiro (câmera, relógio, GPS) | Coleta informal de evidências. |
| | Planilhas e relatórios de indicadores | Consolidação das manifestações (processo G03). |
| **Físicos** | Parada, terminal ou veículo onde a ocorrência aconteceu | Local do fato a ser descrito na manifestação. |
| | Postos de atendimento presencial | Canal alternativo de registro. |
| | Documentos e protocolos impressos | Comprovação do registro. |

*Tabela 17 – Recursos do processo P04*

#### 3.3.4 Estrutura do diagrama: pools e raias

| Pool | Tipo | Raias | Observação |
|---|---|---|---|
| **1. Passageiro** | Aberto (detalhado) | Raia única | Contém o fluxo principal do processo. |
| **2. Ouvidoria do GDF** | Aberto (detalhado) | 2.1 Atendimento (1º nível) · 2.2 Área técnica (SEMOB) | A triagem e a apuração técnica ocorrem em papéis distintos. |
| **3. Empresa operadora** | Aberto (detalhado) | Raia única (SAC e área de operação) | Recebe demandas por dois caminhos: direto do passageiro e via ouvidoria. |
| **4. Outros passageiros / redes sociais** | Fechado (caixa-preta) | — | Processo interno não estruturado; comunica-se somente por fluxo de mensagem. |

*Tabela 18 – Pools e raias do processo P04*

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/01-processos-as-is.bpmn` (recorte da parte referente a P04; é o mesmo arquivo combinado com P01)]

#### 3.3.5 Elementos do diagrama

**Pool 1 — Passageiro**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E01 | Evento de início (simples) | Ocorrência vivenciada durante o deslocamento |
| A01 | Tarefa de usuário | Identificar o tipo de ocorrência (viagem não realizada, atraso, superlotação, veículo irregular, insegurança) |
| A02 | Tarefa manual | Reunir os dados da ocorrência (linha, sentido, horário, local e evidências) |
| G01 | Gateway exclusivo (divergente) | O esforço de registrar compensa? |
| A03 | Tarefa manual | Relatar informalmente a conhecidos e não registrar |
| E02 | Evento de fim | Ocorrência não registrada — informação perdida |
| G02 | Gateway inclusivo (divergente) | Quais canais acionar? |
| A04 | Tarefa de usuário | Registrar manifestação no canal de ouvidoria (portal ou telefone) |
| A05 | Tarefa de usuário | Publicar a ocorrência em rede social ou grupo de mensagens |
| A06 | Tarefa de usuário | Acionar o SAC da empresa operadora |
| G03 | Gateway inclusivo (convergente) | — (junção) |
| G04 | Gateway baseado em eventos | Aguardar retorno |
| E03 | Evento intermediário de mensagem (recebimento) | Resposta recebida |
| E04 | Evento intermediário de temporizador | Prazo esgotado sem retorno |
| E05 | Evento de fim | Sem retorno — percepção de canal inefetivo |
| A07 | Tarefa de usuário | Analisar a resposta recebida |
| G05 | Gateway exclusivo (divergente) | A resposta resolve ou explica o problema? |
| E06 | Evento de fim | Manifestação encerrada com resposta satisfatória |
| E07 | Evento de fim | Resposta recebida sem solução efetiva |

**Pool 2 — Ouvidoria do GDF**

| ID | Raia | Tipo BPMN | Rótulo |
|---|---|---|---|
| E08 | Atendimento | Evento de início de mensagem | Manifestação recebida |
| A08 | Atendimento | Tarefa de usuário | Registrar e classificar a manifestação (reclamação, denúncia, solicitação) |
| A09 | Atendimento | Tarefa de usuário | Encaminhar a manifestação à área responsável |
| A10 | Área técnica | Tarefa de usuário | Solicitar apuração à empresa operadora |
| A11 | Área técnica | Tarefa de recebimento | Aguardar o retorno da apuração |
| A12 | Área técnica | Tarefa de usuário | Elaborar a resposta técnica |
| A13 | Atendimento | Tarefa de usuário | Consolidar e enviar a resposta ao cidadão |
| E09 | Atendimento | Evento de fim | Manifestação respondida e arquivada |

**Pool 3 — Empresa operadora**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E10 | Evento de início de mensagem | Demanda recebida (SAC do passageiro ou solicitação da ouvidoria) |
| A14 | Tarefa de usuário | Apurar internamente (escala do dia, telemetria, relato do motorista) |
| G06 | Gateway exclusivo (divergente) | A ocorrência procede? |
| A15 | Tarefa de usuário | Adotar ação corretiva (reprogramação, orientação, manutenção) |
| A16 | Tarefa de usuário | Elaborar justificativa |
| G07 | Gateway exclusivo (convergente) | — (junção) |
| A17 | Tarefa de usuário | Responder ao solicitante |
| E11 | Evento de fim | Demanda encerrada na operadora |

**Pool 4 — Outros passageiros / redes sociais** — pool fechado, sem elementos internos.

#### 3.3.6 Fluxos de sequência

| ID | Origem → Destino | Condição / rótulo |
|---|---|---|
| F01 | E01 → A01 | — |
| F02 | A01 → A02 | — |
| F03 | A02 → G01 | — |
| F04 | G01 → A03 | Não — o esforço supera o retorno esperado |
| F05 | A03 → E02 | — |
| F06 | G01 → G02 | Sim |
| F07 | G02 → A04 | Canal oficial de ouvidoria |
| F08 | G02 → A05 | Rede social ou grupo de mensagens |
| F09 | G02 → A06 | SAC da empresa operadora |
| F10 | A04 → G03 | — |
| F11 | A05 → G03 | — |
| F12 | A06 → G03 | — |
| F13 | G03 → G04 | — |
| F14 | G04 → E03 | Resposta chegou |
| F15 | G04 → E04 | Prazo esgotado |
| F16 | E04 → E05 | — |
| F17 | E03 → A07 | — |
| F18 | A07 → G05 | — |
| F19 | G05 → E06 | Sim |
| F20 | G05 → E07 | Não |
| F21 | E08 → A08 | — |
| F22 | A08 → A09 | — |
| F23 | A09 → A10 | — |
| F24 | A10 → A11 | — |
| F25 | A11 → A12 | — |
| F26 | A12 → A13 | — |
| F27 | A13 → E09 | — |
| F28 | E10 → A14 | — |
| F29 | A14 → G06 | — |
| F30 | G06 → A15 | Sim |
| F31 | G06 → A16 | Não |
| F32 | A15 → G07 | — |
| F33 | A16 → G07 | — |
| F34 | G07 → A17 | — |
| F35 | A17 → E11 | — |

*Tabela 19 – Fluxos de sequência do processo P04*

> **Nota de modelagem (G02 e G03):** o gateway é **inclusivo**, e não exclusivo, porque é comum o passageiro acionar mais de um canal para a mesma ocorrência — por exemplo, publicar na rede social e registrar na ouvidoria. A junção em G03 deve ser igualmente inclusiva, aguardando a conclusão de todos os caminhos ativados.

#### 3.3.7 Fluxos de mensagem entre pools

| ID | Origem → Destino | Conteúdo |
|---|---|---|
| M01 | A04 (Passageiro) → E08 (Ouvidoria) | Manifestação do cidadão |
| M02 | A05 (Passageiro) → Pool 4 (Redes sociais) | Publicação sobre a ocorrência |
| M03 | A06 (Passageiro) → E10 (Operadora) | Chamado registrado no SAC |
| M04 | A10 (Ouvidoria) → E10 (Operadora) | Solicitação de apuração |
| M05 | A17 (Operadora) → A11 (Ouvidoria) | Retorno da apuração |
| M06 | A13 (Ouvidoria) → E03 (Passageiro) | Resposta oficial ao cidadão |
| M07 | A17 (Operadora) → E03 (Passageiro) | Resposta do SAC |
| M08 | Pool 4 (Redes sociais) → E03 (Passageiro) | Comentários e confirmações não verificadas |

*Tabela 20 – Fluxos de mensagem do processo P04*

> **Nota de modelagem (M06, M07, M08 e E03):** os três fluxos de mensagem convergem intencionalmente no mesmo evento de captura E03, em vez de cada um ter um evento de captura próprio após um gateway baseado em eventos com três ramos. Do ponto de vista do passageiro, o que importa nesse ponto é "alguma resposta chegou" — a origem (ouvidoria, SAC da operadora ou rede informal) não muda a ação seguinte (A07, analisar a resposta). Modelar três ramos de captura distintos aumentaria a complexidade do diagrama sem mudar o comportamento do processo; por isso, assim como em G02/G03 (nota da seção 3.3.6), trata-se de uma simplificação deliberada, e não de uma omissão.

#### 3.3.8 Narrativa do fluxo

**Decisão inicial — registrar ou não.** A ocorrência acontece (E01) e o passageiro a identifica (A01) e reúne os dados de que se lembra: linha, sentido, horário e local (A02). Em seguida, avalia se vale a pena registrar (G01). Essa avaliação compara um esforço concreto e imediato — abrir o portal, preencher formulário, descrever o fato — com um retorno abstrato e distante, que virá em semanas e provavelmente não mudará a viagem de amanhã. **Na maioria absoluta dos casos, o processo termina aqui, em E02.**

**Escolha dos canais.** Decidindo registrar (G01 = Sim), o passageiro aciona um ou mais canais em paralelo (G02, inclusivo): a ouvidoria do GDF (A04), a rede social ou grupo de mensagens (A05) e o SAC da operadora (A06). São três canais que não se comunicam entre si e que produzem três registros independentes do mesmo fato.

**Tratamento na ouvidoria.** A manifestação é recebida (E08), registrada e classificada (A08) e encaminhada à área responsável (A09). A área técnica solicita apuração à operadora (A10, via M04), aguarda o retorno (A11), elabora a resposta técnica (A12) e a devolve ao cidadão (A13, via M06). O ciclo completo pode consumir até 30 dias, prorrogáveis por igual período.

**Tratamento na operadora.** A operadora recebe a demanda por dois caminhos — direto do SAC (M03) ou por solicitação da ouvidoria (M04) — e apura internamente com base na escala do dia, na telemetria e no relato do motorista (A14). Se a ocorrência procede (G06 = Sim), adota ação corretiva (A15); caso contrário, elabora justificativa (A16). Em ambos os casos, responde (A17) e encerra a demanda (E11).

**Desfecho para o passageiro.** O passageiro aguarda em um gateway baseado em eventos (G04): ou chega uma resposta (E03) — da ouvidoria, do SAC ou de outros passageiros —, ou o prazo se esgota sem retorno (E04), encerrando o processo com a percepção de que o canal é inefetivo (E05). Havendo resposta, ele a analisa (A07) e o processo termina com a manifestação encerrada (E06) ou com uma resposta sem solução efetiva (E07).

**O que nenhum caminho faz.** Nenhuma das três rotas devolve informação ao passageiro que está, **naquele momento**, esperando na parada da mesma linha. O registro da ocorrência serve à prestação de contas posterior; não serve à decisão de quem está enfrentando o mesmo problema agora.

#### 3.3.9 Disfunções identificadas

| ID | Elemento ancorado | Disfunção | Efeito sobre o beneficiário |
|---|---|---|---|
| N01 | G01 / E02 | **Subnotificação estrutural:** o esforço percebido de registrar é alto e o retorno, distante e incerto. A maior parte das ocorrências nunca é registrada. | A base oficial de qualidade do serviço não reflete a realidade vivida na parada. |
| N02 | A02 / A04 | O registro é textual e depende da memória do passageiro; não há georreferenciamento nem vínculo automático com a linha e a viagem específicas. | Apuração frágil, sujeita a imprecisão e a contestação. |
| N03 | Pool 2 (Ouvidoria) | Ciclo de resposta de até 30 dias, prorrogáveis (Lei nº 13.460/2017, art. 16). | Serve à prestação de contas, não à decisão do passageiro em tempo real. |
| N04 | A05 / M02 / M08 | A rede social é rápida, mas a informação é dispersa, não validada, não georreferenciada e não persiste: some do feed em minutos. | O esforço do passageiro não se converte em conhecimento reutilizável. |
| N05 | E04 / E05 | A ausência de retorno dentro do prazo realimenta o ciclo: quem não recebe resposta não registra da próxima vez. | Ciclo vicioso que agrava a subnotificação (N01). |
| N06 | M04 / M05 / A14 | A apuração da ocorrência é delegada à própria empresa reclamada, que é simultaneamente parte e fonte da evidência. | Assimetria na apuração e baixa confiança do cidadão no resultado. |
| N07 | A08 / A14 | Não há validação cruzada entre manifestações: uma manifestação isolada não distingue um caso pontual de uma falha sistêmica da linha. | Falhas recorrentes só são detectadas quando o volume de reclamações se torna expressivo. |
| N08 | Processo inteiro | Não há um dono único do processo ponta a ponta; passageiro, ouvidoria e operadora executam partes sem visão do todo. | Ninguém é responsável pelo resultado percebido pelo cidadão. |

*Tabela 21 – Disfunções do processo P04*

---

### 3.4 TO-BE com o Movecity — o processo com o sistema entregue

#### 3.4.1 O que este TO-BE é (e o que não é)

A Etapa 2 do trabalho prometia o processo com o Movecity no fluxo. Esta seção o entrega com uma regra de rigor: **só entra no diagrama o que existe no produto em 28/10/2026** (mergeado em `homolog` ou `main`, seção 1.4). Não é um cenário especulativo de melhoria: é o mesmo processo de negócio de 3.2 e 3.3, com o Movecity ocupando o lugar dos canais fragmentados e da rede informal.

> **Correção em relação à versão 2.0.** A versão anterior desta seção (então chamada "AS-IS do Movecity") e o diagrama `02-processo-com-movecity.bpmn` descreviam três mecanismos que **não existem** no produto: (1) a posição do ônibus informada ao vivo por um passageiro a bordo, com prioridade sobre o GPS da SEMOB (a issue #199 segue aberta); (2) a notificação do cancelamento da viagem pelo centro de controle da operadora ao Movecity (não há integração com as operadoras); e (3) o alerta push proativo de cancelamento ao passageiro (issues #28 e #207 abertas). Os três foram retirados do diagrama e da narrativa, e o que ficou sem solução está na seção 3.5. A conferência foi feita contra o código de `homolog`, as issues e o registro de testes em `docs/qa/`.

#### 3.4.2 O mecanismo real do Movecity

O Movecity trabalha com duas fontes oficiais da SEMOB e uma localização do próprio usuário, e **rotula a origem de cada informação**:

1. **Cadastro da rede (linhas, trajetos, paradas e horários previstos):** copiado da SEMOB para o banco por ingestão em lote (workflow mensal do GitHub Actions); se a SEMOB sair do ar, a busca segue servindo o último snapshot (`docs/documento_arquitetura.md`, ADR-03 e seção 10.2).
2. **Posição dos ônibus:** lida ao vivo do feed da SEMOB, com cache de 20 s, e **nunca persistida** (ADR-04; `mobilidade/posicao_service.py`). A posição mostra a idade ("Posição de 2 min atrás", caso CT-ETA-01).
3. **Tempo estimado de chegada (ETA):** o serviço de chegadas devolve sempre a fonte: `ao_vivo` (há ônibus a caminho, calculado pela posição), `previsto` (sem ônibus a caminho: saída do terminal do dia mais o tempo de percurso) ou nenhuma, quando a tela mostra "Sem previsão no momento" em vez de um número sem origem (`mobilidade/chegada_service.py`, regra RN-10; PRs #184 e #185).
4. **Localização do usuário:** pedida ao navegador, usada para centrar o mapa, escolher a parada mais próxima, calcular o ETA e confirmar o embarque. A viagem é persistida **sem nenhuma coluna de posição** (ADR-15; caso CT-SEG-03).
5. **Reportes dos passageiros:** ocorrência estruturada (tipo, linha, descrição, local e, opcionalmente, coordenadas obtidas por botão) que os demais passageiros podem confirmar (`colaboracao/routes.py`).

Ao contrário do que a versão 2.0 afirmava, **não há fonte colaborativa de posição de ônibus**: a única fonte de posição é o feed da SEMOB. O reporte colaborativo existe como informação de ocorrência, não como substituto do GPS.

#### 3.4.3 Ficha do processo

| Atributo | Descrição |
|---|---|
| **Nome** | Planejar o deslocamento e registrar ocorrência com o Movecity |
| **Classificação** | Mesmos processos primários P01 e P04 (seção 2.3). Não é um processo novo no inventário: é o **mesmo processo de negócio**, com o Movecity no papel que hoje é dos canais fragmentados e da rede informal. |
| **Objetivo** | Dar ao passageiro, em um único ponto, a posição do ônibus, o ETA com a fonte declarada, o planejamento de rota e as ocorrências reportadas por outros passageiros, tratando as disfunções D1, D2, D3, D5, D6, D7, D8 e D9 (Tabela 33) na medida em que o produto entregue permite (seção 3.5). |
| **Diferença central em relação ao AS-IS manual** | O passageiro deixa de decidir às cegas: consulta um canal único que diz se o dado é "ao vivo", "previsto" ou inexistente, e pode reconsultar durante a espera. **O elo que falta continua faltando:** o cancelamento decidido pelo centro de controle (`op_A20`) segue sem mensagem ao passageiro, porque não há integração com a operadora. |
| **Fronteiras** | Mesmas de P01 e P04 (seções 3.2.1 e 3.3.1). Muda o meio, não o início nem o fim da jornada. |

*Tabela 22 – Ficha do processo TO-BE com o Movecity*

#### 3.4.4 Estrutura do diagrama: pools e raias

| Pool | Tipo | Raias | Observação |
|---|---|---|---|
| **1. Passageiro** | Aberto | Raia única | Mesmo pool de 3.2 e 3.3, com as tarefas de consulta substituídas por interação com o app. |
| **2. Movecity** | Aberto | App · Backend (Gateway + serviços) | Substitui os pools "Canais digitais" e, em parte, "Rede informal" do AS-IS manual. |
| **3. Empresa operadora** | Aberto | CCO · Motorista · SAC | **Sem alteração em relação ao AS-IS manual.** Não há fluxo de mensagem do CCO para o Movecity. |
| **4. Ouvidoria do GDF** | Aberto | Atendimento · Área técnica | **Mantida sem alteração**: o ciclo formal de até 30 dias (Lei 13.460/2017) segue existindo em paralelo; o Movecity não substitui a obrigação legal de resposta. |

*Tabela 23 – Pools e raias do processo TO-BE com o Movecity*

> **Este diagrama abrange os processos P01 a P04** — a jornada do passageiro (P01, P02, P03) e o reporte de ocorrência (P04), sob o mesmo sistema. **P05** continua aparecendo como contexto paralelo do lado da operadora.

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/02-processo-com-movecity.bpmn`]

#### 3.4.5 Elementos do diagrama que mudam em relação ao AS-IS

**Pool 1 — Passageiro** (os demais elementos são os de 3.2.5)

| ID | Tipo BPMN | Rótulo | Observação |
|---|---|---|---|
| p1_A02 | Tarefa de usuário | Consultar o Movecity | Busca de linha, parada ou rota |
| p1_E14 | Evento intermediário de mensagem (recebimento) | Receber resposta do Movecity (ao vivo, previsto ou sem previsão) | Substitui E14 do AS-IS; a resposta nunca é o horário programado disfarçado de real |
| p1_A07 | Tarefa de recebimento | Aguardar chegada do ônibus (acompanhando o ETA no Movecity) | |
| p1_E18 | Evento de borda — temporizador (interruptivo, em A07) | Espera acima da margem prevista | **Corrigido na versão 3.0:** era um evento de mensagem (alerta proativo), que não existe |
| p1_A08b | Tarefa de usuário | Reconsultar ETA e ocorrências no Movecity | Reconsulta manual, mas com dado atualizado |
| p1_E16 | Evento intermediário de mensagem (recebimento) | Receber resposta atualizada do Movecity | **Novo na versão 3.0:** captura a resposta da reconsulta |
| p1_A10 | Tarefa manual | Tentar outra linha ou rota (opções do planejador do Movecity) | O planejador devolve várias opções, inclusive com baldeação |
| p1_A13 / p1_A14 | Tarefas manuais | Embarcar e tocar em "Peguei este ônibus"; realizar a viagem com a faixa "Em viagem" e o aviso de proximidade da parada de destino | Recursos das issues #171 e #172 |
| p4_A01 | Tarefa de usuário | Abrir Reportar no Movecity (linha, tipo e local; localização por botão, opcional) | Substitui a escolha entre três canais isolados |

**Pool 2 — Movecity**

| ID | Raia | Tipo BPMN | Rótulo |
|---|---|---|---|
| mv_E00 | App | Evento de início de mensagem | Passageiro abre o app |
| mv_A00 | App | Tarefa de serviço | Capturar localização atual do usuário (GPS do celular) |
| mv_E08 | App | Evento de início de mensagem | Consulta de linha recebida |
| mv_A15 | App | Tarefa de serviço | Calcular o ETA, rotular a fonte (ao vivo, previsto ou sem previsão) e exibir no mapa |
| mv_E09 | App | Evento de fim de mensagem | Resposta enviada (com o selo da fonte) |
| mv_G_pos | Backend | Gateway exclusivo | Há ônibus da linha com posição recente no feed da SEMOB? |
| mv_A_aovivo | Backend | Tarefa de serviço | Calcular o ETA pela posição ao vivo (cache de 20 s, não persistida): selo "ao vivo" |
| mv_A_previsto | Backend | Tarefa de serviço | Usar a saída prevista do terminal (snapshot da SEMOB no banco) ou informar "sem previsão no momento" |
| mv_E20 | Backend | Evento de início de mensagem | Reporte de ocorrência recebido |
| mv_A27 | Backend | Tarefa de serviço | Registrar a ocorrência (até 3 por hora por usuário) e listá-la para a linha |
| mv_G10 | Backend | Gateway exclusivo | Outros passageiros confirmaram (3 confirmações)? |
| mv_A28 | Backend | Tarefa de serviço | Marcar a ocorrência como "Confirmada" |
| mv_E19 | Backend | Evento de fim | Ocorrência confirmada, visível na lista da linha até expirar (sem push) |
| mv_E21 | Backend | Evento de fim | Segue "Aguardando confirmação" até expirar (15 a 120 min conforme o tipo) |

**Pool 3 — Empresa operadora:** idêntico a 3.2.5, com uma anotação (`op_N01`) registrando que o cancelamento não chega ao Movecity (US #28 não entregue). O evento de fim `op_E11` passou a se chamar "Viagem não realizada (sem aviso ao passageiro: a lacuna D1 permanece)".

*Elementos removidos em relação à versão 2.0:* `mv_E17` (receber notificação de cancelamento da operadora), `mv_A26` (disparar alerta push), `op_A20b` (notificar o Movecity) e os fluxos de mensagem correspondentes.

#### 3.4.6 Fluxos de mensagem entre pools

| ID | Origem → Destino | Conteúdo |
|---|---|---|
| Mflow_0 | p1_A02 (Passageiro) → mv_E08 (Movecity) | Consulta de linha, parada ou rota |
| Mflow_1 | mv_E09 (Movecity) → p1_E14 (Passageiro) | Posição ao vivo, horário previsto ou "sem previsão", sempre com a fonte |
| Mflow_3 | p1_A08b (Passageiro) → mv_E08 (Movecity) | Nova consulta durante a espera |
| Mflow_2 | mv_E09 (Movecity) → p1_E16 (Passageiro) | Resposta atualizada (ETA e ocorrências) |
| Mflow_4 | op_E13 (Motorista) → p1_A07 (Passageiro) | Chegada física do veículo à parada (inalterado) |
| Mflow_5 | p4_A01 (Passageiro) → mv_E20 (Movecity) | Reporte da ocorrência |
| Mflow_7 a 10 | Passageiro, Ouvidoria e Operadora | Canal formal mantido, sem alteração (ouvidoria, SAC, apuração e retorno) |

*Tabela 24-A – Fluxos de mensagem do TO-BE com o Movecity*

> **Simplificação deliberada (P04).** A confirmação da ocorrência por outros passageiros não tem raia própria: ela entra no diagrama como a condição do gateway `mv_G10`. Do mesmo modo, a leitura da lista de ocorrências por quem está na linha acontece na tela do app e não é modelada como mensagem. Modelar cada passageiro adicional aumentaria o diagrama sem mudar o comportamento descrito.

#### 3.4.7 Narrativa do fluxo

**Caminho principal.** O passageiro identifica a necessidade de se deslocar (p1_E01) e define origem, destino e horário (p1_A01). Ao abrir o app, o Movecity captura a localização do aparelho (mv_E00, mv_A00). O passageiro consulta o Movecity (p1_A02, Mflow_0). No backend, o Movecity verifica se há ônibus da linha com posição recente no feed da SEMOB (mv_G_pos): havendo, calcula o ETA pela posição ao vivo, com o selo "ao vivo"; não havendo, usa a saída prevista do terminal gravada no banco, com o selo "previsto", ou informa "Sem previsão no momento". A resposta chega com a fonte declarada (mv_E09, Mflow_1). O passageiro escolhe a linha e o horário de saída (p1_A05), desloca-se (p1_A06) e aguarda acompanhando o ETA (p1_A07). Quando o veículo chega (op_E13, Mflow_4) e atende, embarca, toca em "Peguei este ônibus" e faz a viagem com a faixa "Em viagem" e o aviso de proximidade da parada de destino (p1_A13, p1_A14), concluindo no tempo previsto (p1_E04).

**Desvio — a espera se frustra.** Se a espera passa da margem prevista, o temporizador de borda (p1_E18) interrompe a espera. O passageiro reconsulta o ETA e as ocorrências da linha (p1_A08b, Mflow_3) e recebe a resposta atualizada (p1_E16, Mflow_2). A diferença para o AS-IS é que agora a reconsulta devolve um dado novo e com a fonte rotulada, em vez de uma pergunta sem resposta a outros passageiros. A decisão (pagar transporte alternativo, tentar outra linha ou rota, ou desistir) continua sendo do passageiro (p1_G04).

**Desvio — insegurança.** A percepção de risco (p1_E03) continua podendo interromper a espera. O Movecity não trata a causa (iluminação, abrigo, isolamento da parada): reduz, quando o ETA é confiável, a incerteza sobre quanto tempo ainda é preciso esperar.

**O que não mudou na operadora.** Quando não há veículo ou motorista disponível (op_G08 = Não), o centro de controle cancela ou remaneja a viagem (op_A20) e o processo encerra em op_E11. **Não existe mensagem para o Movecity nem para o passageiro.** O que o passageiro pode observar é indireto: a linha aparece sem ônibus em operação, com a próxima saída prevista do terminal (caso CT-MAP-08), ou o ônibus aparece sem previsão (caso CT-ETA-02). Isso é inferência do passageiro, não aviso de cancelamento.

**Reporte de ocorrência (P04).** O passageiro abre "Reportar" (p4_A01), informa linha, tipo e local, e pode usar a localização do aparelho por um botão. O Movecity registra a ocorrência, limita a 3 reportes por hora por usuário e a lista para os passageiros da linha (mv_A27). Os tipos "acidente" e "segurança" nascem já "Confirmada", para não ficarem represados; os demais (atraso, não passou, lotação, obra na via, ônibus quebrou) nascem "Aguardando confirmação" e passam a "Confirmada" quando **3 outros passageiros** a confirmam (mv_G10, mv_A28; o autor não confirma a própria ocorrência). Toda ocorrência, confirmada ou não, expira em 15 a 120 minutos conforme o tipo e deixa de aparecer na lista; o registro não é apagado e passa a constar como "expirada" (`colaboracao/routes.py` e `colaboracao/models/ocorrencia.py`; caso CT-COL-05). O passageiro **pode**, e continua podendo, acionar também a ouvidoria e o SAC (p4_G02): o canal formal permanece, em paralelo, para a prestação de contas legal.

#### 3.4.8 O que muda, processo a processo

| | **AS-IS manual (3.2 e 3.3)** | **TO-BE com o Movecity (3.4), como entregue** |
|---|---|---|
| Fonte de posição do ônibus | Canal escolhido no braço (DF no Ponto, Google Maps ou Moovit), sem indicar a origem do dado | Feed da SEMOB, lido ao vivo (cache de 20 s) e exibido com a idade da posição |
| Horário programado × real | O canal exibe o horário programado como se fosse o real | Cada tempo traz a fonte ("ao vivo" ou "previsto"); sem dado, "Sem previsão no momento" |
| Localização do usuário | Não é usada | Capturada no app; usada para o mapa, a parada mais próxima, o ETA e o embarque; não é gravada |
| Planejamento do trajeto | Consulta a vários canais e margem de 15 a 30 minutos | Planejador de rota com opções, inclusive com baldeação, e tempo do ônibus nas paradas de subir e descer; rota favorita |
| Durante a espera | Reconsulta manual e pergunta a outros passageiros | Reconsulta no mesmo canal, com dado atualizado; **sem alerta proativo** |
| Cancelamento da viagem (CCO) | Fica preso no pool da operadora | **Inalterado.** Não há integração com a operadora |
| Reporte de ocorrência | Três canais isolados (ouvidoria, redes sociais, SAC), nenhum devolve informação a quem espera agora | Reporte estruturado, listado por linha para os demais passageiros, com confirmação cruzada por 3 passageiros e expiração por tipo |
| Canal formal (ouvidoria e SAC) | Único caminho; ciclo de até 30 dias | **Mantido, sem alteração** |

*Tabela 24 – Comparativo processo a processo*

---

### 3.5 Quadro comparativo AS-IS × TO-BE por disfunção

O quadro liga cada uma das nove disfunções da síntese (Tabela 33, seção 6) à funcionalidade do Movecity que a trata, à evidência e ao que continua sem solução. A evidência é o caso de teste manual de `docs/qa/execucao-casos-p1.md` (execução em produção, 27 e 28/10/2026), quando existe. **Situação:** *Tratada* = a funcionalidade existe e foi verificada; *Em parte* = o produto trata um aspecto, e o restante está descrito na última coluna; *Não resolvida*.

| # | AS-IS (disfunção) | Funcionalidade do Movecity (issue / PR) | Evidência (caso de teste) | Situação | O que continua sem solução |
|---|---|---|---|---|---|
| **D1** | A posição e o cancelamento existem na operadora, mas não atravessam a fronteira do pool até o passageiro | **Posição:** ônibus em tempo real (#16, PRs #120 e #124), ETA (#19, #159 e #179, PRs #154, #160 e #185) e idade da posição. **Cancelamento:** nenhuma funcionalidade; a linha sem ônibus aparece com a próxima saída prevista do terminal | CT-MAP-07 e CT-ETA-01 (aprovados); CT-MAP-08 (aprovado); CT-ETA-02 (aprovado) | **Em parte** (só a posição) | O cancelamento decidido pelo CCO **não chega** ao passageiro: sem integração com a operadora e sem o alerta de cancelamento (#28 aberta). O passageiro só infere pela ausência de ônibus no feed. A versão 2.0 dava esta disfunção como resolvida; não está |
| **D2** | Os canais exibem o horário programado como se fosse o real | Fonte declarada em cada tempo ("ao vivo", "previsto" ou "Sem previsão no momento"); saída do terminal nunca apresentada como passagem na parada (#179, PRs #181 a #185; #173, PR #177) | CT-ETA-01, CT-ETA-02 e CT-PAR-04 (aprovados); CT-ETA-04 (aprovado em parte) | **Tratada** | A **precisão** do ETA não foi medida em campo: a tolerância proposta (2 min para ETA até 10 min) e a regra do ônibus chegando (#191) dependem de validação em campo. A qualidade do feed da SEMOB é externa ao projeto |
| **D3** | O passageiro compensa a incerteza com margem de 15 a 30 minutos e consultas manuais a fontes informais | Planejador de rota com baldeação (#20, PRs #116 e #119), paradas de subir e descer com o tempo do ônibus (#190, PR #193), busca de parada por nome ou endereço (#21, PR #197), rota favorita (#25, PR #176) | CT-ROT-01, CT-ROT-02 e CT-ROT-05 (aprovados); CT-ROT-06 (aprovado em parte: o embarque ainda não mostra o tempo em minutos) | **Em parte** (meio entregue, efeito não medido) | Não há medição de que a margem do passageiro tenha diminuído; isso exige teste com usuários reais, que não foi feito |
| **D4** | A espera na parada é o ponto de maior exposição a risco, sem previsão de término | ETA declarado na espera (acima); reporte imediato de ocorrência do tipo "segurança" (#23); aviso de proximidade da parada de destino durante a viagem (#172 e #195) | CT-COL-01 (aprovado); CT-VIA-08 (não verificável hoje, só em campo) | **Não resolvida** | Iluminação, abrigo e isolamento da parada são infraestrutura (processo S04), fora do alcance de um app. Reduzir o tempo de exposição por um ETA melhor é hipótese, não medida. O aviso de proximidade é para quem já está a bordo, não para quem espera |
| **D5** | A decisão de continuar esperando é tomada repetidamente sem dado novo | Mapa com posições que se atualizam sozinhas (#16) e reconsulta do ETA e das ocorrências no mesmo canal | CT-MAP-07 (aprovado); CT-ETA-03 (não executado: exige simulação de posição no navegador) | **Em parte** | **Não há alerta proativo entregue:** o alerta de atraso (#27) não tem canal de entrega e o push dos alertas (#207) não foi feito; o passageiro ainda precisa reconsultar por conta própria. A versão 2.0 dava esta disfunção como resolvida por push; não está |
| **D6** | A maior parte das ocorrências nunca é registrada | Reporte em poucos toques, com linha, tipo, local e localização por botão (#23, PR #162); limite de 3 reportes por hora por usuário (CT-COL-03) | CT-COL-01 e CT-COL-03 (aprovados) | **Em parte** (esforço reduzido, taxa de reporte não medida) | Não há medição da taxa de reporte nem uso por passageiros reais; a subnotificação não foi verificada. Quem não tem o app instalado continua fora do ciclo |
| **D7** | O ciclo de tratamento é medido em dias; a necessidade do passageiro, em minutos | Ocorrência listada na hora para os passageiros da linha (#24, PR #180), com selo "Confirmada" ou "Aguardando confirmação" e expiração por tipo | CT-COL-04 (aprovado em parte: o filtro por outra linha não foi comprovado); CT-COL-05 (aprovado) | **Em parte** (só entre passageiros) | O ciclo formal da ouvidoria segue em dias, sem alteração. Não há entrega ativa da ocorrência a quem está na parada: o passageiro precisa abrir a lista (sem push) |
| **D8** | A informação colaborativa existe nas redes sociais, mas é dispersa, não validada e não persistente | Ocorrência estruturada (tipo, linha, local, coordenadas opcionais), por linha, com confirmação cruzada (#26, PR #209) e registro mantido no banco; ver ocorrências de outros passageiros (#24) | CT-COL-01, CT-COL-04 (em parte), CT-COL-05 | **Tratada** (dentro da base de usuários do Movecity) | A confirmação por 3 passageiros (#26) tem código e testes automatizados, mas **nenhum caso manual executado** e a issue segue aberta. Só vale para quem usa o Movecity; o que circula em grupos de mensagem continua fora |
| **D9** | Não há dono do processo ponta a ponta nem validação cruzada entre relatos | Validação cruzada por 3 confirmações de outros passageiros (#26, PR #209), exceto "acidente" e "segurança", exibidos de imediato | Sem caso manual para a confirmação; CT-COL-04 mostra o selo "Aguardando confirmação" | **Em parte** | Continua **sem dono único** entre passageiro, ouvidoria, operadora e Movecity. O limiar real é 3 confirmações, e o Documento de Visão (v1.1) já registra 3, mas a tela de reporte ainda anuncia 2 (#249) |

*Tabela 25 – Quadro AS-IS × TO-BE por disfunção (estado em 28/10/2026)*

**Leitura do quadro.** Das nove disfunções, o Movecity entregue **trata duas** (D2 e D8), **trata em parte seis** (D1, D3, D5, D6, D7 e D9) e **não resolve uma** (D4). Isso é menos do que a versão 2.0 declarava (cinco "resolvidas"); a diferença vem de três mecanismos que o desenho previa e o produto não tem: o aviso de cancelamento, o alerta proativo por push e o fallback colaborativo de posição.

**Lacunas transversais que o quadro não fecha:**

1. **Entrega de alertas.** As preferências de notificação são salvas (#29), mas nenhum alerta de atraso, de cancelamento ou de rota preferida chega ao usuário. O único aviso com canal de entrega é o de proximidade da parada de destino, por Web Push, ainda sem validação em aparelho real (#200).
2. **Integração com a operadora.** Sem ela, a causa raiz do "ônibus fantasma" (cancelamento que não circula) permanece.
3. **Validação em campo e com usuários.** Nenhum efeito de processo (tempo de espera, margem de segurança, taxa de reporte) foi medido; os 49 casos manuais verificam funcionamento, não resultado de negócio. A avaliação de usabilidade foi feita por um avaliador (`docs/qa/avaliacao-usabilidade-nielsen.md`).
4. **Dono do processo.** Continua sem solução; é uma questão de governança entre instituições.

---

## 4. Processo de Desenvolvimento Assistido por Agentes de IA

> **Nota de escopo:** este processo é um **meta-processo interno do projeto** — descreve como o próprio time constrói o Movecity, e não como o cidadão se desloca ou reporta ocorrências. Por isso não entra no inventário de processos de mobilidade da seção 2 nem na matriz de criticidade da seção 2.4, que classificam exclusivamente a cadeia de valor do STPC/DF via BPM CBOK. Ele é modelado com a mesma notação BPMN 2.0 e a mesma estrutura de 9 subseções usada em P01 e P04, por coerência metodológica do documento.

### 4.1 Ficha do processo

| Atributo | Descrição |
|---|---|
| **Nome** | Desenvolver e entregar incremento de software com apoio de agentes de IA |
| **Classificação** | Processo de suporte interno ao projeto (não pertence à cadeia de valor do STPC/DF) |
| **Objetivo** | Transformar uma User Story do backlog em um incremento de software validado em produção, com um agente de IA (Claude Code / opencode) operando em nome do desenvolvedor responsável. |
| **Dono do processo** | O desenvolvedor responsável pela US. O agente de IA é recurso tecnológico usado por ele, nunca dono do processo. |
| **Gatilho (evento inicial)** | US selecionada no Sprint Planning, com os critérios DOR já atendidos. |
| **Resultado esperado** | Incremento entregue em produção, validado, com a issue fechada e a documentação atualizada (DoD-Release). |
| **Resultados possíveis (AS-IS)** | (a) entregue em homolog e, depois, em produção dentro do ciclo normal da sprint; (b) retrabalho solicitado no review formal; (c) CI falha e bloqueia o merge até correção; (d) bypass excepcional de proteção de branch, sempre registrado explicitamente na issue (caso raro — ex.: teste deliberado do próprio pipeline). |
| **Fronteira inicial** | Seleção da US no sprint planning, com DOR atendido. |
| **Fronteira final** | Issue fechada com o DoD-Release cumprido. |
| **Quem escreve o código** | Agentes de IA. Todo o código do Movecity foi gerado por agentes de IA (Claude Code, opencode e Gemini são as ferramentas com configuração no repositório; qual gerou cada trecho não é registrado, por regra de autoria), conduzidos por seis estudantes que especificaram, revisaram e aprovaram (seção 4.10). |
| **Frequência** | Regra do time: 1 US por desenvolvedor por sprint, para não sobrecarregar o revisor. Na prática, a autoria dos PRs ficou desigual entre os integrantes (seção 4.10). |
| **Duração média (AS-IS)** | Variável conforme a complexidade da US; a promoção de `homolog` para `main` ocorre em lote (por exemplo, os PRs #142, #163, #170 e #203). Não há medição do ciclo da US; a mediana da criação ao merge de um PR é de 17 min (`docs/guia-apresentacao.md`, 3.2). |

*Tabela 26 – Ficha do processo de desenvolvimento assistido por IA*

### 4.2 Stakeholders envolvidos

| Stakeholder | Tipo | Papel no processo | Interesse / expectativa |
|---|---|---|---|
| **Desenvolvedor responsável pela US** | Interno — primário | Conduz a sessão de desenvolvimento com o agente de IA, do planejamento ao merge; toma toda decisão que a IA não pode tomar sozinha. | Entregar a US corretamente, dentro da sprint, com rastreabilidade. |
| **Revisor (outro integrante do time)** | Interno — primário | Analisa o PR e submete a aprovação formal (botão "Review changes" → "Approve"). | Garantir qualidade e aderência ao padrão arquitetural antes do merge. |
| **Pipeline de CI/CD (GitHub Actions, Fly.io, Vercel)** | Interno — suporte automatizado | Roda lint de Conventional Commits, testes (pytest/Jest) e dispara o deploy automaticamente após o merge. | Bloquear merges com testes quebrados; manter homolog e produção sempre consistentes com o código aprovado. |
| **Orquestração do backlog** | Interno — secundário | Prioriza o backlog e garante que a US chegue à sprint já com DOR atendido. | Previsibilidade de entrega e escopo gerenciável por sprint. |
| **Professor orientador da disciplina / avaliador do TCC** | Externo — secundário | Avalia se o processo de desenvolvimento é rastreável e se a autoria do trabalho intelectual é do time. | Verificar que o uso de IA não substitui o julgamento humano nem a autoria acadêmica. |
| **Usuários finais do Movecity** | Externo — beneficiário indireto | Recebem o incremento em produção. | Sistema funcional, correto e confiável. |

*Tabela 27 – Stakeholders do processo de desenvolvimento assistido por IA*

### 4.3 Recursos atuais utilizados

| Categoria | Recurso | Onde é utilizado no processo |
|---|---|---|
| **Humanos** | Desenvolvedor responsável pela US | Todo o processo — toma toda decisão de merge, bypass e resolução de divergência. |
| | Revisor | Análise do PR e submissão do review formal. |
| **Tecnológicos** | Agente de IA (Claude Code / opencode) | Recurso usado pelo desenvolvedor para ler a US e o diagrama de sequência, planejar, codificar, testar localmente, commitar e abrir o PR — sempre em nome do desenvolvedor, nunca como autor. |
| | Repositório Git / GitHub (issues, PRs, branch protection) | Rastreamento de todo o ciclo, vínculo PR↔issue, aplicação das regras de aprovação obrigatória. |
| | GitHub Actions (CI) | Execução automática de lint, pytest e Jest a cada PR. |
| | Fly.io e Vercel (CD) | Deploy automático disparado pelo merge em `homolog` ou `main`. |
| | GitHub Projects | Card de sprint com checklist de desenvolvimento, review e deploy. |
| **Documentais** | Templates de US/PRD/SPEC e de card de sprint | Formalização da US antes do desenvolvimento (critério DOR). |
| | Diagrama de sequência da issue (`docs/diagramas/sequencia/`) | Spec técnica de execução, referência obrigatória antes de codificar (critério DOR). |
| | `docs/boas-praticas-ia.md`, `docs/guia-contribuicao.md`, `docs/manual-sprint.md` | Regras de governança do uso de IA, gitflow/commits e do ciclo completo, respectivamente. |

*Tabela 28 – Recursos do processo de desenvolvimento assistido por IA*

### 4.4 Estrutura do diagrama: pools e raias

| Pool | Tipo | Raias | Observação |
|---|---|---|---|
| **1. Desenvolvedor** | Aberto (detalhado) | Raia única | Planejamento e execução com apoio do agente de IA ocorrem na mesma raia — a IA é recurso usado dentro do papel do desenvolvedor, não um ator autônomo com raia própria (decisão de modelagem alinhada a `docs/boas-praticas-ia.md`: a IA é ferramenta, o humano decide e responde). |
| **2. Revisor** | Aberto (detalhado) | Raia única | Outro integrante do time, papel formal de aprovação. |
| **3. Pipeline CI/CD** | Aberto (detalhado) | Raia única | Pool de sistema — reage automaticamente a eventos do repositório, sem intervenção humana direta. |

*Tabela 29 – Pools e raias do processo de desenvolvimento assistido por IA*

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/03-processo-desenvolvimento-ia.bpmn`]

### 4.5 Elementos do diagrama

**Pool 1 — Desenvolvedor**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E01 | Evento de início (simples) | US selecionada no sprint planning (DOR atendido) |
| A01 | Tarefa de usuário | Ler a US, o PRD/SPEC e o diagrama de sequência da issue |
| A02 | Tarefa de usuário | Criar branch a partir de `homolog` (`feat`/`fix`) ou de `main` (`docs`/`chore`) |
| A03 | Tarefa de usuário | Desenvolver com apoio do agente de IA (planejar, codificar, testar localmente) |
| G01 | Gateway exclusivo (divergente) | Os testes locais passam? |
| A04 | Tarefa de usuário | Corrigir com o agente e retestar |
| A05 | Tarefa de usuário | Commit em Conventional Commits (sem atribuição de IA) e abrir PR vinculado à issue |
| E02 | Evento intermediário de mensagem (recebimento) | Receber o resultado do CI |
| G02 | Gateway exclusivo (divergente) | O CI passou? |
| A06 | Tarefa manual | Corrigir conforme a falha apontada pelo CI |
| E03 | Evento intermediário de mensagem (recebimento) | Receber a decisão do review |
| G03 | Gateway exclusivo (divergente) | Aprovação formal (botão "Review changes" → "Approve") foi recebida? |
| A07 | Tarefa manual | Ajustar conforme os comentários do review |
| G04 | Gateway exclusivo (divergente) | É um bypass excepcional e deliberado (ex.: teste do próprio pipeline)? |
| A08 | Tarefa de usuário | Registrar o bypass explicitamente na issue, com justificativa |
| A09 | Tarefa de usuário | Confirmar o merge em `homolog` (decisão sempre humana, nunca automática) |
| E04 | Evento intermediário de mensagem (recebimento) | Receber a confirmação de que o deploy em homolog foi concluído |
| A10 | Tarefa de usuário | Validar os critérios de aceite (BDD) em homolog |
| G05 | Gateway exclusivo (divergente) | Os critérios de aceite foram atendidos em homolog? |
| A11 | Tarefa manual | Retomar o desenvolvimento com o agente |
| A12 | Tarefa de usuário | Comentar o resultado na issue (DoD-Sprint) |
| E05 | Evento de fim | US concluída na sprint (DoD-Sprint) |
| A13 | Tarefa de usuário | Abrir PR `homolog → main` (em lote, ao final da sprint) |
| E06 | Evento intermediário de mensagem (recebimento) | Receber a aprovação formal do PR `homolog → main` |
| A14 | Tarefa de usuário | Confirmar o merge em `main` (decisão sempre humana) |
| E07 | Evento intermediário de mensagem (recebimento) | Receber a confirmação de que o deploy em produção foi concluído |
| A15 | Tarefa de usuário | Validar o endpoint/tela real em produção |
| G06 | Gateway exclusivo (divergente) | Validado em produção? |
| A16 | Tarefa manual | Investigar e corrigir com o agente |
| A17 | Tarefa de usuário | Fechar a issue e atualizar a documentação, se aplicável |
| E08 | Evento de fim | Incremento entregue em produção (DoD-Release) |

**Pool 2 — Revisor**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E09 | Evento de início de mensagem | PR recebido para revisão |
| A18 | Tarefa de usuário | Analisar as mudanças do PR (aba "Files changed") |
| G07 | Gateway exclusivo (divergente) | O código atende ao padrão e à US? |
| A19 | Tarefa de usuário | Comentar solicitando ajustes (comentário de texto — não conta como aprovação formal) |
| A20 | Tarefa de usuário | Submeter review formal (botão "Review changes" → "Approve") |
| E10 | Evento de fim de mensagem | Decisão de review enviada |

**Pool 3 — Pipeline CI/CD**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E11 | Evento de início de mensagem | PR aberto ou atualizado |
| A21 | Tarefa de serviço | Rodar lint de Conventional Commits, pytest e Jest |
| G08 | Gateway exclusivo (divergente) | Todos os testes passam? |
| E12 | Evento de fim de mensagem | Resultado do CI (verde) enviado |
| E12b | Evento de fim de mensagem | Resultado do CI (falha) enviado |
| E14 | Evento de início de mensagem | Merge realizado em `homolog` ou `main` |
| A22 | Tarefa de serviço | Disparar deploy automático (Fly.io para backend, Vercel para frontend) |
| E13 | Evento de fim de mensagem | Deploy concluído |

### 4.6 Fluxos de sequência

| ID | Origem → Destino | Condição / rótulo |
|---|---|---|
| F01 | E01 → A01 | — |
| F02 | A01 → A02 | — |
| F03 | A02 → A03 | — |
| F04 | A03 → G01 | — |
| F05 | G01 → A05 | Sim |
| F06 | G01 → A04 | Não |
| F07 | A04 → A03 | — |
| F08 | A05 → E02 | — |
| F09 | E02 → G02 | — |
| F10 | G02 → E03 | Sim — CI passou, segue para aguardar o review |
| F11 | G02 → A06 | Não |
| F12 | A06 → A03 | — |
| F13 | E03 → G03 | — |
| F14 | G03 → A09 | Sim — aprovação formal recebida |
| F15 | G03 → G04 | Não — sem aprovação formal |
| F16 | G04 → A08 | Sim — bypass excepcional e deliberado |
| F17 | G04 → A07 | Não — regra geral, sem bypass |
| F18 | A07 → A03 | — |
| F19 | A08 → A09 | — |
| F20 | A09 → E04 | — |
| F21 | E04 → A10 | — |
| F22 | A10 → G05 | — |
| F23 | G05 → A12 | Sim |
| F24 | G05 → A11 | Não |
| F25 | A11 → A03 | — |
| F26 | A12 → E05 | — |
| F27 | E05 → A13 | Em lote, ao final da sprint |
| F28 | A13 → E06 | — |
| F29 | E06 → A14 | — |
| F30 | A14 → E07 | — |
| F31 | E07 → A15 | — |
| F32 | A15 → G06 | — |
| F33 | G06 → A17 | Sim |
| F34 | G06 → A16 | Não |
| F35 | A16 → A03 | — |
| F36 | A17 → E08 | — |
| F37 | E09 → A18 | — |
| F38 | A18 → G07 | — |
| F39 | G07 → A20 | Sim |
| F40 | G07 → A19 | Não |
| F41 | A19 → E10 | — |
| F42 | A20 → E10 | — |
| F43 | E11 → A21 | — |
| F44 | A21 → G08 | — |
| F45 | G08 → E12 | Sim |
| F46 | G08 → E12b | Não |
| F47 | E14 → A22 | — |
| F48 | A22 → E13 | — |

*Tabela 30 – Fluxos de sequência do processo de desenvolvimento assistido por IA*

### 4.7 Fluxos de mensagem entre pools

| ID | Origem → Destino | Conteúdo |
|---|---|---|
| M01 | A05 (Desenvolvedor) → E11 (Pipeline CI/CD) | PR aberto/atualizado, solicita execução do CI |
| M02 | E12 (Pipeline CI/CD) → E02 (Desenvolvedor) | Resultado do CI: verde |
| M03 | E12b (Pipeline CI/CD) → E02 (Desenvolvedor) | Resultado do CI: falha |
| M04 | A05 (Desenvolvedor) → E09 (Revisor) | PR vinculado à issue, solicitação de review |
| M05 | E10 (Revisor) → E03 (Desenvolvedor) | Decisão do review: aprovado ou comentários solicitando ajuste |
| M06 | A09 (Desenvolvedor) → E14 (Pipeline CI/CD) | Merge realizado em `homolog` |
| M07 | E13 (Pipeline CI/CD) → E04 (Desenvolvedor) | Deploy em homolog concluído |
| M08 | A14 (Desenvolvedor) → E14 (Pipeline CI/CD) | Merge realizado em `main` |
| M09 | E13 (Pipeline CI/CD) → E07 (Desenvolvedor) | Deploy em produção concluído |

*Tabela 31 – Fluxos de mensagem do processo de desenvolvimento assistido por IA*

> **Nota de modelagem (E02, E13, E14):** por coerência com o mesmo princípio já aplicado em P01/P04, eventos de captura são reutilizados quando duas mensagens têm o mesmo significado para quem recebe. `E02` captura tanto M02 quanto M03 porque, para o desenvolvedor, o que importa é "o CI respondeu" — a ramificação (verde/falha) já vem como atributo da própria mensagem. Da mesma forma, `E13` e `E14` são reutilizados para homolog e para main: isso reflete um fato real do processo — **o mesmo pipeline de CI/CD atende as duas branches, só muda o destino** (`docs/manual-sprint.md`, seção 8).

### 4.8 Narrativa do fluxo

**Caminho principal (feliz).** A US chega pronta para desenvolvimento (E01), com DOR atendido. O desenvolvedor lê a US, o PRD/SPEC e o diagrama de sequência (A01) — essa leitura prévia é o que a equipe chama de "spec programming": sem ela, o código tende a divergir da arquitetura pretendida e o problema só aparece no review, tarde demais. Cria a branch a partir da base correta (A02) e conduz, com apoio do agente de IA, o ciclo de planejar, codificar e testar localmente (A03). Passando nos testes locais (G01 = Sim), faz o commit em Conventional Commits — sem qualquer atribuição de IA — e abre o PR vinculado à issue (A05). O pipeline roda o CI (M01) e devolve resultado verde (M02, capturado em E02); o PR segue para revisão (M04) e o revisor aprova formalmente pelo botão "Review changes" → "Approve" (A20, via M05, capturado em E03). Com aprovação formal confirmada (G03 = Sim), o desenvolvedor — nunca a IA — confirma o merge em `homolog` (A09). O deploy dispara automaticamente (M06 → A22 → M07, capturado em E04), os critérios de aceite são validados em homolog (A10) e, atendidos (G05 = Sim), a issue recebe o comentário de fechamento da sprint (A12): DoD-Sprint cumprido (E05). Ao final da sprint, em lote, o PR `homolog → main` é aberto (A13), aprovado (E06) e mergeado (A14) — sempre por confirmação humana. O deploy em produção conclui (M08 → A22 → M09, capturado em E07), a validação em produção é feita de fato, não suposta (A15); atendida (G06 = Sim), a issue é fechada e a documentação atualizada, se aplicável (A17): DoD-Release cumprido (E08).

**Primeiro desvio — testes locais ou CI falham.** Se os testes locais falham (G01 = Não), o desenvolvedor corrige com o agente e retesta (A04), sem gastar um ciclo de CI para descobrir o mesmo erro — CI é mais lento, feedback local é instantâneo. Se o CI falha depois de aberto o PR (G02 = Não, via E12b), a correção volta ao mesmo ciclo de desenvolvimento com o agente (A06 → A03).

**Segundo desvio — review não aprova.** Um comentário de texto no PR ("revisado", "ok pra mim") **não conta como aprovação formal** — só o botão "Review changes" → "Approve" satisfaz a proteção de branch. Sem essa aprovação (G03 = Não), o processo verifica se é um bypass excepcional e deliberado (G04) — cenário raro, aceitável apenas quando o próprio objetivo do trabalho é testar o pipeline de CI/CD. Sendo esse o caso (G04 = Sim), o bypass é registrado explicitamente na issue, com justificativa (A08), nunca de forma silenciosa. Fora desse cenário (G04 = Não), o desenvolvedor ajusta conforme os comentários do revisor e retorna ao desenvolvimento (A07 → A03).

**Terceiro desvio — critérios de aceite ou validação em produção falham.** Se os critérios de aceite não são atendidos em homolog (G05 = Não) ou a validação em produção falha (G06 = Não), o processo retorna ao desenvolvimento com o agente (A11 ou A16 → A03) — nunca se declara a US concluída sem checagem real do resultado, seja em homolog ou em produção.

**O que garante que a IA não decide sozinha.** Em nenhum ponto do fluxo a IA confirma um merge, registra um bypass ou submete uma aprovação formal — essas três ações (A09, A08, A20) são sempre tarefas de usuário conduzidas pelo humano responsável, mesmo quando toda a codificação anterior foi feita com apoio do agente.

### 4.9 Riscos de governança e mitigação

Ao contrário das seções 3.2.9 e 3.3.9, que listam disfunções ainda sem tratamento, esta seção lista **riscos que o próprio desenho do processo já mitiga** — é a base factual da defesa apresentada na seção 5.

| ID | Elemento ancorado | Risco | Como o processo mitiga |
|---|---|---|---|
| R1 | A03 / G03 | Confiança excessiva na IA, sem revisão humana antes do merge. | Gateway `G03` prevê aprovação formal antes de qualquer merge em `homolog` ou `main`. É a regra de desenho; a conferência de como cada PR do orquestrador (que o GitHub não deixa aprovar o próprio) foi mergeado está pendente (4.10), então não se afirma que valeu sem exceção. |
| R2 | G04 / A08 | Bypass de proteção de branch usado para acelerar entrega, mascarando risco real. | Bypass só é aceitável no cenário excepcional de teste do próprio pipeline (`G04`), é sempre decisão do desenvolvedor (nunca da IA) e precisa ser registrado explicitamente na issue (`A08`) — nunca silencioso. |
| R3 | A05 | Perda de rastreabilidade de autoria do trabalho acadêmico. | Commits, PRs e comentários de issue nunca citam a IA como autora ou colaboradora (`A05`) — o histórico reflete apenas o trabalho do time. |
| R4 | G03 / A20 | Comentário informal no PR ser confundido com aprovação real, furando a proteção de branch. | `G03` só avança com `reviewDecision: APPROVED` confirmado via revisão formal (`A20`, botão "Review changes" → "Approve"); comentário de texto (`A19`) é tratado explicitamente como não-aprovação. |
| R5 | A03 | Divergência entre o plano de arquitetura e o código real ser resolvida silenciosamente pela IA, sem o time perceber. | A prática do time é expor a divergência ao desenvolvedor responsável e deixar a decisão explícita (seguir o código ou seguir o plano), nunca escolher um lado sozinha. |

*Tabela 32 – Riscos de governança do processo de desenvolvimento e sua mitigação*

### 4.10 O processo na prática: volume, qualidade e falhas

Esta subseção registra o que o processo modelado entregou de fato. Fontes: `gh issue list` e `gh pr list` de 28/10/2026; `docs/guia-apresentacao.md`, seção 3 (números coletados em 27/10/2026, salvo indicação); `docs/qa/` (qualidade medida em 16/10 e casos manuais executados até 28/10).

**Quem escreveu o quê.** Todo o código do Movecity foi gerado por agentes de IA. Seis estudantes conduziram esses agentes: especificaram (issue, cenários BDD, diagrama de sequência), revisaram e aprovaram. Por regra de autoria (`docs/boas-praticas-ia.md`), os commits não levam assinatura de ferramenta, de modo que o histórico do repositório não mostra a participação da IA; a declaração é do grupo e está feita neste documento. Não se usa "percentual de código escrito pela IA": seria 100% e não mede o esforço humano, que esteve na especificação, na revisão e na verificação.

**Volume.**

| Métrica | Valor | Fonte |
|---|---|---|
| Issues | 101 (70 fechadas, 31 abertas), em 28/10; 84 em 27/10 | `gh issue list` |
| Pull Requests | 146 (132 mergeados, 11 fechados sem merge, 3 abertos), em 28/10; 126 em 27/10 | `gh pr list` |
| Commits | 138 (`feat` 35, `fix` 28, `docs` 26, `chore` 24), em 27/10 | Guia, 3.1 |
| Período | 15/08 a 27/10/2026, cerca de 10 semanas | Guia, 3.1 |
| PRs por tipo de branch (de 126) | 61 `feat`, 37 `fix`, 9 `chore`, 9 `docs` | Guia, 3.1 |
| Issues de épico (US) | 30 fechadas de 38 | `gh issue list` |
| PRs fechados sem merge | 11, todos por retrabalho ou consolidação (3 testes deliberados de workflow, 3 tentativas de recuperação de senha refeitas, 3 do tutorial consolidados em um, entre outros); nenhum por reprovação de qualidade | Guia, 3.2 |
| Tempo da criação ao merge de um PR | mediana de 17 min; `feat` 25 min, `fix` 8 min | Guia, 3.2 e 3.4 |

**Qualidade.**

| Métrica | Valor | Fonte |
|---|---|---|
| Testes automatizados | 1.640 passando no CI de 28/10 (844 de backend, 796 de frontend); eram 1.260 em 16/10 (671 + 589) e 297 no registro original da #151 | `docs/qa/relatorio-testes-unitarios.md` |
| Cobertura | backend 93,7%; frontend 89,1% (piso otimista: 3 arquivos fora da medição) | `docs/qa/relatorio-cobertura-e-defeitos.md` |
| Disciplina de teste | 27 de 27 PRs `feat`/`fix` desde 22/09 trazem arquivo de teste | `docs/qa/resumo-executivo.md` |
| CI de PR verde | 74% no total, 79% na Sprint 2, 94% na Sprint 3 | `docs/qa/relatorio-cobertura-e-defeitos.md` |
| Casos manuais em produção | 49 de 49 executados: 32 aprovados, 11 em parte ou com ressalva, 1 reprovado por configuração, 3 não verificáveis hoje, 2 pendentes | `docs/qa/execucao-casos-p1.md` |
| Defeitos catalogados | 26 (a classificação por origem abaixo é a dos 24 primeiros: 10 de conexão entre as peças e 14 de regra, dado ou interface; 4 ocorreram em produção, 2 foram pegos pelo CI, 14 por teste manual ou uso real; os 2 novos são o armazenamento de tokens em `localStorage`, #253, e a mensagem de 2 confirmações, #249) | `docs/qa/relatorio-cobertura-e-defeitos.md` |
| Deploys | backend e frontend sem falha desde 22/09 | idem |

**Onde a IA e o processo falharam.** O registro de falhas é parte da defesa, não uma lacuna dela:

- *De processo:* na issue #35, um comentário de texto no PR foi tomado por aprovação formal (origem da regra "só conta o botão Approve", `docs/boas-praticas-ia.md`); o plano previa quatro apps e o código era um monolito, e a divergência foi exposta e decidida por uma pessoa, em vez de resolvida em silêncio (`docs/relato-deploy-sprint0.md`).
- *De código:* o Gateway repassava o `X-User-Id` enviado pelo cliente, e os serviços liam o falso (#188, defeito de segurança, corrigido no PR #189); o `/auth/refresh` chamado pelo Gateway não existia no serviço de autenticação (#212); o cadastro aceitava `termos_aceitos: false` (#211). Os dois últimos foram achados pela execução manual dos casos em 27/10, não pelos testes automatizados, que mockam a vizinhança.
- *Leitura:* os defeitos relevantes são de conexão entre as peças, não de regra de negócio; o CI pegou os que estavam ao seu alcance e os que escaparam só apareceram com dado real ou com a execução manual (`docs/qa/resumo-executivo.md`).

**Limites do processo.** (1) Revisor único: a revisão formal é feita por uma pessoa, e a mediana de 17 min até o merge torna legítima a pergunta sobre a profundidade da revisão. (2) A autoria dos PRs ficou desigual (Davi 71, Vitória 29, Kelvin 11, Breno 7, Nathália 5 e Luis 3, em 27/10), embora a regra seja uma US por pessoa por sprint; parte do trabalho do orquestrador é infraestrutura e correção. (3) O GitHub não permite que o autor aprove o próprio PR; **a conferência de como cada PR do orquestrador foi mergeado frente à regra de aprovação formal está pendente** (`docs/guia-apresentacao.md`, seções 3.4 e 6) e, enquanto não for feita, este documento não afirma que a regra valeu sem exceção. (4) Não há ambiente de homologação separado da produção (decisão de custo). (5) Não houve validação em campo nem teste com usuários reais.

---

## 5. Defesa do Uso de Agentes de IA no Desenvolvimento

Esta seção argumenta, com base no processo modelado na seção 4 e nos números de 4.10, por que o uso de agentes de IA no desenvolvimento do Movecity não compromete a validade do trabalho como TCC. A tese é a do guia de apresentação (`docs/guia-apresentacao.md`, seção 1): **todo o código foi gerado por agentes de IA, conduzidos por seis estudantes que especificaram, revisaram e aprovaram; dentro de um processo com travas (issue, BDD, PR, CI, review, homolog, main), isso entregou um produto funcional e testado em cerca de dez semanas. A IA escreveu; o processo e as pessoas garantiram a qualidade, e onde o processo falhou, os defeitos apareceram.**

### 5.1 Legitimidade acadêmica

A defesa não depende de dizer que a IA "ajudou um pouco": ela escreveu o código. O que é dos estudantes é o que a IA não decide sozinha: o problema e o escopo, a arquitetura e as decisões que contrariaram o plano inicial (`docs/documento_arquitetura.md`, seção 10), a especificação de cada User Story (issue, cenários BDD e diagrama de sequência, lidos antes de qualquer código), a revisão do que foi gerado, a aprovação e o merge, e a verificação do resultado em produção (49 casos manuais executados, 26 defeitos catalogados). Como mostra a narrativa 4.8, as três ações que fecham cada etapa crítica do ciclo — confirmar o merge (`A09`/`A14`), registrar um bypass (`A08`) e submeter a aprovação formal (`A20`) — são tarefas de usuário, conduzidas por pessoas. A regra de `docs/boas-praticas-ia.md` complementa: a IA age em nome de quem conduz a sessão, nunca é citada como autora em commit, PR ou comentário de issue, porque o repositório é acadêmico e a responsabilidade pelo trabalho é do time. Isso explica por que o histórico não mostra a ferramenta; a transparência sobre o uso está nos documentos do projeto, e não nos commits.

### 5.2 Rastreabilidade e governança

O processo tem pontos de controle formal que o desenvolvimento sem IA não garantiria por si só: critérios DOR antes de qualquer código, aprovação formal obrigatória via GitHub (não um comentário), CI obrigatório, Conventional Commits para histórico legível e DoD em dois níveis (Sprint e Release). A tabela 32 (seção 4.9) resume os riscos concretos de usar IA no desenvolvimento e o mecanismo de mitigação desenhado para cada um. Dois pontos pedem honestidade: a regra de aprovação formal é de desenho, e a conferência de como cada PR do próprio orquestrador foi mergeado ainda está pendente (4.10); e o repositório tem um único revisor formal. Os mecanismos existem e são auditáveis (histórico de commits, comentários de issue, log de reviews), mas a defesa não deve prometer "nenhuma exceção" antes de essa conferência ser feita.

### 5.3 Qualidade e produtividade: o que os números sustentam

Os números de 4.10 descrevem o que foi entregue: 101 issues e 146 PRs em cerca de dez semanas, 30 das 38 issues de épico fechadas, 1.640 testes automatizados, cobertura de 93,7% (backend) e 89,1% (frontend), e todos os 27 PRs `feat`/`fix` desde 22/09 com teste. O ciclo de `docs/manual-sprint.md` — ler a US e o diagrama antes de codar, testar localmente antes do CI, commit atômico — é a prática do time; o CI de PR passou de 79% verde (Sprint 2) para 94% (Sprint 3), mas a causa dessa melhora não foi isolada. Este documento **não afirma ganho de produtividade**: não houve grupo de controle nem medição do tempo que o mesmo trabalho levaria sem IA, e métricas como tempo médio de ciclo da US não foram coletadas de forma sistemática (a mediana de 17 min de criação ao merge é de PR, não de US).

### 5.4 Limites e riscos assumidos

A defesa fica mais forte se declarar o que o processo não resolveu: (1) os testes automatizados mockam as integrações, e os defeitos relevantes (10 dos 24 classificados) são de conexão entre as peças; a verificação real foi a execução manual em produção; (2) revisor único e revisão rápida; (3) a autoria dos PRs é desigual entre os integrantes; (4) não há ambiente de homologação separado, de modo que `homolog` publica na produção; (5) a avaliação de usabilidade teve um único avaliador e não houve teste com usuários reais; (6) a tolerância do ETA e a regra do ônibus chegando não foram medidas em campo; (7) o frontend grava os tokens de sessão em `localStorage` (#253, aberta), o que enfraquece a proteção do cookie httpOnly descrita na arquitetura: é um risco de segurança conhecido e não corrigido; (8) o raio de embarque ficou em 100 km em produção, de propósito, para a demonstração (a regra de uso real é 100 m). Esses limites estão registrados em `docs/qa/resumo-executivo.md` e em `docs/guia-apresentacao.md`, seção 6.1.

---

## 6. Síntese das Disfunções Identificadas

A modelagem AS-IS dos dois processos revela que a informação necessária para resolver o problema **já existe** — está no GPS do veículo, na escala do CCO, na decisão de cancelamento e na experiência dos passageiros. O que não existe é um caminho que a leve, em tempo útil, a quem está na parada.

| # | Disfunção consolidada | Processo | Natureza | Situação com o Movecity entregue (28/10/2026) |
|---|---|---|---|---|
| D1 | A informação de posição e de cancelamento existe na operadora, mas não atravessa a fronteira do pool em direção ao passageiro. | P01 (N05, N06) | Ruptura de fluxo de informação | **Em parte:** a posição chega (feed da SEMOB); o cancelamento não |
| D2 | Os canais digitais exibem o horário programado como se fosse o horário real. | P01 (N01) | Qualidade do dado | **Tratada:** cada tempo declara a fonte; precisão não medida em campo |
| D3 | O passageiro compensa a incerteza com margem de segurança e com consultas manuais a fontes informais. | P01 (N02, N03) | Retrabalho e desperdício | **Em parte:** meios entregues (ETA, rota, favoritos); efeito não medido |
| D4 | A espera na parada é o ponto de maior exposição a risco e ocorre sem qualquer previsão de término. | P01 (N04) | Segurança | **Não resolvida:** é infraestrutura, fora do alcance do app |
| D5 | A decisão de continuar esperando é tomada repetidamente sem nenhum dado novo. | P01 (N07) | Decisão sob incerteza | **Em parte:** reconsulta com dado atualizado; sem alerta proativo |
| D6 | A maior parte das ocorrências nunca é registrada. | P04 (N01, N05) | Subnotificação | **Em parte:** esforço de reportar reduzido; taxa de reporte não medida |
| D7 | O ciclo de tratamento é medido em dias; a necessidade do passageiro é medida em minutos. | P04 (N03) | Descompasso de tempo de ciclo | **Em parte:** só entre passageiros; ouvidoria inalterada |
| D8 | A informação colaborativa existe nas redes sociais, mas é dispersa, não validada e não persistente. | P04 (N04, N07) | Perda de conhecimento coletivo | **Tratada** dentro da base de usuários do Movecity |
| D9 | Não há dono do processo ponta a ponta nem validação cruzada entre relatos. | P04 (N06, N08) | Governança | **Em parte:** validação cruzada (3 confirmações); sem dono único |

*Tabela 33 – Síntese das disfunções dos processos AS-IS e situação no Movecity entregue*

Essas nove disfunções constituem a linha de base contra a qual o TO-BE com o Movecity (seção 3.4) foi comparado; a Tabela 25 (seção 3.5) detalha, para cada uma, a funcionalidade, a evidência e o que segue sem solução. Em resumo: duas tratadas, seis tratadas em parte e uma não resolvida. Elas se referem exclusivamente aos processos de mobilidade (P01/P04); os riscos do processo de desenvolvimento assistido por IA estão na tabela 32 (seção 4.9), por pertencerem a um domínio diferente.

---

## 7. Próximos Passos

| Etapa | Atividade | Situação em 28/10/2026 |
|---|---|---|
| 1 | Desenhar os diagramas BPMN 2.0 de P01, P04, do TO-BE com o Movecity e do desenvolvimento com IA | **Concluído.** Arquivos `.bpmn` em `docs/diagramas/processos/`. O `02-processo-com-movecity.bpmn` foi corrigido na versão 3.0 para refletir o produto entregue. **Pendente:** as imagens renderizadas ainda precisam ser inseridas nos placeholders `[Inserir imagem do fluxo...]` deste documento |
| 2 | Validar a modelagem AS-IS e o TO-BE com usuários reais do STPC/DF em Taguatinga e Ceilândia | **Não feito.** Segue como trabalho futuro. Sem isso, as disfunções D1 a D9 são análise do grupo, não evidência empírica |
| 3 | Validar com a equipe de arquitetura se o mecanismo descrito em 3.4.2 corresponde ao que foi implementado | **Concluído em 28/10:** conferido contra o código de `homolog`. A conferência mostrou que o mecanismo da versão 2.0 (prioridade colaborativo → GPS oficial) não existia; o diagrama e a seção 3.4 foram corrigidos |
| 4 | Definir os indicadores de desempenho dos processos (tempo de espera percebido, taxa de notificação de ocorrências, tempo até a informação chegar ao passageiro) | **Aberto.** O produto não registra esses indicadores; os números de qualidade existentes (`docs/qa/`) medem o software, não o processo de negócio |
| 5 | Tratar as lacunas que impedem resolver D1 e D5: alerta de cancelamento (#28), push dos alertas (#207) e integração com a operadora | **Aberto**, fora do que foi entregue até a defesa |
| 6 | Validar em campo: tolerância do ETA, regra do ônibus chegando (CT-VIA-07), aviso de proximidade (CT-VIA-08) e Web Push em aparelho (#200) | **Aberto.** VIA-07 e VIA-08 entram no ensaio da defesa |
| 7 | Voltar o raio de embarque de 100 km para 100 m em produção (`RAIO_EMBARQUE_M`) | **Depois da defesa**, por decisão do grupo de 28/10 (`docs/qa/resumo-executivo.md`) |

### 7.1 Pontos a confirmar: o que as fontes já resolveram e o que segue aberto

**Resolvidos:**

- *Existência da API de posições da frota (SEMOB):* os endpoints de `dados.semob.df.gov.br` existem e estão vivos (`docs/pesquisa-integracao-onibus-df.md`, correção de 13/09, PR #112). Em produção, a posição ao vivo foi observada nos casos CT-ETA-01 e CT-MAP-07. **Continua em aberto** a periodicidade oficial de atualização: são endpoints sem documentação pública nem SLA (ADR-03), e na checagem de 13/09 apenas 678 dos 2.736 veículos com posição recente informavam linha e sentido.
- *Mecanismo de fonte da posição:* ver etapa 3 acima.
- *Existência de e-mail no fluxo de recuperação de senha:* resolvido em 28/10 por SMTP (#237, PR #238); a confirmação de conta por e-mail não existe.

**Seguem abertos:**

- Denominação atual, canais de acesso e prazos **praticados** pela ouvidoria do GDF para manifestações sobre transporte público. O prazo legal (30 dias, prorrogáveis) vem da Lei nº 13.460/2017, art. 16; o prazo efetivamente praticado não foi confirmado em fonte oficial.
- Nome e funcionalidades vigentes do aplicativo oficial de informação ao usuário do STPC/DF. A pesquisa do projeto o identifica como "DF no Ponto" (`docs/pesquisa-integracao-onibus-df.md`), sem API pública para desenvolvedores; a vigência de cada funcionalidade modelada em 3.2 não foi confirmada.
- Fluxo interno de decisão de cancelamento de viagem nas empresas operadoras, idealmente validado em entrevista com profissional da área. É a premissa de N05 e de D1; não foi validada.
- **Limiar de validação cruzada:** o código exige **3 confirmações de outros usuários** (`LIMITE_CONFIRMACOES = 3`, `colaboracao/models/ocorrencia.py`), com "acidente" e "segurança" exibidos de imediato. A tela de reporte também diz "mínimo 2 confirmações" (#249, aberta) e um caso de teste manual registra "2 confirmações" (CT-COL-01), enquanto o servidor exige 3; o Documento de Visão (v1.1) já registra 3. Falta corrigir o texto da tela.
- **Segurança da sessão (#253, aberta):** o frontend grava os tokens em `localStorage`, o que anula a proteção do cookie httpOnly que a arquitetura declara; a correção não foi feita.
- Issues #26, #29 e #200 seguem abertas com código mergeado; o grupo decide se as fecha ou se registra o que falta.
- Conferência de como os PRs do orquestrador foram mergeados frente à regra de aprovação formal (4.10).

---

## 8. Referências

- ABPMP. **BPM CBOK — Guia para o Gerenciamento de Processos de Negócio: Corpo Comum de Conhecimento.** Association of Business Process Management Professionals.
- BRASIL. **Lei nº 13.460, de 26 de junho de 2017** — dispõe sobre participação, proteção e defesa dos direitos do usuário dos serviços públicos da administração pública.
- CAROLI, P. **Lean Inception: como alinhar pessoas e construir o produto certo.** Editora Caroli, 2018.
- CGDF. **Painel de Ouvidoria do Distrito Federal.** Controladoria-Geral do Distrito Federal, 2026.
- GRUPO SEGURANÇA NO TRANSPORTE. **Boas Práticas de Uso de IA no Workflow — Movecity.** Disponível em: `docs/boas-praticas-ia.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Documento de Arquitetura de Software — Movecity.** Disponível em: `docs/documento_arquitetura.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Documento de Visão — Movecity.** Disponível em: `docs/documento_visao.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Guia de Contribuição — Movecity.** Disponível em: `docs/guia-contribuicao.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Manual do Sprint Movecity — do Backlog ao Deploy.** Disponível em: `docs/manual-sprint.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Repositório do projeto Movecity.** GitHub, 2026. Disponível em: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb>. Acesso em: 28 set. 2026.
- IPEDF. **Pesquisa Distrital por Amostra de Domicílios (PDAD).** Instituto de Pesquisa e Estatística do Distrito Federal, 2022.
- OMG. **Business Process Model and Notation (BPMN), Version 2.0.** Object Management Group.

## Anexos

Os três arquivos a seguir, no formato BPMN 2.0 (`.bpmn`), estão anexados a esta entrega e contêm o código-fonte completo dos diagramas referenciados ao longo do documento. Podem ser abertos em qualquer ferramenta aderente à notação BPMN 2.0 (ex.: bpmn.io, Camunda Modeler, Bizagi Modeler).

- `01-processos-as-is.bpmn` — Processos P01 e P04 no cenário AS-IS manual (sem Movecity), incluindo DF no Ponto, Google Maps/Moovit.
- `02-processo-com-movecity.bpmn` — TO-BE com o Movecity — os mesmos processos operando com o sistema entregue em 28/10/2026 (corrigido na versão 3.0: sem fallback colaborativo, sem notificação do cancelamento pela operadora e sem alerta push de cancelamento).
- `03-processo-desenvolvimento-ia.bpmn` — Processo de desenvolvimento de software assistido por agentes de IA.

Também está anexada a **versão resumida** deste documento (`docs/analise-processos-negocio-resumo.md`), que é a entrega oficial de até 25 páginas exigida pela disciplina.
