import uuid
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from shared.database import SessionLocal
from mobilidade.models.linha_acompanhada import LinhaAcompanhada


def criar_worker(
    servico: ServicoRastreamento,
    intervalo_minutos: int = 5,
) -> BackgroundScheduler:
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

    return scheduler
