# Etapa 1 — Entrega Parcial: Análise e Modelagem de Processos de Negócio (Versão Resumida)

**Projeto:** Movecity — Mobilidade Urbana Colaborativa no DF
**Disciplina:** Análise de Processos de Negócio — Universidade Católica de Brasília (UCB)
**Professor orientador (disciplina):** Oscar Galdino de Oliveira Junior
**Autores deste documento:** Vitória Cordeiro Albuquerque, Davi Eduardo Costa Miranda e Nathalia Gualberto Lopes
**Versão:** 2.0 (resumida, ≤ 25 páginas) — estado do produto em 28/10/2026

> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/analise-processos-negocio-resumo.md>

> **Nota sobre esta versão:** este é o documento reduzido, dentro do limite de 25 páginas exigido pela disciplina. A **versão completa** — com o detalhamento elemento-a-elemento (IDs, fluxos de sequência e de mensagem) de cada diagrama BPMN, o processo de desenvolvimento assistido por IA em detalhe total e a defesa argumentada — está disponível em `docs/analise-processos-negocio.md` (<https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/analise-processos-negocio.md>), junto com os arquivos-fonte `.bpmn` dos diagramas, anexados a esta entrega.

> **Nota sobre autoria:** este documento é entregável da disciplina de Análise de Processos de Negócio, cursada por apenas 3 dos 6 integrantes do grupo Segurança no Transporte, sob orientação do Prof. Oscar Galdino de Oliveira Junior. O restante do time do TCC Movecity e o orientador do TCC têm participação ativa no projeto Movecity como um todo (ver `docs/distribuicao_us.md`), mas não neste documento específico.

> **Nota sobre uso de IA na elaboração deste documento:** ferramentas de IA (Claude Code) foram utilizadas como apoio em correção e revisão textual, pesquisa de apoio sobre notação BPMN 2.0 e verificação técnica dos diagramas. A identificação dos processos, a análise das disfunções e as decisões de modelagem são dos autores.

---

## Sumário

1. Contextualização do Projeto
2. Identificação dos Processos de Negócio
3. Modelagem dos Processos Atuais — P01 (AS-IS manual)
4. Modelagem dos Processos Atuais — P04 (AS-IS manual)
5. TO-BE com o Movecity e quadro AS-IS × TO-BE
6. Processo de Desenvolvimento Assistido por IA e Defesa do seu Uso
7. Síntese das Disfunções e Próximos Passos
8. Referências

---

## 1. Contextualização do Projeto

O **Movecity** é um aplicativo web de mobilidade urbana colaborativa desenvolvido como Trabalho de Conclusão de Curso pelo grupo Segurança no Transporte da UCB. A plataforma combina duas fontes de informação hoje isoladas: **dados oficiais de GPS** da frota do STPC/DF (API da SEMOB/GDF, GeoJSON) e **reportes colaborativos** dos próprios passageiros, no modelo do Waze, com validação cruzada (mínimo de dois reportes independentes). O resultado é um mapa em tempo real com previsão de chegada, itinerário e alertas de atraso, cancelamento e risco de segurança. Opera como projeto-piloto em **Taguatinga e Ceilândia**.

O domínio é a **gestão e o consumo de informação sobre mobilidade urbana no DF**, marcado por assimetria de informação: a frota é monitorada por GPS, mas o dado raramente chega de forma fidedigna ao cidadão.

| Problema | Consequência |
|---|---|
| **"Ônibus fantasma"** — viagens programadas que não ocorrem, sem aviso | Espera indefinida, perda de compromissos |
| **Insegurança física e psicológica** — espera em paradas isoladas | Exposição a risco, ansiedade |
| **Ineficiência operacional** — ausência de previsibilidade | Margem de 15-30 min por trajeto, perda de produtividade |

*Tabela 1 – Problemas atacados pelo Movecity*

**Beneficiários diretos:** trabalhadores de turnos críticos, estudantes, profissionais corporativos, passageiros com mobilidade reduzida. **Indiretos:** empresas operadoras, SEMOB/GDF, sociedade do DF. Segundo o IPEDF (2022), 33,3% da população do DF usa o ônibus como principal meio de transporte.

**Situação em 28/10/2026** (`gh`, `docs/guia-apresentacao.md`, `docs/qa/`): 24 histórias de usuário em três épicos; das 38 issues de épico, 30 estão fechadas e 8 abertas. Arquitetura com API Gateway, três serviços FastAPI, Next.js e PostgreSQL. Entregues: autenticação (e-mail, Google, recuperação de senha por SMTP, sessão), mapa, busca de linha e de parada, ônibus em tempo real, ETA com fonte declarada, rota com baldeação, "Peguei este ônibus" com aviso de proximidade, reporte, listagem e confirmação de ocorrências, favoritos, preferências de notificação e tutorial. **Com limites:** os alertas de atraso (#27) e de rotas preferidas (#22) não têm canal de entrega. **Fora:** alerta de cancelamento (#28), push dos alertas (#207), motor GTFS/RAPTOR (#115), horários da linha (#118) e fallback colaborativo de posição (#199). Qualidade: 1.640 testes automatizados no CI de 28/10, 26 defeitos catalogados, 49 casos manuais executados em produção; sem validação em campo nem com usuários reais.

Esta entrega apresenta o **AS-IS manual** — sem sistema dedicado (seções 3 e 4) — e o **TO-BE com o Movecity, limitado ao que foi entregue** (seção 5). "Entregue" significa mergeado em `homolog` ou `main`; o que não foi feito ou não foi medido está dito como tal.

---

## 2. Identificação dos Processos de Negócio

Adotou-se a classificação do **BPM CBOK (ABPMP)**: processos **primários** (entregam valor direto ao cliente), **de suporte** (viabilizam os primários) e **de gestão** (planejam, medem, controlam).

> **Convenção de códigos:** cada processo tem um prefixo de categoria + um número sequencial **dentro daquela categoria** (os números não se relacionam entre categorias diferentes). **P** = processo **Primário** (P01 a P05) · **S** = processo de **Suporte** (S01 a S06) · **G** = processo de **Gestão** (G01 a G05). Na matriz de criticidade (Tabela 2), cada processo recebe nota de 1 (baixo) a 3 (alto) em três critérios — **I**mpacto no beneficiário, **F**requência de execução e grau de **D**isfunção atual — somados na coluna Total.

A cadeia de valor se organiza em três camadas: a **gestão** define metas e sanções que orientam os **processos primários** (a jornada do passageiro: P01→P02→P03→P05 em sequência, com P04 paralelo, acionado sob demanda), sustentados pela **camada de suporte** (dados, cadastro, infraestrutura).

| ID | Processo | Classificação | Dono | I | F | D | Total | Criticidade |
|---|---|---|---|:-:|:-:|:-:|:-:|---|
| P01 | Planejar e realizar deslocamento por ônibus | Primário | Passageiro | 3 | 3 | 3 | **9** | **Crítico** |
| P02 | Consultar a situação da linha em tempo real | Primário | Passageiro/canais | 3 | 3 | 3 | **9** | **Crítico** |
| P03 | Aguardar e embarcar na parada | Primário | Passageiro | 3 | 3 | 2 | **8** | **Crítico** |
| P04 | Registrar e tratar ocorrência no serviço | Primário | Passageiro/Ouvidoria | 2 | 2 | 3 | **7** | **Crítico** |
| P05 | Executar a viagem programada | Primário | Empresa operadora | 3 | 3 | 2 | **8** | Alta |
| S01 | Coletar dados de GPS da frota | Suporte | Operadora/SEMOB | 3 | 3 | 3 | **9** | **Crítico** |
| S02 | Manter cadastro de linhas e paradas | Suporte | SEMOB | 2 | 1 | 2 | 5 | Média |
| S03 | Operar canais de atendimento | Suporte | Ouvidoria/SAC | 1 | 2 | 3 | 6 | Média |
| S04 | Manter infraestrutura de paradas | Suporte | GDF | 2 | 1 | 3 | 6 | Média |
| S05 | Operar a bilhetagem eletrônica | Suporte | SEMOB/operadoras | 2 | 3 | 1 | 6 | Baixa |
| S06 | Manter canais digitais oficiais | Suporte | SEMOB | 2 | 2 | 2 | 6 | Média |
| G01 | Planejar a oferta e programar a operação | Gestão | SEMOB | 2 | 1 | 2 | 5 | Média |
| G02 | Monitorar e fiscalizar a execução | Gestão | SEMOB | 2 | 2 | 3 | **7** | Alta |
| G03 | Gerir a qualidade a partir das manifestações | Gestão | Ouvidoria/SEMOB | 1 | 1 | 3 | 5 | Média |
| G04 | Gerir os contratos de concessão | Gestão | SEMOB/GDF | 1 | 1 | 2 | 4 | Baixa |
| G05 | Gerir a transparência e abertura de dados | Gestão | SEMOB/CGDF | 1 | 1 | 2 | 4 | Baixa |

*Tabela 2 – Inventário e criticidade dos processos (I=Impacto, F=Frequência, D=Disfunção, escala 1-3)*

**Por que P01, P02, P03 e S01 são críticos:** concentram a experiência percebida pelo passageiro — uma falha aqui não é compensável depois. S01 (coleta de GPS) é a **causa raiz**: o dado existe na operadora mas não chega de forma confiável ao passageiro. **P04 é crítico pelo grau de disfunção**, não pela frequência: o ciclo é tão lento que a maioria das ocorrências não é registrada.

**Processos selecionados para modelagem:** **P01** (engloba P02 e P03 — a jornada de consumo de informação) e **P04** (o lado da produção/reporte de informação) — juntos cobrem os dois lados da proposta de valor do Movecity. **P05** (execução da viagem pela operadora) não ganha modelagem própria — ele aparece nos dois diagramas como o processo paralelo do lado da empresa operadora (pool "Empresa operadora"), necessário pro fluxo fazer sentido, mas não é um dos dois processos escolhidos como foco.

---

## 3. Modelagem AS-IS — P01: Planejar e Realizar Deslocamento por Ônibus

Modelado em **BPMN 2.0 (OMG)**. Convenção de IDs: `E`=evento, `A`=atividade, `G`=gateway, `F`=fluxo de sequência, `M`=fluxo de mensagem. O detalhamento elemento-a-elemento (toda a tabela de eventos/tarefas/gateways e cada fluxo de sequência/mensagem) está na **versão completa** e no arquivo-fonte `docs/diagramas/processos/01-processos-as-is.bpmn`.

> **Este diagrama abrange os processos P01, P02 e P03** (planejar o deslocamento, consultar a situação da linha e aguardar/embarcar na parada) — modelados como um único fluxo por serem sequenciais e do mesmo ator (o passageiro). O processo **P05** (execução da viagem pela operadora) também aparece, no pool "Empresa operadora", como contexto paralelo — não é o foco da modelagem, mas o fluxo depende dele (é o motorista chegando à parada que o passageiro está esperando). **P04 não está neste diagrama** — é modelado separadamente na seção 4.

| Atributo | Descrição |
|---|---|
| **Objetivo** | Levar o passageiro da origem ao destino, no menor tempo e com maior previsibilidade possíveis. |
| **Dono** | Passageiro (executor); previsibilidade depende da operadora e da SEMOB. |
| **Gatilho** | Necessidade de deslocamento identificada. |
| **Resultados possíveis** | (a) concluído no prazo; (b) concluído com atraso; (c) não realizado; (d) espera abandonada por insegurança. |
| **Duração média (AS-IS)** | Tempo de viagem + 15-30 min de margem de segurança embutida pelo passageiro. |

*Tabela 3 – Ficha do processo P01*

**Stakeholders principais:** Passageiro (executa de ponta a ponta), Motorista e CCO da operadora (escala, decide cancelamento), SEMOB/GDF (quadro de horários), Canais digitais (DF no Ponto, Google Maps, Moovit), Rede informal/redes sociais (fonte não verificada).

**Recursos:** smartphone e canais digitais (consulta), GPS embarcado no veículo, sistema de bilhetagem, parada de ônibus e iluminação pública (infraestrutura física).

**Pools do diagrama:** (1) Passageiro; (2) Canais digitais de informação; (3) Empresa operadora (raias CCO e Motorista); (4) Rede informal de passageiros (pool fechado/caixa-preta, comunica-se só por mensagem).

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/01-processos-as-is.bpmn` (recorte da parte referente a P01)]

**Narrativa (resumida):** o passageiro consulta os canais digitais e, se a informação for insuficiente (sem GPS recente, só horário programado), recorre à rede informal ou estima pela experiência própria. Desloca-se e aguarda na parada. Se a espera excede a margem prevista, reconsulta; sem confirmação, escolhe entre pagar transporte alternativo, tentar outra linha ou desistir — **este é o desvio que caracteriza o "ônibus fantasma"**. A percepção de risco pode interromper a espera a qualquer momento. Na operadora, quando não há veículo/motorista disponível, o CCO cancela a viagem — mas **nenhum fluxo de mensagem informa o passageiro**: ele continua esperando por um veículo que nunca sairá da garagem.

| ID | Disfunção | Efeito |
|---|---|---|
| N01 | Dados de GPS indisponíveis/desatualizados; canal exibe horário programado como se fosse real. | Passageiro planeja com base em promessa, não fato. |
| N03 | Margem de segurança de 15-30 min embutida pelo passageiro. | Perda diária de produtividade. |
| N04 | Espera é o ponto de maior exposição, sem previsão de término. | Risco de segurança física. |
| N05 | Cancelamento decidido e registrado internamente, mas nenhuma mensagem informa quem está na parada. | **Causa raiz do "ônibus fantasma."** |
| N06 | Posição do veículo só chega ao passageiro quando ele aparece fisicamente na parada. | Informação tardia demais pra decidir. |

*Tabela 4 – Principais disfunções do processo P01*

---

## 4. Modelagem AS-IS — P04: Registrar e Tratar Ocorrência no Serviço

| Atributo | Descrição |
|---|---|
| **Objetivo** | Comunicar uma falha vivenciada e obter apuração, resposta e correção. |
| **Dono** | Compartilhado (passageiro inicia; ouvidoria e operadora apuram) — não há dono único, já é uma disfunção. |
| **Gatilho** | Ocorrência vivenciada (viagem não realizada, atraso, superlotação, insegurança). |
| **Resultados possíveis** | (a) não registrada; (b) registrada e resolvida; (c) registrada sem solução; (d) sem retorno no prazo. |
| **Duração média (AS-IS)** | De dias a 30 dias, prorrogáveis (Lei nº 13.460/2017, art. 16). |

*Tabela 5 – Ficha do processo P04*

**Stakeholders:** Passageiro reclamante, demais passageiros da linha (vivenciam mas não registram), atendente da ouvidoria, área técnica da SEMOB, SAC da operadora, redes sociais (canal informal).

**Recursos:** portal/telefone da ouvidoria, sistema de gestão de manifestações, canal de SAC, redes sociais, smartphone (evidências informais).

**Pools do diagrama:** (1) Passageiro; (2) Ouvidoria do GDF (raias Atendimento e Área técnica); (3) Empresa operadora (SAC); (4) Outros passageiros/redes sociais (pool fechado).

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/01-processos-as-is.bpmn` (recorte da parte referente a P04; é o mesmo arquivo combinado com P01)]

**Narrativa (resumida):** o passageiro avalia se vale a pena registrar — esforço concreto e imediato contra retorno distante e incerto. **Na maioria dos casos, o processo termina aqui, sem registro.** Decidindo registrar, aciona um ou mais canais em paralelo (ouvidoria, rede social, SAC da operadora) — três canais que não se comunicam e produzem três registros independentes do mesmo fato. A ouvidoria pode levar até 30 dias para responder. **Nenhuma das três rotas devolve informação a quem está, naquele momento, esperando na parada da mesma linha** — o registro serve à prestação de contas posterior, não à decisão de quem enfrenta o mesmo problema agora.

| ID | Disfunção | Efeito |
|---|---|---|
| N01 | **Subnotificação estrutural** — esforço alto, retorno distante e incerto. | Base oficial não reflete a realidade da parada. |
| N03 | Ciclo de resposta de até 30 dias (Lei 13.460/2017). | Serve à prestação de contas, não à decisão em tempo real. |
| N04 | Rede social é rápida, mas dispersa, não validada, não persiste. | Esforço do passageiro não vira conhecimento reutilizável. |
| N06 | Apuração delegada à própria empresa reclamada. | Assimetria e baixa confiança no resultado. |
| N07 | Sem validação cruzada entre manifestações. | Falha sistêmica só é vista com alto volume de reclamações. |
| N08 | Sem dono único do processo ponta a ponta. | Ninguém responde pelo resultado percebido pelo cidadão. |

*Tabela 6 – Principais disfunções do processo P04*

---

## 5. TO-BE com o Movecity — o processo com o sistema entregue

O TO-BE descreve o mesmo processo com o Movecity no lugar dos canais fragmentados, **limitado ao que foi entregue** (mergeado em `homolog` ou `main`) em 28/10/2026. Foi conferido contra o código, as issues e o registro de testes (`docs/qa/`). Na versão anterior, o diagrama previa três mecanismos que **não existem** e foram retirados: a posição do ônibus informada por passageiro a bordo (#199, aberta), a notificação do cancelamento pela operadora ao Movecity (não há integração) e o alerta push de cancelamento (#28 e #207, abertas).

**O mecanismo real:** (1) linhas, trajetos, paradas e horários previstos vêm da SEMOB por ingestão em lote para o banco; (2) a posição dos ônibus é lida ao vivo do feed da SEMOB, com cache de 20 s, e nunca é gravada; (3) cada tempo de chegada declara a fonte ("ao vivo", "previsto") ou mostra "Sem previsão no momento"; (4) a localização do usuário serve ao mapa, ao ETA e ao embarque e não é gravada; (5) as ocorrências reportadas ficam listadas por linha e passam a "Confirmada" com 3 confirmações de outros passageiros ("acidente" e "segurança" são exibidos de imediato) e expiram em 15 a 120 minutos.

**Pools:** Passageiro; Movecity (raias App e Backend); Empresa operadora, **sem alteração** (nenhuma mensagem do CCO ao Movecity); Ouvidoria do GDF, **mantida**, com ciclo de até 30 dias.

> **Este diagrama abrange P01 a P04.** P05 aparece como contexto paralelo da operadora.

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/02-processo-com-movecity.bpmn`]

| | **AS-IS manual** | **TO-BE com o Movecity, como entregue** |
|---|---|---|
| Fonte de posição | Canal sem indicar a origem do dado | Feed da SEMOB ao vivo, com a idade da posição |
| Horário programado × real | Programado exibido como real | Fonte declarada em cada tempo |
| Durante a espera | Reconsulta e pergunta a outros passageiros | Reconsulta com dado atualizado; **sem alerta proativo** |
| Cancelamento (CCO) | Preso na operadora | **Inalterado** |
| Reporte de ocorrência | 3 canais isolados | Reporte estruturado, por linha, com confirmação cruzada |
| Canal formal | Ciclo de até 30 dias | **Mantido** |

*Tabela 7 – Comparativo processo a processo*

### Quadro AS-IS × TO-BE por disfunção

| # | Funcionalidade do Movecity (issue / PR) | Caso de teste (`docs/qa/execucao-casos-p1.md`) | Situação | O que continua sem solução |
|---|---|---|---|---|
| D1 | Posição ao vivo e ETA (#16, #19, #159, #179; PRs #120, #124, #154, #160, #185) | CT-MAP-07, CT-ETA-01, CT-MAP-08 (aprovados) | **Em parte** | O cancelamento não chega ao passageiro (sem integração com a operadora; #28 aberta) |
| D2 | Fonte declarada em cada tempo (#179, PRs #181 a #185; #173) | CT-ETA-01, CT-ETA-02, CT-PAR-04 (aprovados); CT-ETA-04 (em parte) | **Tratada** | Precisão do ETA não medida em campo; só parte da frota informa linha e sentido no feed |
| D3 | Planejador de rota, tempo nas paradas, busca de parada, favoritos (#20, #21, #25, #190) | CT-ROT-01, 02, 05 (aprovados); CT-ROT-06 (em parte) | **Em parte** | Efeito sobre a margem do passageiro não medido |
| D4 | ETA declarado; reporte imediato de "segurança" (#23) | CT-COL-01 (aprovado) | **Não resolvida** | Infraestrutura da parada fora do alcance do app |
| D5 | Posições que se atualizam sozinhas e reconsulta (#16) | CT-MAP-07 (aprovado); CT-ETA-03 (não executado) | **Em parte** | Sem alerta proativo: #27 sem canal de entrega, #207 não feita |
| D6 | Reporte em poucos toques (#23, PR #162) | CT-COL-01, CT-COL-03 (aprovados) | **Em parte** | Taxa de reporte não medida; sem usuários reais |
| D7 | Ocorrência listada na hora (#24, PR #180) | CT-COL-04 (em parte), CT-COL-05 (aprovado) | **Em parte** | Ouvidoria segue em dias; sem push da ocorrência |
| D8 | Ocorrência estruturada, confirmada e persistente (#24, #26, PR #209) | CT-COL-01, CT-COL-04, CT-COL-05 | **Tratada** | A confirmação (#26) não tem caso manual; só vale dentro do Movecity |
| D9 | Confirmação cruzada por 3 passageiros (#26) | sem caso manual | **Em parte** | Sem dono único; a visão fala em 2 reportes, o servidor exige 3 e a tela anuncia 2 (#249) |

*Tabela 8 – Disfunções × funcionalidades do Movecity (estado em 28/10/2026)*

Resultado: **duas tratadas, seis em parte, uma não resolvida** (a versão anterior dava cinco como resolvidas). Lacunas transversais: nenhum alerta de atraso, cancelamento ou rota preferida chega ao usuário (só o aviso de proximidade da parada de destino tem canal, por Web Push, sem validação em aparelho, #200); não houve validação em campo nem teste com usuários reais.

---

## 6. Processo de Desenvolvimento Assistido por IA e Defesa do seu Uso

> **Nota de escopo:** meta-processo interno do projeto, fora do inventário da seção 2. O detalhamento está na versão completa e em `docs/diagramas/processos/03-processo-desenvolvimento-ia.bpmn`.

**Todo o código do Movecity foi gerado por agentes de IA, conduzidos por seis estudantes que especificaram (issue, cenários BDD, diagrama de sequência), revisaram e aprovaram.** Por regra de autoria, os commits não levam assinatura de ferramenta; a declaração é do grupo.

| Atributo | Descrição |
|---|---|
| **Objetivo** | Transformar uma User Story em incremento validado em produção, com agente de IA operando em nome do desenvolvedor. |
| **Dono** | O desenvolvedor responsável. A IA é recurso, nunca dona do processo. |
| **Gatilho** | US selecionada no Sprint Planning, com DOR atendido. |

*Tabela 9 – Ficha do processo de desenvolvimento assistido por IA*

**Pools:** Desenvolvedor; Revisor; Pipeline CI/CD.

[Inserir imagem do fluxo — diagrama BPMN renderizado de `docs/diagramas/processos/03-processo-desenvolvimento-ia.bpmn`]

**Fluxo:** o desenvolvedor lê a US e o diagrama de sequência, desenvolve com o agente, testa localmente, commita (Conventional Commits) e abre PR. O CI roda; o revisor aprova pelo botão "Review changes" → "Approve" (comentário de texto não conta). O merge e o bypass são decisões humanas, sempre registradas. Deploy automático, validação real em homolog e produção, DoD em dois níveis.

| ID | Risco | Como o processo mitiga |
|---|---|---|
| R1 | Confiança excessiva na IA | Aprovação formal prevista antes do merge; a conferência de como os PRs do orquestrador foram mergeados está pendente |
| R2 | Bypass de proteção de branch | Só em teste deliberado do pipeline; decisão humana, registrada na issue |
| R3 | Perda de rastreabilidade de autoria | Commits e PRs não citam a IA; a participação é declarada nos documentos |
| R4 | Comentário confundido com aprovação | Só vale `reviewDecision: APPROVED` |
| R5 | IA resolver divergência plano/código sozinha | A divergência é exposta ao desenvolvedor |

*Tabela 10 – Riscos de governança e mitigação*

**O processo em números** (`gh` de 29/10; `docs/guia-apresentacao.md`, 3; `docs/qa/`): 103 issues e 155 PRs (143 mergeados; 11 fechados sem merge, por retrabalho e consolidação, nenhum por reprovação de qualidade); 283 commits entre 15/08 e 29/10 (cerca de 11 semanas); 1.640 testes automatizados passando no CI de 28/10 (844 backend, 796 frontend); cobertura de 93,7% e 89,1% (medida em 16/10); 41 dos 42 PRs `feat`/`fix` desde 22/09 com teste; 26 defeitos catalogados, a maioria de conexão entre as peças, 4 em produção; 49 casos manuais executados em produção (32 aprovados, 11 em parte ou com ressalva, 1 reprovado por configuração, 3 não verificáveis, 2 pendentes). Falhas reconhecidas: aprovação por comentário confundida com review formal (#35); `X-User-Id` repassado pelo cliente (#188); `/auth/refresh` inexistente (#212); tokens em `localStorage` (#253, aberta).

### Defesa do uso de IA no desenvolvimento

**Legitimidade acadêmica:** a IA escreveu o código; é dos estudantes o que ela não decide sozinha: problema, escopo, arquitetura, especificação, revisão, aprovação, merge e verificação em produção.

**Rastreabilidade e governança:** DOR, aprovação formal, CI, Conventional Commits e DoD em dois níveis são pontos de controle auditáveis. Não se promete "nenhuma exceção" antes da conferência dos PRs do orquestrador.

**Qualidade e produtividade:** os números descrevem o que foi entregue; **não há medição de ganho de produtividade** (sem grupo de controle).

**Limites:** revisor único e mediana de 18 min até o merge de um PR; autoria de PRs desigual; testes que mockam integrações; sem ambiente de homologação separado; um único avaliador de usabilidade; sem validação em campo; raio de embarque em 100 km na demonstração (regra real: 100 m).

---

## 7. Síntese das Disfunções e Próximos Passos

A modelagem revela que a informação necessária **já existe** — no GPS do veículo, na escala do CCO, na decisão de cancelamento, na experiência dos passageiros. O que não existia era um caminho que a leve, em tempo útil, a quem está na parada.

| # | Disfunção | Processo | Situação com o Movecity entregue |
|---|---|---|---|
| D1 | Posição e cancelamento não atravessam a fronteira do pool | P01 | Em parte (posição sim, cancelamento não) |
| D2 | Horário programado exibido como se fosse real | P01 | Tratada |
| D3 | Margem de segurança e consultas manuais | P01 | Em parte (efeito não medido) |
| D4 | Espera é o ponto de maior exposição a risco | P01 | Não resolvida |
| D5 | Decisão repetida sem dado novo | P01 | Em parte (sem alerta proativo) |
| D6 | Maior parte das ocorrências nunca é registrada | P04 | Em parte (taxa não medida) |
| D7 | Ciclo em dias; necessidade em minutos | P04 | Em parte (só entre passageiros) |
| D8 | Informação colaborativa dispersa e não persistente | P04 | Tratada |
| D9 | Sem dono único, sem validação cruzada | P04 | Em parte (3 confirmações; sem dono) |

*Tabela 11 – Síntese das disfunções e situação (D1-D9 detalhadas na versão completa)*

**Próximos passos:** (1) inserir as imagens dos diagramas nos placeholders (arquivos `.bpmn` prontos; o de `02` foi corrigido); (2) validar a modelagem com usuários reais do STPC/DF — **não feito**; (3) conferência do mecanismo com a arquitetura — **concluída em 28/10** contra o código, e o diagrama foi corrigido; (4) definir indicadores do processo (espera percebida, taxa de reporte, tempo até a informação chegar) — **aberto**; (5) alerta de cancelamento (#28), push dos alertas (#207) e integração com a operadora — **aberto**; (6) validação em campo do ETA, do aviso de proximidade e do Web Push (#200) — **aberto**; (7) voltar o raio de embarque a 100 m depois da defesa.

**Pontos a confirmar:** denominação e prazos **praticados** pela ouvidoria do GDF; vigência das funcionalidades do aplicativo oficial (DF no Ponto); periodicidade e SLA do feed da SEMOB (endpoints sem documentação pública); fluxo interno de cancelamento nas operadoras (entrevista); limiar de confirmação (visão: 2; servidor: 3; tela: 2, #249); segurança da sessão (tokens em `localStorage`, #253); conferência dos PRs do orquestrador frente à regra de aprovação.

---

## 8. Referências

- ABPMP. **BPM CBOK — Guia para o Gerenciamento de Processos de Negócio.** Association of Business Process Management Professionals.
- BRASIL. **Lei nº 13.460, de 26 de junho de 2017.**
- CAROLI, P. **Lean Inception: como alinhar pessoas e construir o produto certo.** Editora Caroli, 2018.
- CGDF. **Painel de Ouvidoria do Distrito Federal.** Controladoria-Geral do Distrito Federal, 2026.
- GRUPO SEGURANÇA NO TRANSPORTE. **Documento de Arquitetura de Software — Movecity.** Disponível em: `docs/documento_arquitetura.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Documento de Visão — Movecity.** Disponível em: `docs/documento_visao.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Manual do Sprint Movecity — do Backlog ao Deploy.** Disponível em: `docs/manual-sprint.md`.
- GRUPO SEGURANÇA NO TRANSPORTE. **Repositório do projeto Movecity.** GitHub, 2026. Disponível em: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb>. Acesso em: 28 set. 2026.
- IPEDF. **Pesquisa Distrital por Amostra de Domicílios (PDAD).** Instituto de Pesquisa e Estatística do Distrito Federal, 2022.
- OMG. **Business Process Model and Notation (BPMN), Version 2.0.** Object Management Group.

## Anexos

Anexados a esta entrega: (1) a **versão completa** deste documento (`docs/analise-processos-negocio.md`), com o detalhamento elemento-a-elemento de cada diagrama BPMN; (2) os 3 arquivos-fonte `.bpmn` (`01-processos-as-is.bpmn`, `02-processo-com-movecity.bpmn`, `03-processo-desenvolvimento-ia.bpmn`); (3) os slides de apresentação (a montar).
