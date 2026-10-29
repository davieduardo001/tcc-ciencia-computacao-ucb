# Distribuição de User Stories — Movecity

**Critério:** agrupamento por épico/tema para manter coesão técnica. Cada membro fica responsável por um conjunto de funcionalidades relacionadas, facilitando rastreamento e revisão.

---

## @davieduardo001 — Orquestração e Gerenciamento

| # | Responsabilidade / User Story |
|---|---|
| — | Gerenciamento de backlog e priorização |
| — | Orquestração da equipe e cerimônias |
| — | Revisão de PRs e merge nas branches principais |
| — | Manutenção da documentação arquitetural |
| #31 | Gerenciar Ciclo de Vida da Sessão (Gateway como Proxy) |
| #34 | Documento de Arquitetura de Software |
| #12 | Login via Provedor Social (Google) |
| #17 | Visualizar Trajeto e Paradas da Linha no Mapa |

### Detalhes da US #31 — Gateway como Proxy

O Gateway é o **ponto único de entrada** para todas as requisições do frontend.
Nenhum serviço backend se comunica com o banco diretamente — tudo passa pelo Gateway.

**Endpoints de Proxy:**

| Endpoint | Método | Destino |
|----------|--------|---------|
| `/api/auth/login` | POST | Auth Service |
| `/api/auth/registrar` | POST | Auth Service |
| `/api/auth/refresh` | POST | Auth Service |
| `/api/auth/logout` | POST | Auth Service |
| `/api/mobilidade/*` | GET/POST/PUT/DELETE | Mobilidade Service |
| `/api/colaboracao/*` | GET/POST/PUT/DELETE | Colaboracao Service |

**Arquivos do Gateway:**

| Arquivo | Responsabilidade |
|---------|------------------|
| `middleware.py` | Valida JWT do cookie em cada request |
| `jwt_validator.py` | Decodifica e valida tokens JWT |
| `dependencies.py` | `get_usuario_atual` para endpoints protegidos |
| `proxy.py` | Proxy genérico para serviços backend |
| `cookies.py` | Helper para setar/limpar cookies httpOnly |
| `config.py` | Configuração das URLs dos serviços |
| `routes.py` | Endpoints de proxy (auth, mobilidade, colaboracao) |

---

## @brenouchihar — Épico Autenticação (5 USs)

| # | User Story |
|---|---|
| #32 | Criar Termos de Uso e Política de Privacidade |
| #10 | Realizar Login com E-mail e Senha |
| #11 | Criar Nova Conta de Usuário |
| #13 | Recuperação de Senha (Esqueci minha senha) |

---

## @Kelvin963 — Épico Mapa & Rastreamento — Núcleo (3 USs)

| # | User Story |
|---|---|
| #14 | Visualizar Mapa com Localização Atual |
| #15 | Buscar Linha por Número |
| #16 | Rastrear Posição do Ônibus em Tempo Real |

---

## @louisassis — Épico Mapa & Rastreamento — Detalhes e Rotas (4 USs)

| # | User Story |
|---|---|
| #18 | Ver Detalhes de uma Parada |
| #19 | Ver Tempo Estimado de Chegada do Ônibus até Minha Parada |
| #20 | Calcular Rota de Origem até Destino por Ônibus |
| #21 | Buscar Parada por Nome ou Endereço |

---

## @Vitoria-Albuquerque — Colaboração (Reporte) + Protótipo (5 USs + protótipo)

| # | User Story |
|---|---|
| #23 | Reportar Ocorrência em uma Linha |
| #24 | Visualizar Ocorrências Reportadas por Outros Passageiros |
| #25 | Salvar Rota Favorita |
| #26 | Confirmar Ocorrência Reportada por Outro Passageiro |
| #30 | Visualizar Tutorial no Primeiro Acesso |
| #33 | Criação do Protótipo — telas do épico Colaboração e Mapa |

---

## @gualbertonathalia — Colaboração (Alertas) + Termos + Protótipo (5 itens + protótipo)

| # | User Story |
|---|---|
| #22 | Receber Notificações de Rotas Preferidas |
| #27 | Receber Alerta de Atraso na Linha Acompanhada |
| #28 | Receber Alerta de Cancelamento de Viagem |
| #29 | Gerenciar Preferências de Notificação |
| #33 | Criação do Protótipo — telas de Autenticação e Onboarding |

---

## Estado atual das USs (28/10/2026)

As seções por pessoa acima registram a **distribuição planejada** no início do projeto. Esta seção e as duas seguintes registram o que aconteceu até 28/10/2026, com base nas issues (`gh issue list`), nos PRs mergeados (`gh pr list --state merged`) e no [relatório de execução dos casos](qa/execucao-casos-p1.md).

**Como ler:**
- **Responsável (issue):** assignee atual da issue. Em várias USs ele difere do plano das seções acima, e em outras quem abriu o PR é outra pessoa; por isso há uma coluna com os autores dos PRs.
- **Estado:** *Entregue em `main`* (issue fechada, promovida para produção); *Entregue em `homolog`* (PR mergeado, aguarda a promoção para `main`; como o workflow de deploy publica `homolog` na produção da Vercel e do Fly.io, o código já está no ar, ver o [plano de testes](qa/plano-de-testes.md)); *Aberta* (sem PR mergeado); *Fora de escopo* (trabalho futuro, segundo a issue #206).
- A conta `ngualbertolopes` é a que aparece nas issues e PRs atribuídos à Nathália Gualberto; o plano original cita `@gualbertonathalia`. As duas contas são da mesma pessoa: os perfis do GitHub têm o mesmo nome (Nathália Gualberto Lopes).

### USs do planejamento original (#10 a #33)

| # | User Story | Responsável (issue) | PRs (autor) | Estado |
|---|---|---|---|---|
| #10 | Login com e-mail e senha | @ngualbertolopes | #75 (@ngualbertolopes) | Entregue em `main` |
| #11 | Criar nova conta | @Vitoria-Albuquerque | #52 (@Vitoria-Albuquerque) | Entregue em `main` |
| #12 | Login via Google | @ngualbertolopes | #91 (@ngualbertolopes) | Entregue em `main` |
| #13 | Recuperação de senha (backend) | @Kelvin963 | #87 (@Kelvin963) | Entregue em `main` (telas na #133, abaixo) |
| #14 | Mapa com localização atual | @louisassis | #85 (@louisassis) | Entregue em `main` |
| #15 | Buscar linha por número | @Vitoria-Albuquerque | #99 (@Vitoria-Albuquerque) | Entregue em `main` |
| #16 | Rastrear ônibus em tempo real | @davieduardo001 | #120, #124 (@davieduardo001) | Entregue em `main` |
| #17 | Trajeto e paradas da linha | @davieduardo001 | #105, #108 a #111, #114 (@davieduardo001) | Entregue em `main` |
| #18 | Detalhes de uma parada | @louisassis | #169 (@louisassis) | Entregue em `main` |
| #19 | ETA do ônibus até a minha parada | @davieduardo001 | #154 (@davieduardo001), #160 (@Vitoria-Albuquerque) | Entregue em `main` |
| #20 | Calcular rota por ônibus | @davieduardo001 | #116, #119 (@davieduardo001) | Entregue em `main` |
| #21 | Buscar parada por nome ou endereço | @louisassis | #197 (@louisassis) | Entregue em `main` (promovida pela #203) |
| #22 | Notificações de rotas preferidas | @brenouchihar | #94 (@brenouchihar) | Entregue em `main` (sem canal de entrega ao usuário; ver #207) |
| #23 | Reportar ocorrência | @Vitoria-Albuquerque | #162 (@Vitoria-Albuquerque) | Entregue em `main` |
| #24 | Ver ocorrências de outros passageiros | @Vitoria-Albuquerque | #180 (@Vitoria-Albuquerque) | Entregue em `main` (promovida pela #203) |
| #25 | Salvar e visualizar rota favorita | @brenouchihar | #176 (@brenouchihar) | Entregue em `main` (promovida pela #203) |
| #26 | Confirmar ocorrência de outro passageiro | @brenouchihar | #209 (@brenouchihar) | Entregue em `homolog` (issue ainda aberta) |
| #27 | Alerta de atraso | @ngualbertolopes | #152 (@ngualbertolopes) | Entregue em `main` (sem canal de entrega ao usuário; ver #207) |
| #28 | Alerta de cancelamento de viagem | @Kelvin963 | nenhum | **Aberta** (planejada na Sprint 4, sem PR mergeado) |
| #29 | Preferências de notificação | @Kelvin963 | #127 (@Kelvin963, backend); #223 e #224 (@davieduardo001, tela `/alertas` e correção) | Backend em `main`; tela entregue em `homolog` (issue reaberta em 27/10 por falta da tela) |
| #30 | Tutorial no primeiro acesso | @Kelvin963 | #158 (@Kelvin963) | Entregue em `main` |
| #31 | Ciclo de vida da sessão (Gateway como proxy) | @davieduardo001 | #56, #66 (@davieduardo001) | Entregue em `main` |
| #32 | Termos de uso e política de privacidade | @gualbertonathalia, @brenouchihar, @Kelvin963 | sem PR de código: o texto dos Termos foi postado como comentário da issue (12/06/2026, @brenouchihar) | Issue fechada |
| #33 | Protótipo de alta fidelidade | @Vitoria-Albuquerque, @gualbertonathalia | sem PR de código: protótipo publicado no GitHub Pages (link na issue, 18/06/2026, @Vitoria-Albuquerque); páginas HTML versionadas em `prototipo-alta-fid/` (commit 6d098c3, 18/06/2026) | Issue fechada |

### USs criadas depois do planejamento (Sprints 2 a 4)

| # | User Story | Responsável (issue) | PRs (autor) | Estado |
|---|---|---|---|---|
| #133 | Recuperação de senha no aplicativo (rota no Gateway e telas) | @brenouchihar | #153 (@brenouchihar) | Entregue em `main`. O envio do e-mail por SMTP (#237, PR #238) está em `homolog` |
| #136 | Instalar o Movecity na tela inicial (PWA) | @davieduardo001 | #137 (@davieduardo001) | Entregue em `main` (promovida pela #142) |
| #159 | ETA real da rota planejada | @Vitoria-Albuquerque | #160 (@Vitoria-Albuquerque) | Entregue em `main` |
| #171 | Pegar o ônibus (indicar embarque e acompanhar a viagem) | @Kelvin963 | #186, #187 (@Vitoria-Albuquerque), #191 (@davieduardo001) | Entregue em `main` (promovida pela #203). Atribuída ao @Kelvin963 e entregue pela @Vitoria-Albuquerque (confirmado pelo grupo) |
| #172 | Alerta de proximidade da parada | @ngualbertolopes | #178 (@ngualbertolopes), #194 (@davieduardo001) | Entregue em `main` (promovida pela #203) |
| #190 | Paradas de subir e descer na rota, com o tempo do ônibus | @davieduardo001 | #191, #193 (@davieduardo001) | Entregue em `main` (promovida pela #203) |
| #195 | Alerta de proximidade com a tela bloqueada (Web Push) | @davieduardo001 | #196 (@davieduardo001) | Entregue em `main`; o grupo testou o Web Push em iPhone com resultado funcional (sem evidência registrada); a #200 segue aberta |
| #199 | Fallback colaborativo da posição do ônibus, com consentimento | @ngualbertolopes | nenhum | **Aberta** (planejada na Sprint 4, sem PR mergeado) |
| #207 | Notificações push dos alertas de atraso e das rotas preferidas | @louisassis | nenhum | **Aberta** (planejada na Sprint 4, sem PR mergeado) |
| #115 | Planejar viagem por horário (motor GTFS + RAPTOR) | @davieduardo001 | nenhum | **Fora de escopo** (trabalho futuro, #206) |
| #118 | Ver horários de operação da linha | @davieduardo001 | nenhum | **Fora de escopo** (trabalho futuro, #206) |

### Cards de sprint, correções e itens de apoio (não contam como US)

| # | Card | Responsável (issue) | PRs (autor) | Estado |
|---|---|---|---|---|
| #97, #143 | Melhorias de interface e adaptação ao protótipo v3 | @Vitoria-Albuquerque | #131 (@davieduardo001), #166 e #168 (@Vitoria-Albuquerque) | Entregue em `main` |
| #132, #138, #140 | Interface do mapa v3 e correções de navegação no celular | @davieduardo001 | #135, #139, #141 (@davieduardo001) | Entregue em `main` |
| #173 | Corrigir a hora do ETA (mapeamento entre paradas) | @davieduardo001 | #177 (@davieduardo001), #185 (@Vitoria-Albuquerque) | Entregue em `main` |
| #174 | Follow-up da US #18 | @louisassis | #192 (@davieduardo001) | Entregue em `main` |
| #179 | Consolidar navegação, rotas e ETA da parada | @Vitoria-Albuquerque | #181 a #185 (@Vitoria-Albuquerque) | Entregue em `main` |
| #188 | `X-User-Id` repassado pelo cliente | @Vitoria-Albuquerque | #189 (@Vitoria-Albuquerque) | Entregue em `main` |
| #201 | Remover "Nova Viagem" da barra lateral | @davieduardo001 | #202 (@davieduardo001) | PR mergeado antes da promoção #203; issue ainda aberta |
| #200 | Chaves VAPID pelo GitHub Actions e validação do Web Push em aparelho | @davieduardo001 | #210 (@davieduardo001) | Chaves no CI entregues em `homolog`; validação em aparelho **aberta** |
| #211, #212, #213 | Defeitos: termos no cadastro, `/auth/refresh`, preferências com usuário inexistente | sem assignee | #218, #224 (@davieduardo001) | Corrigidos em `homolog` (issues abertas) |
| #214, #215, #216 | Defeitos da parada e do embarque (o #214 foi reclassificado como comportamento da #179) | sem assignee | #219, #225 (@davieduardo001) | Corrigidos em `homolog` (issues abertas) |
| #217 | Folha única com 3 alturas no celular | sem assignee | #220 (@davieduardo001) | Entregue em `homolog` |
| #221 | Sessão expirada sem renovar nem pedir login | sem assignee | #222 (@davieduardo001) | Corrigido em `homolog` |
| #227 | Botão de perfil sem ação na barra de cima | sem assignee | #228 (@davieduardo001) | Corrigido em `homolog` |
| #230, #237 | Mensagens sobre e-mail e envio da recuperação de senha por SMTP | sem assignee | #238 (@davieduardo001) | Entregue em `homolog` |
| #231, #232 | Coordenadas na URL ao tocar em "Ir" e "Parada sem nome" nos cards de rota | sem assignee | #239, #240 (@davieduardo001) | Corrigidos em `homolog` |
| #233, #234, #236, #243 | Rota sem resultado a investigar, build com Google Fonts, dica de "Buscar parada" no desktop, acentos nas mensagens de redefinição | sem assignee | nenhum | Abertas |
| #208 | Alinhamento da interface com boas práticas de UX | @Vitoria-Albuquerque | nenhum | Aberta (Sprint 4) |
| #204, #205 | Documentação final; slides e roteiro da defesa | @davieduardo001; @Vitoria-Albuquerque | #204: #226, #229, #235, #241, #242, #244 (@davieduardo001); #205: nenhum | Abertas (Sprint 4) |
| #151 | Estratégia de testes: plano QA, relatórios e testes de conexão | @davieduardo001 | #198 (@davieduardo001) | Fase 1 (`docs/qa/`) em `main`; a Fase 2 (relatório de testes no CI e contrato front↔gateway) segue aberta |

> A seção de cards não é exaustiva: issues administrativas e do Sprint 0 (#1 a #9, #35 a #62, #83, #92 e outras) estão fechadas e não geram caso de teste. Os guarda-chuvas das sprints são #90 (Sprint 1), #144, #175 e #206.

---

## Resumo

### Distribuição planejada (Sprints 0 a 2)

| Responsável | Escopo | Qtd |
|---|---|---|
| @davieduardo001 | Orquestração + Backlog + #31 + #34 | — |
| @brenouchihar | Autenticação | 5 |
| @Kelvin963 | Mapa & Rastreamento (núcleo) | 3 |
| @louisassis | Mapa & Rastreamento (detalhes) | 4 |
| @Vitoria-Albuquerque | Colaboração (reporte) + Protótipo (#33) | 5 + protótipo |
| @gualbertonathalia | Colaboração (alertas) + Termos + Protótipo (#33) | 5 + protótipo |
| **Total USs** | | **24** |

### Estado em 28/10/2026

Contagem das tabelas "USs do planejamento original" (24) e "USs criadas depois do planejamento" (11), ou seja, 35 USs:

| Estado | USs | Qtd |
|---|---|---|
| Entregue em `main` | #10 a #25, #27, #30 a #33, #133, #136, #159, #171, #172, #190, #195 | 28 |
| Entregue em `homolog`, aguardando promoção | #26 (por completo) e #29 (a tela `/alertas`; o backend já está em `main`) | 2 |
| Aberta, planejada na Sprint 4 e sem PR mergeado | #28, #199, #207 | 3 |
| Fora de escopo (trabalho futuro) | #115, #118 | 2 |
| **Total** | | **35** |

Do total, **30 USs estão entregues** (28 em `main` e 2 em `homolog`) e 5 não foram entregues. Os 35 itens são todas as issues com o prefixo `[US]` mais #32 e #33 (a #33 é o protótipo, com prefixo `[PROTO]`, e a #32 não tem prefixo).

---

## Diagramas de Sequência — Leitura Obrigatória

> **Prazo de planejamento: 19/06/2026.** O desenvolvimento de código acontecerá no próximo semestre. Até lá, cada membro deve estudar e compreender o diagrama de sequência da(s) sua(s) issue(s) — ele descreve exatamente como o sistema se comporta por dentro para atender àquela funcionalidade.

### Como visualizar o diagrama

Os arquivos `.puml` de cada issue estão no repositório:
**[docs/diagramas/sequencia/](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/tree/main/docs/diagramas/sequencia)**

Para visualizar, abra o arquivo correspondente à sua issue, copie o conteúdo e cole no renderizador online (BAIXE O ARQUIVO E ADICIONE AOS COMENTÁRIOS!!!):
**[https://www.plantuml.com/plantuml/uml/](https://www.plantuml.com/plantuml/uml/)**
