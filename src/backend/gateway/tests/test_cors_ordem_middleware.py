# Regressão: CORSMiddleware precisa ser o middleware mais externo do
# Gateway (adicionado por último — o Starlette executa o último
# adicionado primeiro na entrada da requisição).
#
# Com AutenticacaoMiddleware mais externo (ordem antiga), qualquer rota
# protegida (mobilidade, colaboracao, auth/me, auth/logout) tinha dois
# problemas em produção (cross-site, front na Vercel / gateway no Fly):
#   1. O preflight OPTIONS caía em 401 antes do CORS rodar — o navegador
#      nunca chegava a tentar a requisição real.
#   2. Um 401 de verdade (sem cookie, sessão expirada) saía sem
#      Access-Control-Allow-Origin — o navegador reportava "erro de
#      CORS" em vez de deixar o front tratar um 401 normal.
from fastapi.testclient import TestClient

from gateway.main import app

client = TestClient(app)

ORIGEM_FRONTEND = "http://localhost:3000"  # default de CORS_ORIGINS em dev/teste


def test_preflight_options_em_rota_protegida_nao_exige_autenticacao():
    response = client.options(
        "/api/mobilidade/linhas/0.110",
        headers={
            "Origin": ORIGEM_FRONTEND,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code != 401
    assert response.headers.get("access-control-allow-origin") == ORIGEM_FRONTEND


def test_401_de_rota_protegida_ainda_carrega_cors():
    response = client.get(
        "/api/mobilidade/linhas/0.110",
        headers={"Origin": ORIGEM_FRONTEND},
    )

    # A autenticação continua valendo — isso não deve virar rota pública.
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == ORIGEM_FRONTEND
