# Resumo Executivo de Qualidade — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/resumo-executivo.md>

**Sprint 3, 16/10/2026 · `homolog` @ `07c9edc` · detalhes e fontes em [`README.md`](README.md)**

## Em uma frase

O projeto tem uma base automatizada ampla e verde (1.260 testes, 0 falhas), mas a qualidade ainda não foi **validada de ponta a ponta**: os casos manuais por US existem e não foram executados, e a conexão entre as peças continua sendo o ponto mais frágil.

## Números

| O que | Valor |
|---|---|
| Testes automatizados | **1.260** passando (671 backend contra Postgres 16 com migrations, 589 frontend) |
| Evolução | de 297 (registro original da #151) para 1.260 |
| Cobertura do código de produção | backend **93,7%**; frontend **89,1%** (só dos arquivos importados pelos testes) |
| Disciplina de teste nos PRs | **27 de 27** PRs `feat`/`fix` desde 22/09 trazem arquivo de teste (+14.835 linhas de teste nos 31 PRs fora de promoção) |
| CI de PR | 94% verde na Sprint 3 (33 de 35), contra 79% desde a Sprint 2 (60 de 76); mediana de 1,1 min |
| Casos de teste manuais | **49** escritos, **0** executados; 27 USs e cards na matriz de rastreabilidade |

## O que a análise mostra

1. **Os defeitos relevantes são de conexão, não de regra.** Dos 13 defeitos catalogados, 8 são de integração (dependência faltando, contrato front ↔ Gateway, ordem de middleware, rotas públicas, cabeçalhos duplicados, import perdido num merge). Quatro chegaram a produção.
2. **O CI pega o que está ao seu alcance.** Os 16 vermelhos desde a Sprint 2 foram, em sua maioria, em migrations e no boot dos serviços, antes do merge. Em 16/10 o Jest barrou um import perdido que o Git não marcava como conflito.
3. **O teste real continua insubstituível.** Linhas circulares sem ETA, o embarque recusado fora de 100 m e vários achados de interface só apareceram com dados e uso reais.

## Riscos e lacunas

| Risco | Situação |
|---|---|
| Sem ambiente de homologação separado | O frontend de `homolog` publica na produção da Vercel e o backend compartilha apps e banco; casos de teste que gravam dados afetam o ambiente visível |
| Gateway ↔ serviços e front ↔ Gateway só com mocks | É a causa de 8 dos 13 defeitos |
| Sem validação em campo | Tolerância de ETA (2 min até 10 min), raio de embarque e regra do ônibus chegando não medidos |
| Cobertura não é medida no CI | E o Jest mede só os arquivos importados (3 de 43 ficam de fora) |
| Aviso com a tela bloqueada | Não existe (Web Push em desenvolvimento) |

## Próximos passos sugeridos

1. Executar os 18 casos P1 em `homolog` e registrar o estado (regressão mínima antes da promoção para `main`).
2. Entregar o contrato front ↔ Gateway e o teste do Gateway com HTTP real (Fase 2 da #151, itens 2 e 3).
3. Medir cobertura no CI e incluir os arquivos hoje fora da medição.
4. Validar em campo o ETA e o embarque, e definir quem separa os ambientes (a #42 consta como fechada, mas os workflows de deploy não mudaram).
5. Regerar estes relatórios ao fim de cada sprint (procedimento no `README.md`).
