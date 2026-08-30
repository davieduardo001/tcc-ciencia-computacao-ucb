#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "=========================================="
echo "  Movecity — Verificação Pré-Deploy"
echo "=========================================="

ERROS=0

echo ""
echo "[1/4] Verificando dependências do Gateway..."
if pip install -r src/backend/gateway/requirements.txt --dry-run 2>/dev/null; then
    echo "  ✅ Dependências OK"
else
    echo "  ❌ Dependências faltando no requirements.txt"
    ERROS=$((ERROS + 1))
fi

echo ""
echo "[2/4] Verificando imports..."
if python -c "from gateway.main import app; print('  ✅ Gateway OK')" 2>/dev/null; then
    true
else
    echo "  ❌ Gateway: import falhou"
    ERROS=$((ERROS + 1))
fi

if python -c "from auth.main import app; print('  ✅ Auth OK')" 2>/dev/null; then
    true
else
    echo "  ❌ Auth: import falhou"
    ERROS=$((ERROS + 1))
fi

echo ""
echo "[3/4] Verificando health check..."
cd src/backend
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
sleep 3

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✅ Health check OK"
else
    echo "  ❌ Health check falhou (esperado 200)"
    ERROS=$((ERROS + 1))
fi

kill $UVICORN_PID 2>/dev/null || true
wait $UVICORN_PID 2>/dev/null || true
cd "$ROOT_DIR"

echo ""
echo "[4/4] Verificando rotas públicas..."
cd src/backend
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
sleep 3

for ROTA in "/health" "/gateway/hello" "/gateway/health"; do
    if curl -sf "http://localhost:8000${ROTA}" > /dev/null 2>&1; then
        echo "  ✅ ${ROTA}"
    else
        echo "  ❌ ${ROTA} falhou"
        ERROS=$((ERROS + 1))
    fi
done

echo ""
echo "Verificando rota protegida (deve retornar 401)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/gateway/hello)
if [ "$HTTP_CODE" = "401" ]; then
    echo "  ✅ /gateway/hello retorna 401 (correto)"
else
    echo "  ❌ /gateway/hello retornou ${HTTP_CODE} (esperado 401)"
    ERROS=$((ERROS + 1))
fi

kill $UVICORN_PID 2>/dev/null || true
wait $UVICORN_PID 2>/dev/null || true
cd "$ROOT_DIR"

echo ""
echo "=========================================="
if [ $ERROS -eq 0 ]; then
    echo "  ✅ Tudo OK! Pronto para deploy."
    echo "=========================================="
    exit 0
else
    echo "  ❌ ${ERROS} erro(s) encontrado(s)."
    echo "  Corrija antes de fazer deploy."
    echo "=========================================="
    exit 1
fi
