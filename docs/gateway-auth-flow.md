# Fluxo de Autenticação: Gateway ↔ Auth Service

> Revisado em 28/10/2026 contra o código de `homolog` (ambiente publicado). Onde o planejamento original divergiu do código, este documento descreve o código. Decisões relacionadas: ADR-07, ADR-17, ADR-20 e ADR-21 em `docs/documento_arquitetura.md`.

## Visão Geral

O Gateway é o **ponto único de entrada** para todas as requisições do frontend.
Ele valida o JWT **localmente** (sem round-trip ao Auth Service) a partir do cookie `access_token`, grava e limpa os cookies de sessão e encaminha a identidade do usuário aos serviços de domínio.

O Gateway **não acessa o banco**. Os serviços Auth, Mobilidade e Colaboração acessam o PostgreSQL por conta própria.

---

## Arquitetura

```
[Browser]
    │  cookies: access_token + refresh_token
    ▼
[Next.js Frontend]
    │  fetch com credentials: "include"
    ▼
[API Gateway — Ponto Único de Entrada]
    │  lê access_token do cookie
    │  valida JWT localmente (assinatura e expiração)
    │  guarda o sub em request.state.usuario_id
    │  roteia para serviços backend
    ├──► [Auth Service] ──► [PostgreSQL]
    ├──► [Mobilidade Service] ──► [PostgreSQL]
    └──► [Colaboracao Service] ──► [PostgreSQL]
```

---

## Gateway como Proxy

### Endpoints

| Endpoint | Método | Destino | Exige `access_token` |
|----------|--------|---------|----------------------|
| `/api/hello`, `/api/status`, `/health` | GET | Gateway | Não |
| `/api/auth/login` | POST | Auth Service; grava os cookies | Não |
| `/api/auth/login/google` | POST | Auth Service; grava os cookies | Não |
| `/api/auth/link-google/confirmar` | POST | Auth Service; grava os cookies | Não |
| `/api/auth/registrar` | POST | Auth Service | Não |
| `/api/auth/esqueci-senha` | POST | Auth Service | Não |
| `/api/auth/redefinir-senha` | POST | Auth Service | Não |
| `/api/auth/refresh` | POST | Auth Service; regrava os cookies | Não (usa o cookie `refresh_token`) |
| `/api/auth/logout` | POST | Auth Service; limpa os cookies | Não |
| `/api/auth/me` | GET | Auth Service | Sim |
| `/api/auth/me/first-access` | PUT | Auth Service | Sim |
| `/api/mobilidade/*` | GET/POST/PUT/DELETE | Mobilidade Service | Sim |
| `/api/colaboracao/*` | GET/POST/PUT/DELETE | Colaboracao Service | Sim |

A lista de rotas públicas está em `AutenticacaoMiddleware.ROTAS_PUBLICAS` (`gateway/middleware.py`); também são públicos `/`, `/docs`, `/redoc` e `/openapi.json`.

### Fluxo de Proxy

```
1. Browser envia request para /api/*
2. O middleware de autenticação confere a rota: se não é pública, exige o cookie
   access_token e valida o JWT; sem cookie ou token inválido/expirado, responde 401
3. Gateway roteia para o serviço correspondente (query string repassada; Accept-Encoding não)
4. O serviço processa e responde
5. Gateway devolve a resposta ao Browser
```

Falhas do serviço de destino: 504 se demorar mais de 30 s; 502 se não houver conexão.

### Identidade encaminhada aos serviços de domínio

Nas rotas `/api/mobilidade/*` e `/api/colaboracao/*`, o Gateway define o cabeçalho `X-User-Id` com o `sub` do JWT validado. Um `X-User-Id` enviado pelo cliente é **sempre descartado** (`HEADERS_SO_DO_GATEWAY` em `gateway/proxy.py`, sem diferenciar maiúsculas; issue #188, PR #189). Os serviços de domínio confiam nesse cabeçalho e não validam sua origem; como os serviços estão em URLs públicas do Fly.io, a proteção vale apenas para quem passa pelo Gateway.

O Auth Service **não** usa o `X-User-Id`: em `/auth/me` e `/auth/me/first-access` ele lê o cookie `access_token` repassado pelo Gateway e valida a assinatura ele mesmo.

### Configuração dos serviços

```python
# gateway/config.py (variáveis com prefixo GATEWAY_)
class GatewaySettings(BaseSettings):
    AUTH_SERVICE_URL: str = "https://movecity-auth.fly.dev"
    MOBILIDADE_SERVICE_URL: str = "https://movecity-mobilidade.fly.dev"
    COLABORACAO_SERVICE_URL: str = "https://movecity-colaboracao.fly.dev"
```

URLs públicas HTTPS, e não a rede interna do Fly.io (ADR-01).

---

## Fluxos de Autenticação

### 1. Cadastro (US #11)

```
1. Browser envia POST /api/auth/registrar (nome, e-mail, senha, termos_aceitos)
2. Gateway roteia para o Auth Service
3. Auth Service rejeita termos_aceitos = false, rejeita e-mail já cadastrado (409),
   grava a senha com hash bcrypt e cria a conta já ativa
```

Não existe confirmação de conta por e-mail: a conta entra direto.

### 2. Login com e-mail e senha (US #10)

```
1. Browser envia POST /api/auth/login (email + senha)
2. Gateway roteia para o Auth Service
3. Auth Service confere a senha. Cinco erros seguidos bloqueiam a conta por 15 min (423)
4. Auth Service cria um registro em `sessoes` e responde com access_token e refresh_token no corpo
5. Gateway grava os cookies httpOnly:
   - access_token  (1 h,    path=/api,      Secure, SameSite=None)
   - refresh_token (7 dias, path=/api/auth, Secure, SameSite=None)
6. Gateway devolve ao Browser a resposta do Auth Service, que continua contendo os tokens no corpo
```

O login com Google (`/api/auth/login/google`) segue o mesmo caminho. Se o e-mail já pertence a uma conta com senha, o Auth Service responde sem tokens e com `account_linking_required`, e o vínculo só se conclui em `/api/auth/link-google/confirmar`, que revalida o token do Google.

### 3. Requisição autenticada

```
1. Browser envia GET /api/mobilidade/linhas (cookie access_token)
2. Gateway lê o cookie e valida o JWT localmente (assinatura HS256 e expiração)
3. Extrai o sub do payload e o guarda em request.state.usuario_id
4. Encaminha ao serviço de domínio com o cabeçalho X-User-Id
```

**Código de referência:** `src/backend/gateway/middleware.py`, `jwt_validator.py`, `proxy.py`.

O Gateway valida o token só por assinatura e expiração; **não consulta a tabela `sessoes`**.

### 4. Renovação da sessão (Refresh) — feita pelo frontend

O Gateway não renova nada sozinho. A renovação é reativa e vive no frontend (`fetchAutenticado` em `src/frontend/lib/api.ts`; issue #221, PR #222):

```
1. O frontend chama o Gateway e recebe 401 (access token vencido)
2. Se a rota não é de autenticação (login, registrar, refresh, logout, esqueci-senha,
   redefinir-senha, link-google), o frontend chama UMA vez POST /api/auth/refresh
   (cookie refresh_token enviado automaticamente)
3. Gateway roteia para o Auth Service
4. Auth Service valida assinatura e expiração do refresh token e confere que ele existe em `sessoes`
5. Auth Service ROTACIONA o par: grava novos tokens na sessão e responde com eles
6. Gateway regrava os cookies httpOnly
7. O frontend repete a requisição original
8. Se o refresh falha (401 ou erro de rede), o frontend limpa a sessão no cliente
   e leva o usuário a /login?sessao=expirada
```

Detalhes:

- Chamadas simultâneas que recebem 401 compartilham **a mesma** renovação. Como o refresh rotaciona o token, duas renovações em paralelo fariam a segunda usar um token já invalidado e derrubariam a sessão.
- A renovação só acontece quando o primeiro 401 chega; não há renovação agendada.
- Rota do Auth Service: `POST /auth/refresh` (implementada na issue #212, PR #218; antes disso o Gateway fazia proxy de uma rota que não existia e respondia 404).
- Validada em produção em 27/10/2026: `GET` com 401, `POST /api/auth/refresh` 200 e a consulta refeita com 200, sem pedir login.

### 5. Logout

```
0. Frontend (`logoutUsuario`) remove a inscrição de Web Push deste aparelho, sem impedir o logout se falhar
1. Frontend chama POST /api/auth/logout
2. Gateway roteia para o Auth Service
3. Auth Service apaga da tabela `sessoes` a sessão do cookie access_token (se o cookie chegou)
4. Gateway limpa os dois cookies, sempre
5. Frontend limpa os tokens do localStorage e o cache local de favoritos
   (o redirecionamento depende da tela que chamou o logout; não verificado aqui)
```

Com a sessão apagada, o refresh token deixa de funcionar. Um access token já emitido **continua aceito até expirar** (1 h), porque o Gateway não consulta `sessoes`. Se o cookie `access_token` já tiver sido descartado pelo navegador, o Auth Service não encontra a sessão para apagar.

### 6. Recuperação de senha (US #13)

```
1. Browser envia POST /api/auth/esqueci-senha (e-mail)
2. Auth Service aplica o limite de 5 solicitações por e-mail em 15 min (429)
3. Se o e-mail existe, grava um token de uso único (guardado como hash SHA-256, validade 60 min)
   e AGENDA o envio do e-mail em segundo plano (BackgroundTasks)
4. A resposta é a mesma para e-mail cadastrado e não cadastrado
5. O e-mail sai por SMTP (smtp.gmail.com:587, STARTTLS) com o link
   <FRONTEND_URL>/redefinir-senha?token=...
6. Browser envia POST /api/auth/redefinir-senha (token, nova senha, confirmação)
7. Auth Service confere que as senhas coincidem, que têm ao menos 8 caracteres e que o
   token é válido; grava o novo hash e marca o token como usado
```

Se `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` ou `FRONTEND_URL` faltarem, o e-mail não é enviado e o endpoint responde normalmente. Falha de SMTP é registrada no log (só o tipo do erro) e não derruba o endpoint. Em 28/10/2026 o e-mail chegou à caixa de entrada e a nova senha foi definida pelo link (issue #237, PR #238). O limite de solicitações fica na memória do processo.

---

## Cookies

| Cookie | HttpOnly | Secure | SameSite | Path | Max Age |
|--------|----------|--------|----------|------|---------|
| `access_token` | Sim | Sim | **None** | `/api` | 60 min (3600 s) |
| `refresh_token` | Sim | Sim | **None** | `/api/auth` | 7 dias (604800 s) |

`SameSite=None` porque o frontend (Vercel) e o Gateway (Fly.io) estão em domínios diferentes: com `Lax` ou `Strict` o navegador não envia o cookie em `fetch()` cross-site. `Secure` é obrigatório junto com `SameSite=None` (ADR-07).

**O que os cookies httpOnly protegem, e o que não protegem hoje.** Cookie httpOnly não pode ser lido por JavaScript, o que seria a proteção contra roubo de token por XSS. **Essa proteção está reduzida** porque o corpo da resposta de login (e-mail e Google) e de refresh continua trazendo `access_token` e `refresh_token` (o Gateway devolve a resposta do Auth Service e só acrescenta os cookies), e o frontend grava os dois em `localStorage` (`loginUsuario` e `armazenarTokensSeExistirem`, em `src/frontend/lib/api.ts`). `getAccessToken()` e `getRefreshToken()` existem, mas nenhuma outra parte do frontend as chama: a autenticação real usa os cookies. Mesmo sem uso, qualquer script executado na página consegue ler os tokens do `localStorage`. **Limitação conhecida, issue #253 (aberta).**

---

## Configuração

### Variáveis de ambiente

```python
# shared/config.py
JWT_SECRET: str = "dev-secret-change-in-production"   # padrão de desenvolvimento
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_MINUTES: int = 60                       # vale para o access token
CORS_ORIGINS: str = "http://localhost:3000"
```

O refresh token tem validade fixa de 7 dias no código (`auth/security.py`). Gateway e Auth Service precisam usar o mesmo `JWT_SECRET`; o valor usado no Fly.io é secret do app e não é verificado por este documento.

### CORS (obrigatório para cookies)

```python
# gateway/main.py — o CORSMiddleware é adicionado por ÚLTIMO, ficando o mais externo
app.add_middleware(AutenticacaoMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,  # obrigatório para cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Com o CORS mais externo, o preflight `OPTIONS` (que nunca leva cookie) é respondido antes da autenticação, e todo 401 legítimo chega ao frontend como 401 (ADR-09).

---

## Implementação

### Gateway (US #31)

| Arquivo | Responsabilidade |
|---------|------------------|
| `middleware.py` | Valida o JWT do cookie em cada request não público |
| `jwt_validator.py` | Decodifica e valida tokens JWT |
| `dependencies.py` | `get_usuario_atual` para endpoints protegidos |
| `proxy.py` | Proxy genérico: query string, descarte do `X-User-Id` do cliente, timeouts |
| `cookies.py` | Grava e limpa os cookies httpOnly |
| `config.py` | URLs dos serviços |
| `routes.py` | Rotas de proxy (auth, mobilidade, colaboração) e `/api/status` |

### Auth Service (US #10, #11, #12, #13)

| Arquivo | Responsabilidade |
|---------|------------------|
| `routes.py` | login, login Google, vínculo Google, registrar, refresh, logout, me, first-access, esqueci-senha, redefinir-senha |
| `security.py` | Hash bcrypt e criação/decodificação dos JWT |
| `google_auth.py` | Validação do token do Google |
| `email_service.py` | Envio do e-mail de recuperação de senha por SMTP |
| `models/` | `Usuario`, `Sessao`, `TokenResetSenha` |

### Frontend

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/frontend/lib/api.ts` | Chamadas ao Gateway com `credentials: "include"`; `fetchAutenticado` (renovação em 401); `SessaoExpiradaError` |
| `src/frontend/lib/navegacao.ts` | Redirecionamento ao login |

---

## Segurança

| Ameaça | Mitigação | Limite |
|--------|-----------|--------|
| **XSS** | Cookies httpOnly | **Reduzida:** o frontend também grava os tokens em `localStorage` (#253, aberta) |
| **CSRF** | Escopo de `path` por cookie e HTTPS obrigatório | `SameSite=None` amplia a exposição a CSRF; não há token anti-CSRF |
| **Replay** | Access token de 1 h; refresh de 7 dias, rotacionado a cada renovação | — |
| **Token roubado** | O refresh token deixa de valer no logout (sessão apagada) | O access token já emitido vale até expirar; o Gateway não consulta `sessoes` |
| **Força bruta** | Bloqueio de 15 min após 5 senhas erradas; limite de 5 pedidos de recuperação por e-mail em 15 min | Limite de recuperação na memória do processo |
| **Identidade forjada** | O Gateway descarta o `X-User-Id` do cliente (#188) | Serviços de domínio acessíveis diretamente nas URLs públicas confiam no cabeçalho |

---

## Referências

- US #31: [Gerenciar Ciclo de Vida da Sessão](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/31)
- Issues: #188 (X-User-Id), #212 e #221 (refresh), #237 (e-mail de recuperação), #253 (tokens no `localStorage`)
- Diagrama de sequência: `docs/diagramas/sequencia/UC10-realizar-login-email-senha.puml`
