# Contratos da US #28 — Receber alerta de cancelamento de viagem
#
# Define a interface (typing.Protocol) que o ServicoCancelamento consome
# para descobrir QUEM acompanha cada linha, no mesmo padrão de
# contratos_proximidade.py (US #172). As demais dependências (veículos,
# preferências, notificador) já têm contrato na US #172/#29 e são
# reaproveitadas.
#
# ---------------------------------------------------------------------------
# SUPosições PROVISÓRIAS
# ---------------------------------------------------------------------------
#
# 1. DESTINATÁRIOS — duas fontes, uma resposta
#    O Cenário 1 da US #28 fala em "linha nos favoritos ou acompanhando-a
#    ativamente". As duas fontes existem hoje:
#      - `linhas_acompanhadas` (mobilidade, US #27) — quem segue a linha;
#      - `rotas_favoritas` (colaboração, US #25) — quem salvou uma rota
#        que passa por ela (`numero_linha` desnormalizado).
#    As duas tabelas vivem no MESMO banco (a issue #42 ainda não separou),
#    então a implementação real lê as duas por SQL direto — o mesmo
#    artifício de preferencias_banco.py, pelo mesmo motivo: o Dockerfile
#    do mobilidade não copia o pacote `colaboracao`.
#    Quando a #42 separar bancos, a troca é só aqui (provider por HTTP
#    via Gateway) — o ServicoCancelamento não muda.
#
# 2. CANCELAMENTO PELO OPERADOR — sem fonte hoje
#    O Cenário 1 prevê "cancelada pelo operador ou detectada como ausente".
#    Hoje não existe tabela, endpoint nem feed de cancelamento operacional
#    no SEMOB. Por isso o serviço só implementa a detecção por AUSÊNCIA
#    (Cenário 3) e deixa o campo `status` do AlertaCancelamento pronto
#    ("suspeito" × "confirmado") para quando a fonte existir.

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy.orm import Session


@runtime_checkable
class DestinatariosProvider(Protocol):
    """
    Contrato para listar quem acompanha cada linha (Cenário 1 da US #28).

    Implementação real: DestinatariosDoBanco (destinatarios_banco.py) —
    une `linhas_acompanhadas` e `rotas_favoritas` por SQL direto.
    """

    def listar_por_linha(self, db: Session) -> dict[str, set[UUID]]:
        """
        Linhas monitoradas e, para cada uma, os usuários a serem avisados.

        Chave: número da linha (ex: "0.110"). Valor: conjunto de
        usuario_id. Um usuário que aparece nas duas fontes conta uma vez.

        Retorna `{}` quando nada está sendo acompanhado — nunca lança
        exceção (sem destinatário, o ciclo inteiro não faz nada).
        """
        ...
