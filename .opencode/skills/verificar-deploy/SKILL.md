---
name: verificar-deploy
description: Verifica se o código está pronto para deploy antes de subir.
---

# Verificar Deploy — Movecity

Esta skill verifica se o código está pronto para deploy, prevenindo erros como health check retornando 401.

## Checklist Pré-Deploy

### 1. Health Check

```bash
# Testar localmente
curl http://localhost:8000/health

# Esperado: {"status":"ok","service":"gateway","environment":"..."}
# NÃO deve retornar 401
```

### 2. Rotas Públicas

```bash
# Gateway
curl http://localhost:8000/gateway/hello
curl http://localhost:8000/gateway/health

# Auth
curl http://localhost:8000/auth/login
curl http://localhost:8000/auth/registrar
curl http://localhost:8000/auth/refresh
```

### 3. Rotas Protegidas (devem retornar 401 sem token)

```bash
curl http://localhost:8000/gateway/hello
# Esperado: {"detail":"Não autenticado"}
```

### 4. Requirements

```bash
# Verificar se todas as dependências estão no requirements.txt
pip install -r requirements.txt --dry-run
```

### 5. Testes

```bash
# Backend
cd src/backend && pytest -v

# Frontend
cd src/frontend && npm test
```

### 6. Imports

```bash
# Verificar se imports funcionam
cd src/backend
python -c "from gateway.main import app; print('Gateway OK')"
python -c "from auth.main import app; print('Auth OK')"
```

## Comandos Rápidos

```bash
# Verificar tudo de uma vez
cd src/backend
python -c "from gateway.main import app; print('Gateway OK')" && \
pytest -v && \
curl http://localhost:8000/health
```

## Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| Health check retorna 401 | Rota não está na lista de rotas públicas | Adicionar `/health` em `ROTAS_PUBLICAS` |
| `ModuleNotFoundError` | Dependência faltando no requirements.txt | Adicionar dependência |
| Import error | Arquivo não existe ou path incorreto | Verificar path do import |

## Referências

- Middleware: `src/backend/gateway/middleware.py`
- Health check: `src/backend/gateway/main.py`
- Requirements: `src/backend/gateway/requirements.txt`
