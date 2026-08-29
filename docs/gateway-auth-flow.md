# Fluxo de Autenticação: Gateway ↔ Auth Service

## Visão Geral

O Gateway é o ponto único de entrada para todas as requisições do frontend.
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
[GatewayAPI <<servico gateway>>]
    │  lê access_token do cookie
    │  valida JWT localmente
    │  extrai identidadeUsuario
    ├──► [Auth Service] ──► [PostgreSQL]
    └──► [Serviços de Domínio]
```

**Decisão-chave:** Gateway valida JWT localmente — sem round-trip ao Auth Service.

---

## Fluxos de Autenticação

### 1. Requisição Autenticada

```
1. Browser envia cookies automaticamente
2. Gateway lê access_token do cookie
3. Valida JWT localmente (verifica assinatura e expiração)
4. Extrai usuario_id do payload
5. Adiciona em request.state.usuario_id
6. Encaminha para serviço de domínio
```

**Código referência:** `src/backend/gateway/middleware.py`

### 2. Renovação de Token (Refresh)

```
1. Access token expira (401 do Gateway)
2. Frontend interceptor detecta 401
3. Chama POST /auth/refresh (cookie refresh_token enviado)
4. Auth Service valida refresh token no banco
5. Retorna novo access token via Set-Cookie
6. Frontend repete request original
```

**Endpoint:** `POST /auth/refresh`

### 3. Logout

```
1. Frontend chama POST /auth/logout
2. Auth Service revoga refresh token no banco
3. Resposta: Clear-Cookie header
4. Frontend redireciona para /login
```

**Endpoint:** `POST /auth/logout`

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
