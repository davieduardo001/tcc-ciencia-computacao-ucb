import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from shared.database import SessionLocal
from shared.logs import instalar_redator_de_acesso
from mobilidade.routes import router as mobilidade_router
from mobilidade.workers.monitoramento import criar_worker, intervalo_proximidade_do_ambiente
from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_proximidade import ServicoProximidade
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from mobilidade.providers.viagens_ativas_banco import ViagensAtivasDoBanco
from mobilidade.viagem_routes import router as viagem_router
from mobilidade.push_routes import router as push_router
from mobilidade.web_push import NotificadorWebPush, configuracao_vapid_do_ambiente
from mobilidade.providers.preferencias_banco import PreferenciasDoBanco
from mobilidade.providers.veiculos_ao_vivo import VeiculosAoVivo
from mobilidade.providers.eta_destino_trajeto import EtaDoDestinoPorTrajeto
from mobilidade.rota_service import RotaService

instalar_redator_de_acesso()
settings = get_settings()
logger = logging.getLogger(__name__)

# Threads que falam com os serviços de push dos navegadores. Poucas de
# propósito: o alerta de proximidade dispara por viagem, não em massa.
MAX_THREADS_WEB_PUSH = 4

app = FastAPI(
    title="Movecity — Mobilidade",
    description="Serviço de mobilidade da API de mobilidade urbana colaborativa",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mobilidade_router, prefix="/mobilidade", tags=["mobilidade"])
app.include_router(viagem_router, prefix="/mobilidade", tags=["viagem"])
app.include_router(push_router, prefix="/mobilidade", tags=["push"])


def _notificador_de_proximidade(app: FastAPI):
    """
    Web Push quando as três variáveis VAPID existem e são coerentes; senão o
    no-op de sempre (o aviso continua chegando DENTRO do app). O alerta de
    atraso (#27) não passa por aqui.
    """
    config = configuracao_vapid_do_ambiente()
    if not config.disponivel:
        logger.info("Web Push desligado (VAPID não configurado): alerta de proximidade só no app.")
        return NotificadorNulo()

    executor = ThreadPoolExecutor(max_workers=MAX_THREADS_WEB_PUSH, thread_name_prefix="web-push")
    app.state.executor_push = executor
    logger.info("Web Push ligado para o alerta de proximidade.")
    return NotificadorWebPush(config, SessionLocal, executor=executor)


@app.on_event("startup")
def startup():
    servico = ServicoRastreamento(FornecedorGTFSMock(), NotificadorNulo())

    # US #172 — alerta de proximidade da parada, agora sobre as viagens
    # reais da US #171 (o provider provisório devolvia sempre []).
    # O ETA é medido ao longo do trajeto até a parada de destino, pelo ônibus
    # da viagem. O RotaService é só do worker: o cache dos trajetos não é
    # dividido com as requisições HTTP.
    servico_proximidade = ServicoProximidade(
        viagens=ViagensAtivasDoBanco(),
        veiculos=VeiculosAoVivo(),
        preferencias=PreferenciasDoBanco(),
        notificador=_notificador_de_proximidade(app),
        eta=EtaDoDestinoPorTrajeto(RotaService()),
    )

    intervalo = int(getattr(settings, "WORKER_INTERVAL_MINUTES", 5))
    scheduler = criar_worker(
        servico,
        intervalo_minutos=intervalo,
        servico_proximidade=servico_proximidade,
        # None (padrão) mantém o intervalo geral; ver monitoramento.py.
        intervalo_proximidade_segundos=intervalo_proximidade_do_ambiente(),
    )
    scheduler.start()
    app.state.scheduler = scheduler


@app.on_event("shutdown")
def shutdown():
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)
    executor_push = getattr(app.state, "executor_push", None)
    if executor_push:
        executor_push.shutdown(wait=False, cancel_futures=True)


@app.get("/")
def root():
    return {"message": "Movecity — Serviço mobilidade"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mobilidade", "environment": settings.ENVIRONMENT}
