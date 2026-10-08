import uuid
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_proximidade import ServicoProximidade
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from shared.database import SessionLocal
from mobilidade.models.linha_acompanhada import LinhaAcompanhada


def criar_worker(
    servico: ServicoRastreamento,
    intervalo_minutos: int = 5,
    servico_proximidade: Optional[ServicoProximidade] = None,
) -> BackgroundScheduler:
    """
    Cria o scheduler com os jobs de monitoramento.

    - "monitoramento-atrasos": alerta de atraso da linha acompanhada
      (US #27).
    - "monitoramento-proximidade": alerta de proximidade da parada de
      destino (US #172) — só é criado quando `servico_proximidade` é
      informado; mesmo intervalo, mesma filosofia de ciclo.

    Os dois jobs abrem a própria sessão e isolam falha por iteração:
    um ciclo quebrado não derruba o scheduler nem o outro job.
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

        scheduler.add_job(
            func=job_proximidade,
            trigger="interval",
            minutes=intervalo_minutos,
            id="monitoramento-proximidade",
            replace_existing=True,
        )

    return scheduler
