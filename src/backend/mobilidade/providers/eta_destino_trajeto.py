# ETA até a parada de destino, ao longo do trajeto — US #172
#
# Implementa o `EtaDoDestinoProvider` que o ServicoProximidade consome. No
# lugar da linha reta que o alerta usava (ignora direção e não sabe se o
# ônibus já passou), mede a distância pelo traçado até a parada de destino,
# no sentido da parada, e divide pela velocidade média realmente percorrida
# — o mesmo motor da pílula do mapa e do "Chegando nesta parada" (#179).
#
# Quem decide se há alerta é o ServicoProximidade; aqui só se responde "em
# quantos minutos", ou `None` quando não dá para afirmar:
#   - sem rota ingerida para a linha, ou destino que não é parada dela;
#   - veículo parado, com posição velha ou fora do traçado;
#   - veículo no sentido oposto ao da parada;
#   - ônibus que já passou do destino (não volta).
# Nenhum desses casos cai em linha reta: melhor não avisar do que avisar
# errado (Cenário 4 da #172, RN-09).

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from mobilidade.eta_service import eta_ate_indice
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.providers.contratos_proximidade import ViagemAtiva
from mobilidade.rota_service import RotaService

# Linha circular: o veículo nunca reporta "CIRCULAR" (ver eta_service); só a
# rota tem esse rótulo, então ela entra sempre como última tentativa.
SENTIDO_CIRCULAR = "CIRCULAR"


class EtaDoDestinoPorTrajeto:
    """
    EtaDoDestinoProvider sobre o trajeto ingerido (`rota`, `rota_parada`).

    Recebe o `RotaService` por injeção: o cache dos trajetos mora nele, e o
    worker do alerta usa o seu, sem dividir estado com as requisições HTTP.
    """

    def __init__(self, rota_service: RotaService) -> None:
        self._rotas = rota_service

    def eta_minutos(
        self,
        viagem: ViagemAtiva,
        veiculo: PosicaoVeiculo,
        agora: datetime,
        db: Session,
    ) -> float | None:
        for sentido in self._sentidos_candidatos(viagem, veiculo):
            medido = self._rotas.trajeto_medido(db, viagem.numero_linha, sentido)
            if medido is None:
                continue
            trajeto, sentido_rota = medido

            vinculo = (
                db.query(RotaParada)
                .join(Parada, Parada.id == RotaParada.parada_id)
                .filter(
                    Parada.codigo == viagem.parada_destino_codigo,
                    RotaParada.numero == viagem.numero_linha,
                    RotaParada.sentido == sentido_rota,
                )
                .first()
            )
            if vinculo is None:
                # O destino não está neste sentido; tenta o próximo.
                continue

            # O sentido da rota é o alvo: veículo no sentido oposto devolve
            # None, e ônibus que já passou do destino também.
            return eta_ate_indice(veiculo, trajeto, vinculo.indice_trajeto, sentido_rota, agora)

        return None

    @staticmethod
    def _sentidos_candidatos(viagem: ViagemAtiva, veiculo: PosicaoVeiculo) -> list[str]:
        """O sentido de agora do veículo vale mais; o do embarque é reserva."""
        sentidos = [
            s.strip().upper() for s in (veiculo.sentido, viagem.sentido) if s and s.strip()
        ]
        return list(dict.fromkeys([*sentidos, SENTIDO_CIRCULAR]))
