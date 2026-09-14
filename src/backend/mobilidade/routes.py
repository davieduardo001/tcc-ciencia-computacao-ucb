from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from mobilidade.geocode_service import GeocodeService
from mobilidade.linha_service import LinhaService
from mobilidade.providers.linha_google_maps import LinhaGoogleMapsProvider
from mobilidade.providers.linha_mock import LinhaMockProvider
from mobilidade.rota_service import RotaService
from mobilidade.schemas import (
    LinhaResponse,
    LinhaResumoResponse,
    LugarResponse,
    OpcaoViagemResponse,
)
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

# US #20 — ambos guardam cache em memória, então são instanciados uma
# vez por processo (o GeocodeService também serializa as chamadas ao
# Nominatim pra respeitar o limite de 1 req/s da política de uso).
_rota_service = RotaService()
_geocode_service = GeocodeService()


@router.get("/hello")
def hello():
    return {"service": "mobilidade", "status": "ok"}


@router.get("/teste-kelvin")
def teste_kelvin():
    return {"service": "mobilidade", "autor": "Kelvin963", "mensagem": "hello world"}


@router.get("/linhas", response_model=list[LinhaResumoResponse])
async def sugerir_linhas(q: str = "", db: Session = Depends(get_db)):
    """
    US #17 — Autocomplete de linhas.

    Sugere linhas cujo número, nome, sentido ou alguma parada combine
    com `q` (ex: buscar "Ceilândia" sugere as linhas que passam por lá).
    `q` vazio ("" ou omitido) lista todas as linhas conhecidas.
    """
    resumos = await _linha_service.sugerir(q, db)
    return [
        LinhaResumoResponse(numero=r.numero, nome=r.nome, sentido=r.sentido)
        for r in resumos
    ]


@router.get("/lugares", response_model=list[LugarResponse])
async def buscar_lugares(q: str = ""):
    """
    US #20 — Autocomplete de origem/destino por ponto de referência.

    Necessário porque os nomes de parada do SEMOB são endereços de rua
    ("Eixo L Norte, SQN 207"), que ninguém digita. Resolve nomes como
    "Rodoviária", "UnB" ou "Shopping Taguatinga" em coordenadas, via
    OpenStreetMap/Nominatim — sem chave de API e sem billing.

    Nunca falha: se o geocodificador estiver fora do ar, devolve lista
    vazia e o usuário ainda pode usar a própria localização ou clicar
    no mapa.
    """
    lugares = await _geocode_service.buscar(q)
    return [
        LugarResponse(nome=l.nome, endereco=l.endereco, lat=l.lat, lng=l.lng)
        for l in lugares
    ]


@router.get("/lugares/reverso", response_model=LugarResponse | None)
async def lugar_reverso(lat: float, lng: float):
    """
    US #20 — Nome legível de um ponto, para "usar minha localização" e
    para o clique no mapa. Devolve `null` quando não há nome conhecido —
    o front mostra a coordenada nesse caso.
    """
    lugar = await _geocode_service.reverso(lat, lng)
    if lugar is None:
        return None
    return LugarResponse(
        nome=lugar.nome, endereco=lugar.endereco, lat=lugar.lat, lng=lugar.lng
    )


@router.get("/rotas", response_model=list[OpcaoViagemResponse])
def calcular_rotas(
    origem_lat: float = Query(...),
    origem_lng: float = Query(...),
    destino_lat: float = Query(...),
    destino_lng: float = Query(...),
    db: Session = Depends(get_db),
):
    """
    US #20 — Calcular Rota de Origem até Destino por Ônibus.

    Cenário 1: rota simples → opções com uma perna (uma linha só).
    Cenário 2: rota com baldeação → quando não há linha direta, opções
               com duas pernas e o ponto de troca.
    Cenário 3: nenhuma rota → lista vazia (não é erro).
    Cenário 5: destino por endereço/referência → resolvido antes, em
               GET /mobilidade/lugares.

    A duração é estimada por velocidade média, não por horário de
    tabela: planejamento por horário é a US #115.
    """
    opcoes = _rota_service.calcular(
        db, (origem_lat, origem_lng), (destino_lat, destino_lng)
    )

    return [
        OpcaoViagemResponse(
            pernas=[
                {
                    "numero": perna.numero,
                    "sentido": perna.sentido,
                    "nome": perna.nome,
                    "embarque": perna.embarque.__dict__,
                    "desembarque": perna.desembarque.__dict__,
                    "distancia_km": perna.distancia_km,
                    "paradas_no_trecho": perna.paradas_no_trecho,
                    "trajeto": perna.trajeto,
                }
                for perna in opcao.pernas
            ],
            baldeacoes=opcao.baldeacoes,
            distancia_km=opcao.distancia_km,
            caminhada_metros=opcao.caminhada_metros,
            duracao_estimada_min=opcao.duracao_estimada_min,
        )
        for opcao in opcoes
    ]


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
