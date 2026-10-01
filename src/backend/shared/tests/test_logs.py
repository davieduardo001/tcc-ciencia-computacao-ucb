"""LGPD — a query string (coordenadas do usuário) não pode ir para o
log de acesso do uvicorn."""

import logging

from shared.logs import RedactorQueryString


def _registro_de_acesso(caminho: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s" %d',
        args=("127.0.0.1:0", "GET", caminho, 200),
        exc_info=None,
    )


def test_redator_remove_a_query_string():
    registro = _registro_de_acesso(
        "/mobilidade/rotas?origem_lat=-15.83&origem_lng=-48.05&destino_lat=0&destino_lng=0"
    )

    assert RedactorQueryString().filter(registro) is True
    assert registro.args[2] == "/mobilidade/rotas?[omitido]"


def test_redator_nao_mexe_em_caminho_sem_query_string():
    registro = _registro_de_acesso("/health")

    RedactorQueryString().filter(registro)

    assert registro.args[2] == "/health"


def test_redator_ignora_logger_diferente():
    registro = _registro_de_acesso("/mobilidade/rotas?origem_lat=-15.83")
    registro.name = "outro.logger"

    RedactorQueryString().filter(registro)

    # Sem ser o logger de acesso do uvicorn, nada é alterado.
    assert "?" in registro.args[2]
