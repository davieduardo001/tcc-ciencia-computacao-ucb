# Relato — Deploy do Hello World (Sprint 0 / Issue #35)

**Data:** 15/08/2026
**Issue:** [#35](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/35)
**Objetivo da issue:** validar o workflow completo de desenvolvimento do Movecity — branch → PR → review → CI → CD → deploy — usando um "hello world" real como cobaia, não uma feature de produto.

Este documento registra, em ordem, tudo o que foi feito para colocar o backend (4 microservices) e o frontend no ar, incluindo os erros encontrados no caminho e como cada um foi resolvido. Serve como referência de como o workflow se comporta na prática e como material de apoio pra quem for repetir o processo em uma User Story real.

---

## 1. Ponto de partida

O trabalho começou retomando um plano de deploy que já vinha sendo desenhado em uma sessão anterior (via OpenCode), registrado em `docs/deploy-plan.md`. O plano previa o backend dividido em 4 microservices FastAPI (`gateway`, `auth`, `mobilidade`, `colaboracao`) publicados como apps independentes no Fly.io, com banco compartilhado no Neon.

[anexar imagem: estado inicial do board/todo do OpenCode antes de retomar]

---

## 2. Atualizar a issue #35 (Render → Fly.io)

A issue #35 original citava Render como plataforma de backend. O `AGENT.md` do projeto já havia sido atualizado para Fly.io antes, então a issue estava desatualizada em relação à decisão de arquitetura vigente. Editamos objetivo, scope, stack e critérios de aceite da issue pra refletir Fly.io.

[anexar imagem: issue #35 antes/depois da edição]

---

## 3. Provisionar o Fly.io

- Destruído o app antigo `movecity-backend` (resquício de uma tentativa anterior, sem uso).
- Criados os 4 apps novos: `movecity-gateway`, `movecity-auth`, `movecity-mobilidade`, `movecity-colaboracao`.

[anexar imagem: lista de apps no dashboard do Fly.io]

---

## 4. Configurar secrets

- `JWT_SECRET` gerado localmente (`openssl rand -hex 32`) e aplicado a `gateway`/`auth`.
- `DATABASE_URL`: localizada a partir do projeto `movecity` já existente no Neon (via `neonctl`), não inventada — é a connection string real do banco de homologação/teste do projeto.
- Todos os secrets aplicados via `flyctl secrets set` nos 4 apps.

[anexar imagem: `flyctl secrets list` de um dos apps]

---

## 5. Rodar local (backend + frontend)

Sem Docker disponível na máquina, o backend local foi apontado direto pro Neon (mesma `DATABASE_URL` de homologação) em vez do Postgres local do `docker-compose.yml`. Migrations aplicadas via Alembic, backend subido com `uvicorn`, frontend com `npm run dev`. Os 4 endpoints (`/gateway/hello`, `/auth/hello`, `/mobilidade/hello`, `/colaboracao/hello`) responderam localmente antes de qualquer deploy.

[anexar imagem: frontend rodando em localhost mostrando status dos 4 serviços]

---

## 6. Descoberta: PR #39 mergeado sem review formal

Ao checar o estado do PR que fecharia a issue #35, veio à tona que ele havia sido mergeado em `homolog` com **bypass da branch protection** — sem nenhuma aprovação registrada, contrariando a regra do `AGENT.md` ("PR requer aprovação — 1 reviewer mínimo. Sem exceção"). Ficou registrado explicitamente na issue #35, como nota de rastreabilidade, sem desfazer o merge (decisão consciente de quem estava testando o fluxo).

[anexar imagem: histórico do PR #39 mostrando reviewDecision sem aprovação]

---

## 7. CI quebrado: 3 bugs encontrados e corrigidos

Rodar o CI do PR #39 revelou 3 falhas, nenhuma delas no código de produto:

| Job | Causa raiz | Correção |
|---|---|---|
| Testes Backend (pytest) | `alembic` faltando em `requirements.txt` — funcionava local só porque já estava instalado manualmente na venv | Adicionado `alembic>=1.13` ao `requirements.txt` |
| Testes Frontend (Jest) | Zero arquivos de teste no frontend — "No tests found" | Criado `jest.config.js`, `jest.setup.js` e um teste smoke da página principal |
| Lint / Conventional Commits | O script validava **cada linha** da mensagem de commit (corpo incluso) contra o regex, reprovando bullets do corpo e o commit de merge | Script corrigido pra validar só a primeira linha (subject) e ignorar merge commits |

Aproveitamos também pra documentar na skill `criar-testes` (OpenCode) que testes devem ser comunicados via comentário na issue — não existe vínculo automático entre teste e issue no GitHub.

[anexar imagem: CI verde — 3/3 checks passando no PR]

---

## 8. Divergência: plano de 4 apps vs. código monolito

Antes de fazer qualquer deploy real, percebemos que o código mergeado no PR #39 era, na prática, **um único processo FastAPI** com 4 routers internos — não 4 serviços independentes como o `deploy-plan.md` descrevia. O `fly.toml`/`Dockerfile` únicos apontavam pro app `movecity-backend`, que já havia sido destruído no passo 3.

Decisão: seguir o plano original e refatorar de verdade pra 4 microservices deployáveis, em vez de simplificar o plano pro que já existia.

[anexar imagem: diagrama antes/depois — monolito vs. 4 serviços]

---

## 9. Refactor: 4 microservices deployáveis

Nova branch `fix/issue-35-split-microservices` (a partir de `homolog`, já que o PR #39 estava fechado):

- `shared/config.py`: settings comuns.
- `gateway/`, `auth/`, `mobilidade/`, `colaboracao/`: cada um com `main.py`, `Dockerfile`, `fly.toml` e `requirements.txt` próprios.
- Testes atualizados pra importar o `main.py` do próprio serviço, não mais um `main.py` compartilhado.
- Validado local: os 4 serviços sobem isolados, cada um na sua porta, sem depender dos outros.

PR #40 aberto, CI verde, **merge com bypass de novo** (decisão consciente, mesma lógica do passo 6 — testar o pipeline).

[anexar imagem: PR #40 com CI verde]

---

## 10. Deploy manual — primeira subida real

Antes de automatizar, validamos manualmente:

```bash
flyctl deploy --config src/backend/auth/fly.toml --dockerfile src/backend/auth/Dockerfile . --remote-only
# repetido para mobilidade, colaboracao e gateway
```

Os 4 apps responderam em produção (`https://movecity-<serviço>.fly.dev/health` e `/<serviço>/hello`).

> **Discussão paralela:** cogitamos consolidar os 4 serviços em 1 único app Fly.io (com múltiplas máquinas/process groups) pra simplificar a operação. Conclusão: o custo é o mesmo (Fly cobra por máquina, não por app), mas um app único amarra o deploy de todos os serviços numa imagem só — perde-se a independência de deploy que é o motivo de existir a separação. Mantivemos os 4 apps separados.

[anexar imagem: `curl` dos 4 endpoints em produção]

---

## 11. CI/CD automático

Criado `.github/workflows/deploy-fly.yml`: dispara `flyctl deploy` dos 4 serviços a cada push em `homolog` ou `main` que toque `src/backend/**`. `auth`, `mobilidade` e `colaboracao` deployam em paralelo; `gateway` só depois dos três (`needs:`).

Tokens de deploy gerados com escopo restrito a 1 app cada (`flyctl tokens create deploy -a <app>`), guardados como secrets no GitHub — evitando usar o token pessoal de acesso total à conta Fly.io.

Testado de ponta a ponta: merge do PR #40 → workflow disparou sozinho → 4/4 jobs verdes → endpoints em produção confirmados.

[anexar imagem: `deploy-fly.yml` rodando com 4 jobs verdes]

---

## 12. Security review

Revisão focada em vulnerabilidades introduzidas pelo diff (não geral): nenhum achado. Pontos verificados: secrets sempre via `env:` (nunca interpolados em `run:`), tokens com escopo mínimo, sem uso de `eval`/`exec`/`pickle`/deserialização insegura no backend.

---

## 13. PR para produção — primeira tentativa

Aberto PR #41 (`homolog` → `main`), sem bypass dessa vez — produção de verdade. Um comentário "Revisado." foi deixado na conversa da PR, mas **não** era uma aprovação formal (o GitHub só conta reviews feitos via botão "Review changes → Approve"). A PR acabou fechada sem merge.

[anexar imagem: PR #41 fechado, reviewDecision ainda REVIEW_REQUIRED]

---

## 14. Reabertura e aprovação formal

PR reaberto, reviewer solicitada explicitamente (`gh pr edit --add-reviewer`), e o caminho certo pra aprovar (aba **Files changed** → botão **Review changes** → **Approve**) foi passado pra revisora. Dessa vez a aprovação ficou registrada de verdade (`reviewDecision: APPROVED`), e o merge para `main` foi feito sem bypass.

[anexar imagem: PR #41 aprovado por @Vitoria-Albuquerque]

---

## 15. Deploy em produção

Merge em `main` disparou o `deploy-fly.yml` de novo, agora publicando os 4 serviços "em produção" (mesmos apps/URLs — ver limitação abaixo). Endpoints reconfirmados no ar.

[anexar imagem: os 4 serviços respondendo depois do merge em main]

---

## 16. Lacunas conhecidas (documentadas, não corrigidas)

Simplificações conscientes, registradas em `docs/deploy-plan.md` e rastreadas na issue [#42](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/42):

- **Sem separação de ambiente no backend.** Homolog e produção usam os *mesmos* 4 apps Fly.io — um push em `homolog` sobrescreve o que está em produção. O frontend não tem esse problema (Vercel já separa preview de produção por branch).
- Sem separação de banco por ambiente (1 projeto Neon só).
- Sem separação por schema Postgres (tudo no `public`).
- Gateway ainda não faz proxy real nem validação de JWT.
- `auth`/`mobilidade`/`colaboracao` são públicos, não internos como o plano original previa.
- Migrations não rodam automaticamente no CD — seguem manuais.

---

## Conclusão

O objetivo da issue #35 — validar o workflow ponta a ponta — foi cumprido, incluindo os desvios do fluxo ideal (2 merges com bypass, 1 PR fechado por engano, uma review informal que não contou) registrados abertamente em vez de escondidos. O resultado é um backend de 4 microservices e um frontend rodando em produção real no Fly.io/Vercel, com CI e CD automatizados, e uma lista clara do que falta amadurecer antes de qualquer User Story tocar em dado real de usuário.
