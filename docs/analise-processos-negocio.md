# Etapa 1 — Entrega Parcial: Análise e Modelagem de Processos de Negócio

**Projeto:** Movecity — Mobilidade Urbana Colaborativa no DF
**Grupo:** Segurança no Transporte — Universidade Católica de Brasília (UCB)
**Integrantes:** Breno Santana Silva, Davi Eduardo Costa Miranda, Kelvin Rodrigues de Sousa, Luis Fernando Monteiro de Assis Lourenço, Nathalia Gualberto Lopes e Vitória Cordeiro Albuquerque
**Versão:** 1.0

---

## Histórico da Revisão

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 18/set/26 | 1.0 | Versão inicial — contextualização, identificação e classificação dos processos e modelagem AS-IS | Grupo Segurança no Transporte |

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
   - 3.2 [Processo P01 — Planejar e realizar deslocamento por ônibus](#32-processo-p01--planejar-e-realizar-deslocamento-por-ônibus-as-is)
   - 3.3 [Processo P04 — Registrar e tratar ocorrência no serviço](#33-processo-p04--registrar-e-tratar-ocorrência-no-serviço-as-is)
4. [Síntese das Disfunções Identificadas](#4-síntese-das-disfunções-identificadas)
5. [Próximos Passos](#5-próximos-passos)
6. [Referências](#6-referências)

---

## 1. Contextualização do Projeto

### 1.1 Descrição do sistema

O **Movecity** é um aplicativo web de mobilidade urbana colaborativa desenvolvido como Trabalho de Conclusão de Curso pelo grupo Segurança no Transporte da UCB. A plataforma combina duas fontes de informação que hoje existem de forma isolada:

1. **Dados oficiais de GPS** da frota do Sistema de Transporte Público Coletivo do Distrito Federal (STPC/DF), obtidos junto à API da SEMOB/GDF em formato GeoJSON;
2. **Reportes colaborativos** dos próprios passageiros, no modelo de inteligência coletiva popularizado pelo Waze, submetidos a validação cruzada (uma ocorrência só é confirmada com, no mínimo, dois reportes independentes).

O resultado é um mapa em tempo real, com previsão de chegada, itinerário, paradas e alertas de atraso, cancelamento e risco de segurança. O sistema opera como projeto-piloto em **Taguatinga e Ceilândia**, regiões administrativas escolhidas por concentrarem alta densidade demográfica e intensa demanda por transporte público.

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

O projeto encontra-se em desenvolvimento ativo, com 24 histórias de usuário distribuídas entre os integrantes e organizadas em três épicos (Autenticação, Mapa e Rastreamento, Colaboração). A arquitetura implementada é orientada a serviços, com um API Gateway atuando como ponto único de entrada, frontend em Next.js, serviços de backend em FastAPI e banco PostgreSQL. A especificação completa está registrada em `docs/documento_visao.md` e `docs/documento_arquitetura.md`.

### 1.5 Delimitação do escopo desta entrega

Esta entrega parcial trata da **análise e modelagem dos processos atuais (AS-IS)** — isto é, de como o deslocamento por ônibus e o tratamento de ocorrências acontecem **hoje, sem o Movecity**. O objetivo é evidenciar, com rigor de notação, onde estão as rupturas de informação que justificam a existência do produto.

A unidade de análise não é uma empresa isolada, mas a **jornada informacional do passageiro do STPC/DF** e o conjunto de processos que a sustentam, envolvendo quatro atores: o passageiro, as empresas operadoras, o poder público (SEMOB/GDF e ouvidoria) e os canais digitais de informação existentes.

A modelagem do estado futuro (TO-BE), com o Movecity inserido no fluxo, será objeto da próxima etapa.

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

### 2.2 Visão macro da cadeia de valor

```
                       PROCESSOS DE GESTÃO
  ┌──────────────────────────────────────────────────────────────────────┐
  │  G01 Planejar a oferta   G02 Monitorar e fiscalizar a execução       │
  │  G03 Gerir a qualidade   G04 Gerir contratos   G05 Gerir transparência│
  └──────────────────────────────────────────────────────────────────────┘
                                    │ metas, quadros de horário, sanções
                                    ▼
                       PROCESSOS PRIMÁRIOS (jornada do passageiro)
  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
  │ P01       │──►│ P02       │──►│ P03       │──►│ P05       │   │ P04       │
  │ Planejar e│   │ Consultar │   │ Aguardar e│   │ Executar a│   │ Registrar │
  │ realizar o│   │ a situação│   │ embarcar  │   │ viagem    │   │ e tratar  │
  │ desloca-  │   │ da linha  │   │ na parada │   │ (operadora)│  │ ocorrência│
  │ mento     │   │           │   │           │   │           │   │           │
  └───────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────┘
                                    ▲
                                    │ insumos: dados, cadastro, infraestrutura
  ┌──────────────────────────────────────────────────────────────────────┐
  │  S01 Coletar dados de GPS   S02 Manter cadastro de linhas e paradas  │
  │  S03 Operar canais de atendimento   S04 Manter paradas e terminais   │
  │  S05 Operar a bilhetagem   S06 Manter canais digitais oficiais       │
  └──────────────────────────────────────────────────────────────────────┘
                       PROCESSOS DE SUPORTE
```

*Figura 1 – Cadeia de valor do ecossistema de informação da mobilidade no DF*

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

#### 3.2.5 Elementos do diagrama

**Pool 1 — Passageiro**

| ID | Tipo BPMN | Rótulo |
|---|---|---|
| E01 | Evento de início (simples) | Necessidade de deslocamento identificada |
| A01 | Tarefa de usuário | Definir origem, destino e horário de chegada desejado |
| A02 | Tarefa de usuário | Consultar linha, itinerário e horário nos canais digitais |
| G01 | Gateway exclusivo (divergente) | A informação obtida é suficiente e confiável? |
| A03 | Tarefa manual | Perguntar em grupo de mensagens, rede social ou a outro passageiro |
| A04 | Tarefa manual | Estimar o horário com base na experiência própria |
| G02 | Gateway exclusivo (convergente) | — (junção) |
| A05 | Tarefa de usuário | Escolher a linha e definir o horário de saída, com margem de segurança |
| A06 | Tarefa manual | Deslocar-se até a parada |
| A07 | Tarefa de recebimento | Aguardar a chegada do ônibus na parada |
| E02 | Evento de borda — temporizador (interruptivo, em A07) | Tempo de espera excede a margem prevista (≈ 15 min) |
| E03 | Evento de borda — condicional (interruptivo, em A07) | Percepção de risco ou insegurança na parada |
| A08 | Tarefa de usuário | Reconsultar o aplicativo e checar com outros passageiros na parada |
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
| A15 | Tarefa de serviço | Localizar a linha e o itinerário na base cadastral |
| A16 | Tarefa de serviço | Consultar a última posição de GPS informada pela frota |
| G06 | Gateway exclusivo (divergente) | Existe posição de GPS recente para a linha? |
| A17 | Tarefa de serviço | Exibir a posição do veículo e a previsão estimada |
| A18 | Tarefa de serviço | Exibir apenas o horário programado do quadro de horários |
| G07 | Gateway exclusivo (convergente) | — (junção) |
| E09 | Evento de fim de mensagem | Resposta devolvida ao passageiro |

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
| F03 | A02 → G01 | — |
| F04 | G01 → G02 | Sim — informação suficiente |
| F05 | G01 → A03 | Não — dado ausente, genérico ou desatualizado |
| F06 | A03 → A04 | — |
| F07 | A04 → G02 | — |
| F08 | G02 → A05 | — |
| F09 | A05 → A06 | — |
| F10 | A06 → A07 | — |
| F11 | A07 → G05 | Ônibus chegou à parada |
| F12 | E02 → A08 | Espera excedida |
| F13 | A08 → G03 | — |
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
| F29 | A15 → A16 | — |
| F30 | A16 → G06 | — |
| F31 | G06 → A17 | Sim |
| F32 | G06 → A18 | Não |
| F33 | A17 → G07 | — |
| F34 | A18 → G07 | — |
| F35 | G07 → E09 | — |
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
| M02 | E09 (Canais digitais) → A02 (Passageiro) | Posição estimada ou apenas horário programado |
| M03 | A03 (Passageiro) → Pool 4 (Rede informal) | Pergunta sobre a situação da linha |
| M04 | Pool 4 (Rede informal) → A03 (Passageiro) | Resposta de outro passageiro, não verificada |
| M05 | E13 (Motorista) → A07 (Passageiro) | Chegada do veículo à parada |
| M06 | A08 (Passageiro) → E08 (Canais digitais) | Nova consulta durante a espera |
| M07 | Pool 4 (Rede informal) → A08 (Passageiro) | Informação informal de outros passageiros |

*Tabela 13 – Fluxos de mensagem do processo P01*

#### 3.2.8 Narrativa do fluxo

**Caminho principal (feliz).** O passageiro identifica a necessidade de se deslocar (E01) e define origem, destino e horário de chegada desejado (A01). Consulta os canais digitais (A02), que localizam a linha na base cadastral (A15) e buscam a última posição de GPS conhecida (A16). Havendo posição recente, a previsão é exibida (A17); caso contrário, apenas o horário programado (A18). Com informação considerada suficiente (G01 = Sim), o passageiro escolhe a linha e define a hora de sair de casa, sempre acrescentando uma margem de segurança (A05). Desloca-se até a parada (A06) e aguarda (A07). Em paralelo, a operadora iniciou a programação diária (E10), escalou veículos e motoristas (A19) e, havendo recursos (G08 = Sim), o motorista executa o itinerário (A22) e chega à parada (E13, que envia M05). O passageiro verifica que o veículo atende (G05 = Sim), embarca e valida a passagem (A13), realiza a viagem (A14) e chega ao destino (E04).

**Primeiro desvio — informação insuficiente.** Quando o canal digital não dispõe de posição de GPS recente e exibe apenas o horário programado, o passageiro considera a informação insuficiente (G01 = Não) e recorre à rede informal (A03, com M03 e M04) ou estima o horário com base na própria experiência (A04). É aqui que a assimetria de informação se converte em trabalho manual do passageiro.

**Segundo desvio — a espera se frustra.** Se o tempo de espera excede a margem prevista, o evento de borda E02 interrompe a espera. O passageiro reconsulta o aplicativo e pergunta a outros passageiros na parada (A08). Se há confirmação de que o ônibus virá (G03 = Sim), retorna à espera (F14); caso contrário, escolhe uma alternativa (G04): pagar transporte por aplicativo, com custo não planejado (A09 → E05); tentar outra linha, retornando ao replanejamento (A10 → A05); ou desistir e avisar sobre o atraso (A11 → E06). **Este é o desvio que caracteriza o "ônibus fantasma" na perspectiva do passageiro.**

**Terceiro desvio — insegurança.** A qualquer momento durante a espera, a percepção de risco (E03) pode interromper o processo: o passageiro deixa a parada (A12) e o deslocamento não se realiza (E07). O gatilho não é o tempo em si, mas a combinação de espera prolongada, isolamento e ausência de informação sobre quando a espera terminará.

**Desvio na operadora — a causa raiz.** Quando não há veículo ou motorista disponível (G08 = Não), o CCO cancela ou remaneja a viagem (A20) e o processo se encerra em E11. **Não existe, nesse ponto, qualquer fluxo de mensagem em direção ao passageiro.** A informação de que a viagem não ocorrerá existe, é conhecida e está registrada — mas permanece dentro do pool da operadora. O passageiro continua esperando em A07 por um veículo que nunca sairá da garagem.

#### 3.2.9 Disfunções identificadas

| ID | Elemento ancorado | Disfunção | Efeito sobre o beneficiário |
|---|---|---|---|
| N01 | A16 / G06 | Dados de GPS frequentemente indisponíveis ou desatualizados; o canal exibe o horário programado como se fosse o horário real. | O passageiro planeja com base em uma promessa, não em um fato. |
| N02 | A03 / M04 | Informação da rede informal não é estruturada, georreferenciada nem validada; some do feed em minutos. | O esforço de um passageiro não beneficia o próximo. |
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

## 4. Síntese das Disfunções Identificadas

A modelagem AS-IS dos dois processos revela que a informação necessária para resolver o problema **já existe** — está no GPS do veículo, na escala do CCO, na decisão de cancelamento e na experiência dos passageiros. O que não existe é um caminho que a leve, em tempo útil, a quem está na parada.

| # | Disfunção consolidada | Processo | Natureza |
|---|---|---|---|
| D1 | A informação de posição e de cancelamento existe na operadora, mas não atravessa a fronteira do pool em direção ao passageiro. | P01 (N05, N06) | Ruptura de fluxo de informação |
| D2 | Os canais digitais exibem o horário programado como se fosse o horário real. | P01 (N01) | Qualidade do dado |
| D3 | O passageiro compensa a incerteza com margem de segurança e com consultas manuais a fontes informais. | P01 (N02, N03) | Retrabalho e desperdício |
| D4 | A espera na parada é o ponto de maior exposição a risco e ocorre sem qualquer previsão de término. | P01 (N04) | Segurança |
| D5 | A decisão de continuar esperando é tomada repetidamente sem nenhum dado novo. | P01 (N07) | Decisão sob incerteza |
| D6 | A maior parte das ocorrências nunca é registrada. | P04 (N01, N05) | Subnotificação |
| D7 | O ciclo de tratamento é medido em dias; a necessidade do passageiro é medida em minutos. | P04 (N03) | Descompasso de tempo de ciclo |
| D8 | A informação colaborativa existe nas redes sociais, mas é dispersa, não validada e não persistente. | P04 (N04, N07) | Perda de conhecimento coletivo |
| D9 | Não há dono do processo ponta a ponta nem validação cruzada entre relatos. | P04 (N06, N08) | Governança |

*Tabela 22 – Síntese das disfunções dos processos AS-IS*

Essas nove disfunções constituem a linha de base contra a qual o estado futuro (TO-BE) deverá ser comparado na próxima etapa.

---

## 5. Próximos Passos

| Etapa | Atividade | Produto esperado |
|---|---|---|
| 1 | Desenhar os diagramas BPMN 2.0 de P01 e P04 em ferramenta aderente à norma, a partir das especificações das seções 3.2 e 3.3. | Arquivos `.bpmn` versionados em `docs/diagramas/processos/` e imagens para o documento impresso. |
| 2 | Validar a modelagem AS-IS com usuários reais do STPC/DF em Taguatinga e Ceilândia. | Ajustes nos fluxos e evidência empírica das disfunções D1 a D9. |
| 3 | Modelar o estado futuro (TO-BE) com o Movecity inserido no fluxo. | Diagramas TO-BE e análise comparativa AS-IS × TO-BE. |
| 4 | Definir os indicadores de desempenho dos processos (tempo de espera percebido, taxa de notificação de ocorrências, tempo até a informação chegar ao passageiro). | Painel de indicadores para avaliação do ganho. |

### 5.1 Pontos a confirmar antes da entrega final

Os itens abaixo foram modelados a partir do conhecimento geral do funcionamento do serviço e devem ser confirmados em fonte oficial antes da versão definitiva:

- Denominação atual, canais de acesso e prazos praticados pela ouvidoria do GDF para manifestações sobre transporte público;
- Nome e funcionalidades vigentes do aplicativo oficial de informação ao usuário do STPC/DF;
- Existência e periodicidade de atualização da API pública de posições da frota (SEMOB), já referenciada em `docs/documento_visao.md`;
- Fluxo interno de decisão de cancelamento de viagem nas empresas operadoras — idealmente validado em entrevista com profissional da área.

---

## 6. Referências

- ABPMP. **BPM CBOK — Guia para o Gerenciamento de Processos de Negócio: Corpo Comum de Conhecimento.** Association of Business Process Management Professionals.
- OMG. **Business Process Model and Notation (BPMN), Version 2.0.** Object Management Group.
- BRASIL. **Lei nº 13.460, de 26 de junho de 2017** — dispõe sobre participação, proteção e defesa dos direitos do usuário dos serviços públicos da administração pública.
- IPEDF. **Pesquisa Distrital por Amostra de Domicílios (PDAD).** Instituto de Pesquisa e Estatística do Distrito Federal, 2022.
- CGDF. **Painel de Ouvidoria do Distrito Federal.** Controladoria-Geral do Distrito Federal, 2026.
- CAROLI, P. **Lean Inception: como alinhar pessoas e construir o produto certo.** Editora Caroli, 2018.
- GRUPO SEGURANÇA NO TRANSPORTE. **Documento de Visão — Movecity.** `docs/documento_visao.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Documento de Arquitetura de Software — Movecity.** `docs/documento_arquitetura.md`.
