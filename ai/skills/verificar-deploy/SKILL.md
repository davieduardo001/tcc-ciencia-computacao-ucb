---
name: verificar-deploy
description: Verifica se o código está pronto para deploy antes de subir.
---

# Verificar Deploy — Movecity

Esta skill verifica se o código está pronto para deploy, prevenindo erros como dependências faltando e health check retornando 401.

## Comando Rápido

```bash
./scripts/verificar-deploy.sh
```

## Checklist Pré-Deploy (manual)

### 1. Health Check

```bash
curl http://localhost:8000/health
# Esperado: {"status":"ok","service":"gateway","environment":"..."}
# NÃO deve retornar 401
```

### 2. Rotas Públicas

```bash
curl http://localhost:8000/gateway/hello
curl http://localhost:8000/gateway/health
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
pip install -r requirements.txt --dry-run
```

### 5. Testes

```bash
cd src/backend && pytest -v
cd src/frontend && npm test
```

### 6. Imports

```bash
cd src/backend
python -c "from gateway.main import app; print('Gateway OK')"
python -c "from auth.main import app; print('Auth OK')"
```

## Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| Health check retorna 401 | Rota não está na lista de rotas públicas | Adicionar `/health` em `ROTAS_PUBLICAS` |
| `ModuleNotFoundError` | Dependência faltando no requirements.txt | Adicionar dependência |
| Import error | Arquivo não existe ou path incorreto | Verificar path do import |

## Referências

- Script: `scripts/verificar-deploy.sh`
- Middleware: `src/backend/gateway/middleware.py`
- Health check: `src/backend/gateway/main.py`
- Requirements: `src/backend/gateway/requirements.txt`
