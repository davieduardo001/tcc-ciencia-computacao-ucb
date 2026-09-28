#!/bin/bash
# Verificação pré-deploy do Movecity.
#
# O que este script existe para pegar: dependência que o código importa e
# que está ausente do requirements.txt do serviço. Isso passa no CI de
# testes — que instala o requirements COMBINADO da raiz, com tudo — e
# derruba o contêiner no boot, porque o Dockerfile de cada serviço
# instala só o arquivo dele. Aconteceu no PR #102 (mobilidade) e no
# #127/#128 (colaboracao).
#
# Por que não basta `pip install -r ... --dry-run`: o dry-run confere se
# os pacotes LISTADOS no arquivo resolvem. Ele não tem como saber de um
# pacote que o código importa e que não está na lista — que é justamente
# o defeito das duas quedas. A única verificação honesta é reproduzir o
# contêiner: ambiente limpo, só o requirements do serviço, e importar a
# aplicação.
#
# Uso:
#   ./scripts/verificar-deploy.sh            # tudo
#   ./scripts/verificar-deploy.sh --rapido   # pula os venv (só HTTP)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

SERVICOS=(gateway auth mobilidade colaboracao)
RAPIDO=0
[ "${1:-}" = "--rapido" ] && RAPIDO=1

ERROS=0
TMP_VENVS="$(mktemp -d)"
trap 'rm -rf "$TMP_VENVS"' EXIT

echo "=========================================="
echo "  Movecity — Verificação Pré-Deploy"
echo "=========================================="

# ---------------------------------------------------------------------------
echo ""
echo "[1/3] Contêiner de cada serviço (ambiente limpo + import)"

if [ "$RAPIDO" -eq 1 ]; then
    echo "  ⏭  pulado (--rapido)"
else
    echo "  Cria um ambiente por serviço; leva alguns minutos na primeira vez."
    for SERVICO in "${SERVICOS[@]}"; do
        REQ="src/backend/${SERVICO}/requirements.txt"

        if [ ! -f "$REQ" ]; then
            echo "  ❌ ${SERVICO}: ${REQ} não existe"
            ERROS=$((ERROS + 1))
            continue
        fi

        VENV="${TMP_VENVS}/${SERVICO}"
        if ! python3 -m venv "$VENV" > /dev/null 2>&1; then
            echo "  ❌ ${SERVICO}: não consegui criar o ambiente"
            ERROS=$((ERROS + 1))
            continue
        fi

        if ! "$VENV/bin/pip" install --quiet -r "$REQ" > /dev/null 2>&1; then
            echo "  ❌ ${SERVICO}: falha ao instalar ${REQ}"
            ERROS=$((ERROS + 1))
            continue
        fi

        # O import roda de dentro de src/backend porque é de lá que o
        # contêiner enxerga os pacotes (o Dockerfile copia models, shared
        # e o pacote do serviço para a raiz da imagem).
        if SAIDA=$(cd src/backend && "$VENV/bin/python" -c \
            "from ${SERVICO}.main import app" 2>&1); then
            echo "  ✅ ${SERVICO}"
        else
            echo "  ❌ ${SERVICO}: o import falhou — provável dependência ausente de ${REQ}"
            echo "     ${SAIDA}" | tail -3 | sed 's/^/     /'
            ERROS=$((ERROS + 1))
        fi
    done
fi

# ---------------------------------------------------------------------------
echo ""
echo "[2/3] Health check do Gateway"

# Sobe o gateway com o ambiente que o passo 1 acabou de montar, quando ele
# existe. Sem isso o script dependeria do que estivesse instalado por fora,
# e falhava em máquina sem as dependências no Python do sistema — sem que o
# código tivesse problema nenhum.
if [ -x "${TMP_VENVS}/gateway/bin/uvicorn" ]; then
    UVICORN="${TMP_VENVS}/gateway/bin/uvicorn"
elif command -v uvicorn > /dev/null 2>&1; then
    UVICORN="uvicorn"
else
    echo "  ⏭  uvicorn não encontrado."
    echo "     Rode sem --rapido (o script monta o ambiente sozinho),"
    echo "     ou ative o ambiente do projeto antes."
    echo ""
    echo "[3/3] Rotas públicas e rota protegida"
    echo "  ⏭  pulado: depende do passo anterior"
    echo ""
    echo "=========================================="
    if [ "$ERROS" -eq 0 ]; then
        echo "  ✅ Sem problemas no que foi verificado."
    else
        echo "  ❌ ${ERROS} problema(s)."
    fi
    echo "=========================================="
    [ "$ERROS" -eq 0 ] && exit 0 || exit 1
fi

cd src/backend
"$UVICORN" gateway.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
UVICORN_PID=$!
sleep 3

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✅ /health responde"
else
    echo "  ❌ /health falhou"
    ERROS=$((ERROS + 1))
fi

# ---------------------------------------------------------------------------
echo ""
echo "[3/3] Rotas públicas e rota protegida"

# O router do Gateway é montado em /api (US #31). As rotas /gateway/* que
# este script checava antes deixaram de existir nessa mudança, e o script
# vinha reprovando por isso — não por defeito no código.
#
# /api/status fica de fora de propósito: ele consulta os outros serviços
# pela rede, então depende de ambiente externo e não serve como verificação
# local.
for ROTA in "/health" "/api/hello"; do
    if curl -sf "http://localhost:8000${ROTA}" > /dev/null 2>&1; then
        echo "  ✅ ${ROTA}"
    else
        echo "  ❌ ${ROTA} falhou"
        ERROS=$((ERROS + 1))
    fi
done

# Rota protegida sem cookie tem que responder 401. Se responder 200, o
# middleware de sessão parou de proteger; se responder 404, a rota sumiu.
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/me)
if [ "$HTTP_CODE" = "401" ]; then
    echo "  ✅ /api/auth/me sem sessão retorna 401"
else
    echo "  ❌ /api/auth/me retornou ${HTTP_CODE}, esperado 401"
    ERROS=$((ERROS + 1))
fi

kill "$UVICORN_PID" 2>/dev/null || true
wait "$UVICORN_PID" 2>/dev/null || true
cd "$ROOT_DIR"

# ---------------------------------------------------------------------------
echo ""
echo "=========================================="
if [ "$ERROS" -eq 0 ]; then
    echo "  ✅ Tudo OK. Pronto para deploy."
    echo "=========================================="
    exit 0
else
    echo "  ❌ ${ERROS} problema(s). Corrija antes do deploy."
    echo "=========================================="
    exit 1
fi
