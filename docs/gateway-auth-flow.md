# Fluxo de Autenticação: Gateway ↔ Auth Service

## Visão Geral

O Gateway é o **ponto único de entrada** para todas as requisições do frontend.
Ele valida JWT **localmente** (sem round-trip ao Auth Service) usando httpOnly cookies.

---

## Arquitetura

```
[Browser]
    │  cookies: access_token + refresh_token
    ▼
[Next.js Frontend]
    │  envia cookies automaticamente
    ▼
[API Gateway — Ponto Único de Entrada]
    │  lê access_token do cookie
    │  valida JWT localmente
    │  extrai identidadeUsuario
    │  roteia para serviços backend
    ├──► [Auth Service] ──► [PostgreSQL]
    ├──► [Mobilidade Service] ──► [PostgreSQL]
    └──► [Colaboracao Service] ──► [PostgreSQL]
```

**Regra:** Nenhum serviço acessa o banco diretamente. Tudo passa pelo Gateway.

---

## Gateway como Proxy

O Gateway é o **ponto único de entrada** para todas as requisições do frontend.
Nenhum serviço backend se comunica com o banco diretamente — tudo passa pelo Gateway.

### Endpoints de Proxy

| Endpoint | Método | Destino |
|----------|--------|---------|
| `/api/auth/login` | POST | Auth Service |
| `/api/auth/registrar` | POST | Auth Service |
| `/api/auth/refresh` | POST | Auth Service |
| `/api/auth/logout` | POST | Auth Service |
| `/api/mobilidade/*` | GET/POST/PUT/DELETE | Mobilidade Service |
| `/api/colaboracao/*` | GET/POST/PUT/DELETE | Colaboracao Service |

### Fluxo de Proxy

```
1. Browser envia request para /api/*
2. Gateway recebe e valida JWT (middleware)
3. Gateway roteia para serviço backend correspondente
4. Serviço backend processa e retorna response
5. Gateway retorna response para Browser
```

### Configuração dos Serviços

```python
# gateway/config.py
SERVICES = {
    "auth": "http://auth-service:8000",
    "mobilidade": "http://mobilidade-service:8000",
    "colaboracao": "http://colaboracao-service:8000",
}
```

---

## Fluxos de Autenticação

### 1. Login (US #10)

```
1. Browser envia POST /api/auth/login (email + senha)
2. Gateway recebe e roteia para Auth Service
3. Auth Service valida credenciais no banco
4. Auth Service retorna tokens (access + refresh)
5. Gateway seta cookies httpOnly:
   - access_token (60 min, path=/api, SameSite=Lax)
   - refresh_token (7 dias, path=/api/auth, SameSite=Strict)
6. Gateway retorna response para Browser
```

### 2. Requisição Autenticada

```
1. Browser envia GET /api/mobilidade/linhas (cookie: access_token)
2. Gateway lê access_token do cookie
3. Valida JWT localmente (verifica assinatura e expiração)
4. Extrai usuario_id do payload
5. Adiciona em request.state.usuario_id
6. Encaminha para serviço de domínio
```

**Código referência:** `src/backend/gateway/middleware.py`

### 3. Renovação de Token (Refresh)

```
1. Access token expira (401 do Gateway)
2. Frontend interceptor detecta 401
3. Chama POST /api/auth/refresh (cookie refresh_token enviado)
4. Gateway roteia para Auth Service
5. Auth Service valida refresh token no banco
6. Auth Service retorna novos tokens
7. Gateway atualiza cookies httpOnly
8. Frontend repete request original
```

**Endpoint:** `POST /api/auth/refresh`

### 4. Logout

```
1. Frontend chama POST /api/auth/logout
2. Gateway roteia para Auth Service
3. Auth Service revoga refresh token no banco
4. Gateway limpa cookies httpOnly
5. Frontend redireciona para /login
```

**Endpoint:** `POST /api/auth/logout`

---

## Cookies

| Cookie | HttpOnly | Secure | SameSite | Path | Max Age |
|--------|----------|--------|----------|------|---------|
| `access_token` | ✅ | ✅ | Lax | `/api` | 60 min |
| `refresh_token` | ✅ | ✅ | Strict | `/api/auth` | 7 dias |

**Por que httpOnly?**
- Protegido contra XSS (JavaScript não acessa)
- Browser gerencia automaticamente
- CSRF mitigation via SameSite + CSRF token (futuro)

---

## Configuração

### Variáveis de Ambiente

```python
# shared/config.py
JWT_SECRET: str = "dev-secret-change-in-production"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_MINUTES: int = 60
```

### Variáveis de Ambiente dos Serviços

```python
# gateway/config.py
GATEWAY_AUTH_SERVICE_URL: str = "http://auth-service:8000"
GATEWAY_MOBILIDADE_SERVICE_URL: str = "http://mobilidade-service:8000"
GATEWAY_COLABORACAO_SERVICE_URL: str = "http://colaboracao-service:8000"
```

### CORS (obrigatório para cookies)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,  # Obrigatório para cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Implementação

### Gateway (US #31)

| Arquivo | Responsabilidade |
|---------|------------------|
| `middleware.py` | Valida JWT do cookie em cada request |
| `jwt_validator.py` | Decodifica e valida tokens JWT |
| `dependencies.py` | `get_usuario_atual` para endpoints protegidos |
| `proxy.py` | Proxy genérico para serviços backend |
| `cookies.py` | Helper para setar/limpar cookies httpOnly |
| `config.py` | Configuração das URLs dos serviços |
| `routes.py` | Endpoints de proxy (auth, mobilidade, colaboracao) |

### Auth Service (US #10, #11)

| Arquivo | Responsabilidade |
|---------|------------------|
| `routes.py` | Endpoints: login, refresh, logout, me |
| `service.py` | Geração e validação de tokens |
| `models/sessao.py` | Controle de sessões no banco |

---

## Segurança

| Ameaça | Mitigação |
|--------|-----------|
| **XSS** | Tokens em httpOnly cookies (JS não acessa) |
| **CSRF** | SameSite=Lax (access) / Strict (refresh) |
| **Replay** | Tokens com expiração curta (60min access, 7d refresh) |
| **Token roubado** | Refresh token revogável no banco |

---

## Referências

- US #31: [Gerenciar Ciclo de Vida da Sessão](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/31)
- Diagrama de sequência: `docs/diagramas/sequencia/UC10-realizar-login-email-senha.puml`
