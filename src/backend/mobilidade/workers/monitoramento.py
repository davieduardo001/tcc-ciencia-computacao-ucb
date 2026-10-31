import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_proximidade import ServicoProximidade
from mobilidade.services.servico_cancelamento import ServicoCancelamento
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from shared.database import SessionLocal
from mobilidade.models.linha_acompanhada import LinhaAcompanhada


logger = logging.getLogger(__name__)

# O feed de posições é cacheado por 20 s (posicao_service.CACHE_SEGUNDOS):
# verificar mais seguido que isso só releria o mesmo dado.
INTERVALO_MINIMO_PROXIMIDADE_SEGUNDOS = 20


def intervalo_proximidade_do_ambiente() -> Optional[int]:
    """
    Intervalo (s) do job de proximidade vindo de WORKER_PROXIMIDADE_INTERVAL_SECONDS,
    ou None para manter o intervalo geral (WORKER_INTERVAL_MINUTES).

    Existe porque a #29 permite avisar com 5 min de antecedência, e um ciclo
    de 5 min faz esse aviso chegar, em média, 2,5 min antes — às vezes quase
    em cima da parada. Ausente, em branco, não numérico ou abaixo do mínimo:
    ignora (com aviso) e mantém o padrão, que não muda.
    """
    bruto = (os.environ.get("WORKER_PROXIMIDADE_INTERVAL_SECONDS") or "").strip()
    if not bruto:
        return None
    try:
        segundos = int(bruto)
    except ValueError:
        segundos = 0
    if segundos < INTERVALO_MINIMO_PROXIMIDADE_SEGUNDOS:
        logger.warning(
            "WORKER_PROXIMIDADE_INTERVAL_SECONDS=%r ignorado: use um inteiro >= %s.",
            bruto,
            INTERVALO_MINIMO_PROXIMIDADE_SEGUNDOS,
        )
        return None
    return segundos


def criar_worker(
    servico: ServicoRastreamento,
    intervalo_minutos: int = 5,
    servico_proximidade: Optional[ServicoProximidade] = None,
    intervalo_proximidade_segundos: Optional[int] = None,
    servico_cancelamento: Optional[ServicoCancelamento] = None,
) -> BackgroundScheduler:
    """
    Cria o scheduler com os jobs de monitoramento.

    - "monitoramento-atrasos": alerta de atraso da linha acompanhada
      (US #27).
    - "monitoramento-proximidade": alerta de proximidade da parada de
      destino (US #172) — só é criado quando `servico_proximidade` é
      informado; por padrão no mesmo intervalo, mas `intervalo_proximidade_segundos`
      permite um ciclo mais curto só para ele.
    - "monitoramento-cancelamento": alerta de cancelamento de viagem
      (US #28) — criado só quando `servico_cancelamento` é informado;
      mesmo intervalo do de atrasos, porque a janela de detecção é de
      minutos e um ciclo curto não muda nada.

    Os jobs abrem a própria sessão e isolam falha por iteração:
    um ciclo quebrado não derruba o scheduler nem os demais jobs.
    """
    scheduler = BackgroundScheduler(max_instances=1)

    def job():
        db = SessionLocal()
        try:
            linhas = db.query(LinhaAcompanhada).all()
            linhas_unicas = {}
            for la in linhas:
                key = (la.usuario_id, la.linha_id)
                linhas_unicas[key] = la

            for (usuario_id, linha_id), _ in linhas_unicas.items():
                try:
                    servico.verificar_e_disparar_alertas(usuario_id, db)
                except Exception:
                    db.rollback()
        except Exception:
            db.rollback()
        finally:
            db.close()

    scheduler.add_job(
        func=job,
        trigger="interval",
        minutes=intervalo_minutos,
        id="monitoramento-atrasos",
        replace_existing=True,
    )

    if servico_proximidade is not None:
        def job_proximidade():
            db = SessionLocal()
            try:
                servico_proximidade.verificar_proximidades(db)
            except Exception:
                db.rollback()
            finally:
                db.close()

        # Padrão inalterado: mesmo intervalo do job de atrasos. Só muda se
        # quem opera o serviço pedir um ciclo mais curto (ver
        # intervalo_proximidade_do_ambiente).
        if intervalo_proximidade_segundos is not None:
            intervalo = {"seconds": intervalo_proximidade_segundos}
        else:
            intervalo = {"minutes": intervalo_minutos}

        scheduler.add_job(
            func=job_proximidade,
            trigger="interval",
            id="monitoramento-proximidade",
            replace_existing=True,
            **intervalo,
        )

    if servico_cancelamento is not None:
        def job_cancelamento():
            db = SessionLocal()
            try:
                servico_cancelamento.verificar_ciclo(db)
            except Exception:
                db.rollback()
            finally:
                db.close()

        # Mesmo intervalo do de atrasos: a janela de detecção (15–45 min)
        # absorve um ciclo a mais ou a menos sem perder a partida.
        scheduler.add_job(
            func=job_cancelamento,
            trigger="interval",
            id="monitoramento-cancelamento",
            replace_existing=True,
            minutes=intervalo_minutos,
        )

    return scheduler
