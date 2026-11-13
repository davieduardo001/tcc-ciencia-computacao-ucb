# Aviso de rotas favoritas por push — US #22, levada ao push pela #207
#
# A cada ciclo, para cada rota favorita de quem tem aparelho inscrito:
#   1. respeita o interruptor geral de notificações (#29);
#   2. mede quando o próximo ônibus da linha passa na parada de embarque;
#   3. aplica a regra da #22 (`decidir_aviso`): dois avisos por corrida,
#      antecedência e ônibus próximo, sem repetir;
#   4. grava o estado e SÓ DEPOIS notifica (como os outros alertas): se o
#      commit falhar, nada sai; se o envio falhar, o estado já impede repetir.
#
# A regra é a da #22 sem mudança, por decisão do time: uma favorita não tem
# horário, então cada ônibus da linha que se aproxima é uma corrida nova e
# gera os dois avisos.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mobilidade.models.aviso_rota_favorita import AvisoRotaFavorita
from mobilidade.providers.contratos_proximidade import (
    PreferenciasDeNotificacao,
    PreferenciasProvider,
    VeiculosProvider,
)
from mobilidade.providers.contratos_rotas_favoritas import (
    EtaDoEmbarqueProvider,
    FavoritaMonitorada,
    FavoritasProvider,
)
from mobilidade.services.servico_notificacoes import Notificador

logger = logging.getLogger(__name__)

# Mesmos limiares do Deduplicador da #22 (colaboracao/deduplicador.py).
LIMIAR_PROXIMIDADE_MINUTOS = 5
# ETA acima de antecedência + margem: o ônibus passou (ou o dado
# reiniciou) e a corrida acabou.
MARGEM_RESET_MINUTOS = 5

# Eventos retornados por `verificar_ciclo` (para log e teste).
EVENTO_ANTECEDENCIA = "antecedencia"
EVENTO_PROXIMIDADE = "proximidade"
EVENTO_PREFERENCIAS = "preferencias_desativadas"
EVENTO_SEM_ETA = "sem_eta"
EVENTO_ERRO = "erro"


class Decisao(Enum):
    ANTECEDENCIA = EVENTO_ANTECEDENCIA
    PROXIMIDADE = EVENTO_PROXIMIDADE
    FIM_DA_CORRIDA = "fim_da_corrida"


def decidir_aviso(
    antecedencia_enviada: bool,
    proximidade_enviada: bool,
    eta_minutos: float,
    ao_vivo: bool,
    antecedencia_min: int,
) -> Decisao | None:
    """
    Regra da #22, em função pura.

    - ETA acima de antecedência + margem → fim da corrida (zera o estado).
    - ETA ≤ 5 min, medido ao vivo, sem aviso de próximo → PROXIMIDADE.
      Pela grade não: "chega em 3 min" sem ônibus visto é o ônibus fantasma.
    - 5 < ETA ≤ antecedência, sem nenhum aviso ainda → ANTECEDENCIA. Depois
      do aviso de próximo, o de antecedência seria atrasado; não sai.
    """
    if eta_minutos > antecedencia_min + MARGEM_RESET_MINUTOS:
        return Decisao.FIM_DA_CORRIDA
    if eta_minutos <= LIMIAR_PROXIMIDADE_MINUTOS:
        if ao_vivo and not proximidade_enviada:
            return Decisao.PROXIMIDADE
        return None
    if eta_minutos <= antecedencia_min and not antecedencia_enviada and not proximidade_enviada:
        return Decisao.ANTECEDENCIA
    return None


class ServicoRotasFavoritas:
    """Serviço do aviso de rotas favoritas. Tudo por injeção (ver contratos)."""

    def __init__(
        self,
        favoritas: FavoritasProvider,
        veiculos: VeiculosProvider,
        preferencias: PreferenciasProvider,
        notificador: Notificador,
        eta: EtaDoEmbarqueProvider,
    ) -> None:
        self.favoritas = favoritas
        self.veiculos = veiculos
        self.preferencias = preferencias
        self.notificador = notificador
        self.eta = eta

    def verificar_ciclo(self, db: Session) -> list[str]:
        """
        Um ciclo: avalia cada favorita uma vez. Devolve um evento por favorita
        que gerou aviso ou foi pulada (EVENTO_*); fora do limiar, nada.
        Falha numa favorita não interrompe as demais.
        """
        favoritas = self.favoritas.listar(db)
        if not favoritas:
            # Lista vazia também é o que o provider devolve quando o banco
            # falha: não limpa o estado, ou o ciclo seguinte repetiria avisos.
            return []
        self._remover_orfaos({f.favorita_id for f in favoritas}, db)

        veiculos_por_linha = self.veiculos.obter_das_linhas({f.numero_linha for f in favoritas})
        agora = datetime.now(timezone.utc)
        preferencias: dict[UUID, PreferenciasDeNotificacao] = {}

        eventos: list[str] = []
        for favorita in favoritas:
            try:
                if favorita.usuario_id not in preferencias:
                    preferencias[favorita.usuario_id] = self.preferencias.obter(
                        favorita.usuario_id, db
                    )
                evento = self._verificar_favorita(
                    favorita,
                    preferencias[favorita.usuario_id],
                    veiculos_por_linha.get(favorita.numero_linha, []),
                    agora,
                    db,
                )
            except IntegrityError:
                # Outra máquina criou o estado desta favorita no mesmo
                # instante e avisou; este ciclo não repete.
                db.rollback()
                evento = None
            except Exception:
                db.rollback()
                logger.exception(
                    "Erro ao verificar rota favorita | favorita=%s | linha=%s",
                    favorita.favorita_id,
                    favorita.numero_linha,
                )
                evento = EVENTO_ERRO

            if evento:
                eventos.append(evento)

        return eventos

    # ------------------------------------------------------------------

    def _verificar_favorita(
        self,
        favorita: FavoritaMonitorada,
        pref: PreferenciasDeNotificacao,
        veiculos: list,
        agora: datetime,
        db: Session,
    ) -> str | None:
        # Cenário 3 da #207 (e da #22): notificações desligadas na #29.
        if not pref.notificacoes_ativas:
            return EVENTO_PREFERENCIAS

        eta = self.eta.eta(favorita, veiculos, agora, db)
        if eta is None:
            return EVENTO_SEM_ETA

        # Trava a linha do estado: com mais de uma máquina no worker, a
        # segunda espera a primeira gravar e já encontra o aviso enviado.
        estado = (
            db.query(AvisoRotaFavorita)
            .filter(AvisoRotaFavorita.favorita_id == favorita.favorita_id)
            .with_for_update()
            .one_or_none()
        )
        decisao = decidir_aviso(
            antecedencia_enviada=bool(estado and estado.antecedencia_enviada),
            proximidade_enviada=bool(estado and estado.proximidade_enviada),
            eta_minutos=eta.eta_minutos,
            ao_vivo=eta.ao_vivo,
            antecedencia_min=pref.antecedencia_minutos,
        )

        if decisao is None:
            db.commit()  # solta a trava
            return None

        if decisao is Decisao.FIM_DA_CORRIDA:
            if estado is not None and (estado.antecedencia_enviada or estado.proximidade_enviada):
                estado.antecedencia_enviada = False
                estado.proximidade_enviada = False
                estado.atualizado_em = datetime.utcnow()
            db.commit()
            return None

        if estado is None:
            estado = AvisoRotaFavorita(
                favorita_id=favorita.favorita_id,
                antecedencia_enviada=False,
                proximidade_enviada=False,
            )
            db.add(estado)
        if decisao is Decisao.PROXIMIDADE:
            estado.proximidade_enviada = True
        else:
            estado.antecedencia_enviada = True
        estado.atualizado_em = datetime.utcnow()
        db.commit()

        self.notificador.alerta_rota_favorita(
            str(favorita.usuario_id),
            favorita.numero_linha,
            eta.eta_minutos,
            proximo=decisao is Decisao.PROXIMIDADE,
        )
        return decisao.value

    @staticmethod
    def _remover_orfaos(ids_vivos: set[UUID], db: Session) -> None:
        """Estado de favorita apagada (ou de quem saiu do push) não serve mais."""
        try:
            db.query(AvisoRotaFavorita).filter(
                AvisoRotaFavorita.favorita_id.notin_(ids_vivos)
            ).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
            logger.warning("Falha ao limpar estado de rotas favoritas", exc_info=True)
