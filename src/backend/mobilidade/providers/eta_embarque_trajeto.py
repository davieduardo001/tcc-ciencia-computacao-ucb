# ETA até a parada de embarque de uma rota favorita — US #22/#207
#
# A favorita guarda linha, origem e destino em coordenadas, sem sentido nem
# parada. Aqui se descobre as duas coisas pelas paradas ingeridas da linha
# (o mesmo `codigo_da_parada` do planejador, #190) e se mede a chegada com
# o motor de `chegadas_da_rota`: ao vivo pelo trajeto, senão a passagem
# prevista pela grade, senão nada (RN-09). Sem linha reta.

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from mobilidade.chegadas_da_rota import (
    PedidoDePerna,
    chegada_da_perna,
    codigo_da_parada,
    vinculos_da_rota,
)
from mobilidade.models.parada import RotaParada
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.providers.contratos_rotas_favoritas import EtaEmbarque, FavoritaMonitorada
from mobilidade.rota_service import RotaService


class EtaDoEmbarquePorTrajeto:
    """
    EtaDoEmbarqueProvider sobre o trajeto ingerido (`rota`, `rota_parada`).

    O `RotaService` é do worker (cache próprio dos trajetos), como no
    EtaDoDestinoPorTrajeto do alerta de proximidade.
    """

    def __init__(self, rota_service: RotaService) -> None:
        self._rotas = rota_service

    def eta(
        self,
        favorita: FavoritaMonitorada,
        veiculos: list[PosicaoVeiculo],
        agora: datetime,
        db: Session,
    ) -> EtaEmbarque | None:
        trecho = self._trecho(favorita, db)
        if trecho is None:
            return None
        sentido, embarque = trecho

        chegada = chegada_da_perna(
            db,
            PedidoDePerna(favorita.numero_linha, sentido, embarque, None),
            veiculos,
            self._rotas,
            agora,
        ).embarque
        if chegada.eta_minutos is None:
            return None
        return EtaEmbarque(eta_minutos=chegada.eta_minutos, ao_vivo=chegada.fonte == "ao_vivo")

    @staticmethod
    def _trecho(favorita: FavoritaMonitorada, db: Session) -> tuple[str, str] | None:
        """
        (sentido, código da parada de embarque) da favorita.

        Prefere o sentido em que a parada de descer vem DEPOIS da de subir:
        a mesma esquina pode ter parada nos dois sentidos, e só um deles leva
        ao destino. Sem parada de descer reconhecida, fica com o primeiro
        sentido que tem a de subir.
        """
        sentidos = [
            s
            for (s,) in db.query(RotaParada.sentido)
            .filter(RotaParada.numero == favorita.numero_linha)
            .distinct()
            .order_by(RotaParada.sentido)
        ]

        so_embarque: tuple[str, str] | None = None
        for sentido in sentidos:
            vinculos = vinculos_da_rota(db, favorita.numero_linha, sentido)
            sobe = codigo_da_parada(vinculos, favorita.origem_lat, favorita.origem_lng)
            if sobe is None:
                continue
            desce = codigo_da_parada(vinculos, favorita.destino_lat, favorita.destino_lng)
            indice = {parada.codigo: v.indice_trajeto for parada, v in vinculos}
            if desce is not None and indice[desce] > indice[sobe]:
                return sentido, sobe
            if so_embarque is None:
                so_embarque = (sentido, sobe)
        return so_embarque
