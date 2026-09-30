# LGPD — os 4 serviços sobem `uvicorn` sem desativar o log de acesso
# padrão, que grava a linha inteira da requisição, incluindo a query
# string. Em `/mobilidade/rotas` e `/mobilidade/lugares/reverso` isso é
# a coordenada de origem/destino informada pelo usuário indo parar no
# log do processo — geolocalização é dado pessoal, não deveria ficar
# ali. Este filtro corta a query string antes do uvicorn formatar a
# linha de log; o path continua visível para diagnóstico.

import logging


class RedactorQueryString(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "uvicorn.access" and len(record.args) >= 3:
            caminho = str(record.args[2])
            if "?" in caminho:
                args = list(record.args)
                args[2] = caminho.split("?", 1)[0] + "?[omitido]"
                record.args = tuple(args)
        return True


def instalar_redator_de_acesso() -> None:
    logging.getLogger("uvicorn.access").addFilter(RedactorQueryString())
