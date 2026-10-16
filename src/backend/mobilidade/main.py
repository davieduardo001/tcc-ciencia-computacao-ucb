from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from shared.logs import instalar_redator_de_acesso
from mobilidade.routes import router as mobilidade_router
from mobilidade.workers.monitoramento import criar_worker
from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_proximidade import ServicoProximidade
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from mobilidade.providers.viagens_ativas_banco import ViagensAtivasDoBanco
from mobilidade.viagem_routes import router as viagem_router
from mobilidade.providers.preferencias_banco import PreferenciasDoBanco
from mobilidade.providers.veiculos_ao_vivo import VeiculosAoVivo

instalar_redator_de_acesso()
settings = get_settings()

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


@app.on_event("startup")
def startup():
    servico = ServicoRastreamento(FornecedorGTFSMock(), NotificadorNulo())

    # US #172 — alerta de proximidade da parada, agora sobre as viagens
    # reais da US #171 (o provider provisório devolvia sempre []).
    servico_proximidade = ServicoProximidade(
        viagens=ViagensAtivasDoBanco(),
        veiculos=VeiculosAoVivo(),
        preferencias=PreferenciasDoBanco(),
        notificador=NotificadorNulo(),
    )

    intervalo = int(getattr(settings, "WORKER_INTERVAL_MINUTES", 5))
    scheduler = criar_worker(
        servico,
        intervalo_minutos=intervalo,
        servico_proximidade=servico_proximidade,
    )
    scheduler.start()
    app.state.scheduler = scheduler


@app.on_event("shutdown")
def shutdown():
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)


@app.get("/")
def root():
    return {"message": "Movecity — Serviço mobilidade"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mobilidade", "environment": settings.ENVIRONMENT}
