# Resumo Executivo de Qualidade — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/resumo-executivo.md>

**Atualizado em 28/10/2026 · testes manuais em produção (`homolog` publicada) · testes automatizados contados no CI em 28/10 · cobertura e CI medidos em 16/10/2026 (`07c9edc`) · detalhes e fontes em [`README.md`](README.md)**

## Em uma frase

O projeto tem uma base automatizada ampla e verde e, agora, **os 49 casos manuais foram executados em produção**: 33 aprovados, 10 aprovados com ressalva, 1 reprovado por configuração, 3 que só se provam em campo e 2 que dependem de simulação de posição. A execução achou 11 defeitos novos, e a conexão entre as peças segue como o ponto mais frágil.

## Números

| O que | Valor | Fonte |
|---|---|---|
| Testes automatizados | **1.640** passando (844 backend, 796 frontend), contados no log do CI em 28/10 | [`relatorio-testes-unitarios.md`](relatorio-testes-unitarios.md), execução `40689632241` (`48483be`). Em 16/10 eram 1.260 |
| Cobertura do código de produção | backend **93,7%**; frontend **89,1%** (só dos arquivos importados pelos testes), de 16/10 | [`relatorio-cobertura-e-defeitos.md`](relatorio-cobertura-e-defeitos.md) |
| Disciplina de teste nos PRs | **27 de 27** PRs `feat`/`fix` desde 22/09 trazem arquivo de teste | `gh pr view --json files` |
| CI de PR | 94% verde na Sprint 3 (33 de 35), contra 79% na Sprint 2 | `gh run list` |
| **Casos manuais executados** | **49 de 49** | [`execucao-casos-p1.md`](execucao-casos-p1.md), "Quadro geral" |
| Resultado dos 49 | **33 aprovados · 10 com ressalva · 1 reprovado por configuração · 3 não verificáveis · 2 pendentes** | idem |
| Defeitos catalogados | **24** (13 até 16/10 e 11 achados em 27 e 28/10): 10 de conexão entre as peças e 14 de regra, dado ou interface | [`relatorio-cobertura-e-defeitos.md`](relatorio-cobertura-e-defeitos.md) |
| Usabilidade (Nielsen) | 10 heurísticas avaliadas, por **um avaliador**; 4 delas com achado de severidade 3, todos com issue aberta ou já corrigidos | [`avaliacao-usabilidade-nielsen.md`](avaliacao-usabilidade-nielsen.md) |

## Os 49 casos manuais, por estado

| Estado | Qtd | Casos |
|---|---|---|
| Aprovado | 33 | a lista completa está no "Quadro geral" da execução |
| Aprovado em parte ou com ressalva | 10 | AUT-01, AUT-03, AUT-05, COL-04, ETA-04, PAR-03, ROT-06, ROT-07, SEG-01, VIA-02 |
| Reprovado por configuração | 1 | VIA-01: o embarque é aceito longe do ônibus porque o raio está em 100 km em produção, por decisão do grupo para demonstrar o "Peguei este ônibus" |
| Não verificável hoje | 3 | NOT-02 (sem canal de entrega), VIA-07 e VIA-08 (só em campo, com o raio em 100 m e um ônibus se aproximando) |
| Pendente | 2 | MAP-03 e ETA-03 (exigem localização simulada pelo DevTools, feita à mão) |

Dos 18 casos P1, 4 reprovaram na primeira execução (AUT-01, AUT-03, PAR-01 e PAR-04) e viraram defeitos; depois da correção passaram na revalidação.

## O que a análise mostra

1. **Os defeitos relevantes são de conexão, não de regra.** Dos 24 defeitos, 10 são de conexão entre as peças (dependência faltando, contrato front ↔ Gateway, ordem de middleware, rotas públicas, cabeçalhos duplicados, import perdido num merge, FK sem o modelo carregado no serviço isolado). Quatro foram relatados como ocorridos em produção.
2. **A execução manual achou o que o CI não achava.** Foram 11 defeitos novos em 27 e 28/10, entre eles o `/auth/refresh` inexistente, as preferências de notificação com erro 500 em produção, a sessão expirada que o app mostrava como "nenhum ônibus" e as coordenadas do usuário na URL. Todos passam pelo mesmo ponto: os testes automatizados mockam a vizinhança.
3. **Correções validadas em produção em 27 e 28/10:** cadastro sem aceite dos termos (#211), rota de refresh e **renovação automática da sessão** (#212, #221; a rede da aba mostrou 401, `POST /auth/refresh` 200 e a consulta refeita com 200), tela e preferências de alertas (#29, #213), saídas do terminal com horário passado (#215), "Parada sem nome" (#232) e coordenadas na URL (#231).
4. **E-mail de recuperação de senha:** passou a funcionar em 28/10 por SMTP (#237). O e-mail chegou à caixa de entrada, o link abriu no celular e a nova senha foi definida. A **confirmação de conta por e-mail não existe** (a conta entra direto) e o texto do cadastro foi corrigido (#230).

## Riscos e lacunas

| Risco | Situação |
|---|---|
| Sem ambiente de homologação separado | `homolog` publica na produção da Vercel e o backend compartilha apps e banco; casos que gravam dados afetam o ambiente visível |
| Gateway ↔ serviços e front ↔ Gateway só com mocks | Segue sem teste automatizado de ponta a ponta; o que cobre isso hoje é a execução manual em produção |
| **Raio de embarque em 100 km** | Decisão do grupo (28/10): manter só para demonstrar o "Peguei este ônibus", dizendo isso na defesa. A regra de uso real é 100 m; a regra "ônibus chegando" (#191) só se prova com o raio em 100 m |
| Sem validação em campo | Tolerância de ETA (2 a 10 min) e regra do ônibus chegando não medidas; VIA-07 e VIA-08 só em campo |
| Alertas sem entrega | A tela de preferências salva, mas não há push (#207) nem alerta de cancelamento (#28) |
| Avaliação de usabilidade com um avaliador | O método pede 3 a 5 avaliadores independentes; não houve teste com usuários reais |
| Cobertura não é medida no CI | E o Jest mede só os arquivos importados (3 de 43 ficam de fora); os números são de 16/10 |
| Issues abertas | #216 (embarque: causa de configuração), #233 (investigar "nenhuma linha liga esses dois pontos"), #234 (build depende do Google Fonts), #236 (dica do "Buscar parada"), #243 (mensagens sem acento) |

## Próximos passos

1. Fazer à mão MAP-03 e ETA-03 (DevTools, Sensors) e levar VIA-07 e VIA-08 para o ensaio da defesa.
2. Promover `homolog` para `main` (#203) e validar em produção o que subiu.
3. Regerar os números automatizados e de cobertura na véspera da defesa (procedimento no `README.md`), já com os testes dos PRs recentes.
4. Repetir a avaliação de usabilidade com 2 ou 3 pessoas do grupo, cada uma por conta própria.
5. Depois da defesa: voltar o raio de embarque a 100 m, validar a regra do ônibus chegando e medir o ETA em campo.
