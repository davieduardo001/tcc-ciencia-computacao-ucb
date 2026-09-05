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

## Resumo

| Responsável | Escopo | Qtd |
|---|---|---|
| @davieduardo001 | Orquestração + Backlog + #31 + #34 | — |
| @brenouchihar | Autenticação | 5 |
| @Kelvin963 | Mapa & Rastreamento (núcleo) | 3 |
| @louisassis | Mapa & Rastreamento (detalhes) | 4 |
| @Vitoria-Albuquerque | Colaboração (reporte) + Protótipo (#33) | 5 + protótipo |
| @gualbertonathalia | Colaboração (alertas) + Termos + Protótipo (#33) | 5 + protótipo |
| **Total USs** | | **24** |

---

## Diagramas de Sequência — Leitura Obrigatória

> **Prazo de planejamento: 19/06/2026.** O desenvolvimento de código acontecerá no próximo semestre. Até lá, cada membro deve estudar e compreender o diagrama de sequência da(s) sua(s) issue(s) — ele descreve exatamente como o sistema se comporta por dentro para atender àquela funcionalidade.

### Como visualizar o diagrama

Os arquivos `.puml` de cada issue estão no repositório:
**[docs/diagramas/sequencia/](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/tree/main/docs/diagramas/sequencia)**

Para visualizar, abra o arquivo correspondente à sua issue, copie o conteúdo e cole no renderizador online (BAIXE O ARQUIVO E ADICIONE AOS COMENTÁRIOS!!!):
**[https://www.plantuml.com/plantuml/uml/](https://www.plantuml.com/plantuml/uml/)**
