"""A lista de rotas públicas do middleware precisa bater com a aplicação.

Duas formas de errar, e as duas já aconteceram:

- entrada que não corresponde a rota nenhuma (`/gateway/hello`, `/doc`),
  que não protege nem libera nada — só dá impressão de cobertura;
- rota que existe e ficou de fora, como `/docs`, que respondia 401 e
  deixava o Swagger inacessível.
"""

from fastapi.testclient import TestClient

from gateway.main import app
from gateway.middleware import AutenticacaoMiddleware

client = TestClient(app)

# Servidas pelo próprio Gateway, sem proxy — dá para checar sem rede.
ROTAS_LOCAIS = ["/", "/health", "/api/hello", "/docs", "/redoc", "/openapi.json"]


def test_rotas_locais_respondem_sem_sessao():
    for rota in ROTAS_LOCAIS:
        resposta = client.get(rota)
        assert resposta.status_code == 200, (
            f"{rota} devia ser pública e respondeu {resposta.status_code}"
        )


def test_documentacao_da_api_e_acessivel():
    """O Swagger já ficou fora da lista, respondendo 401 em produção.

    A lista tinha `/doc`, sem o "s", que não corresponde a rota nenhuma.
    """
    assert "/docs" in AutenticacaoMiddleware.ROTAS_PUBLICAS
    assert client.get("/docs").status_code == 200


def test_nenhuma_rota_publica_e_letra_morta():
    """Toda entrada da lista tem que corresponder a uma rota que existe.

    A conferência usa o schema OpenAPI, e não `app.routes`: o schema é o
    contrato publicado e sua forma é estável entre versões do FastAPI,
    enquanto a estrutura de `app.routes` já mudou.

    As rotas de documentação entram à parte porque não são operações da
    API e, por isso, não aparecem no schema.
    """
    do_schema = set(app.openapi()["paths"])
    da_documentacao = {"/docs", "/redoc", "/openapi.json"}
    conhecidas = do_schema | da_documentacao

    for entrada in AutenticacaoMiddleware.ROTAS_PUBLICAS:
        assert entrada in conhecidas, (
            f"{entrada} está na lista de rotas públicas e não corresponde "
            f"a nenhuma rota da aplicação"
        )


def test_rota_protegida_continua_exigindo_sessao():
    assert client.get("/api/auth/me").status_code == 401
