from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mobilidade.linha_service import LinhaService
from mobilidade.providers.linha_google_maps import LinhaGoogleMapsProvider
from mobilidade.providers.linha_mock import LinhaMockProvider
from mobilidade.schemas import LinhaResponse
from shared.config import get_settings
from shared.database import get_db

router = APIRouter()

# ---------------------------------------------------------------------------
# US #15 — Provider de linha: Google Maps se GOOGLE_MAPS_API_KEY estiver
# configurada, mock caso contrário. A troca é automática e não exige
# nenhuma mudança de código — só configurar o secret na plataforma.
# ---------------------------------------------------------------------------
_settings = get_settings()
_linha_provider = (
    LinhaGoogleMapsProvider() if _settings.GOOGLE_MAPS_API_KEY else LinhaMockProvider()
)
_linha_service = LinhaService(_linha_provider)


@router.get("/hello")
def hello():
    return {"service": "mobilidade", "status": "ok"}


@router.get("/teste-kelvin")
def teste_kelvin():
    return {"service": "mobilidade", "autor": "Kelvin963", "mensagem": "hello world"}


@router.get("/linhas/{numero_linha}", response_model=LinhaResponse)
async def buscar_linha(numero_linha: str, db: Session = Depends(get_db)):
    """
    US #15 — Buscar Linha por Número.

    Cenário 1: linha encontrada → paradas, trajeto e horários previstos.
    Cenário 2: linha não encontrada → 404.
    Cenário 3: resposta rápida → resolvido pelo cache sob demanda do
               LinhaService (só chama a fonte externa na primeira busca
               de cada linha, ou quando o cache expira).
    """
    resultado = await _linha_service.buscar(numero_linha, db)

    if resultado is None:
        raise HTTPException(status_code=404, detail="Linha não encontrada.")

    return LinhaResponse(
        numero=resultado.numero,
        nome=resultado.nome,
        sentido=resultado.sentido,
        paradas=[
            {"nome": p.nome, "lat": p.lat, "lng": p.lng} for p in resultado.paradas
        ],
        trajeto=resultado.trajeto,
        horarios_previstos=resultado.horarios_previstos,
    )
