import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from mobilidade.eta_service import eta_minutos_veiculo, estimar_viagem, proximo_horario_previsto
from mobilidade.geocode_service import GeocodeService
from mobilidade.geometria import TrajetoMedido
from mobilidade.linha_service import LinhaService
from mobilidade.models.linha import Linha
from mobilidade.parada_service import ParadaService
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from mobilidade.providers.linha_google_maps import LinhaGoogleMapsProvider
from mobilidade.providers.linha_mock import LinhaMockProvider
from mobilidade.posicao_service import FUSO_SEMOB, PosicaoService
from mobilidade.rota_service import RotaService
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.schemas import (
    LinhaResponse,
    LinhaResumoResponse,
    LugarResponse,
    OpcaoViagemResponse,
    ParadaDetalheResponse,
    PosicaoVeiculoResponse,
    PosicoesLinhaResponse,
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

# US #16 — uma instância só por processo: o cache do feed de GPS é
# compartilhado entre todos os usuários (ver posicao_service.py).
_posicao_service = PosicaoService()

# US #18 — sem estado próprio, só lê a tabela `linha` sob demanda.
_parada_service = ParadaService()


def get_servico() -> ServicoRastreamento:
    return ServicoRastreamento(FornecedorGTFSMock(), NotificadorNulo())


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
async def calcular_rotas(
    origem_lat: float = Query(..., ge=-90, le=90),
    origem_lng: float = Query(..., ge=-180, le=180),
    destino_lat: float = Query(..., ge=-90, le=90),
    destino_lng: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db),
):
    """
    US #20 — Calcular Rota de Origem até Destino por Ônibus.
    US #159 — ETA real de cada opção, a partir da posição ao vivo dos
              ônibus (embarque) e do intervalo médio entre veículos
              (baldeação) — ver `eta_service.estimar_viagem`.

    Cenário 1: rota simples → opções com uma perna (uma linha só).
    Cenário 2: rota com baldeação → quando não há linha direta, opções
               com duas pernas e o ponto de troca.
    Cenário 3: nenhuma rota → lista vazia (não é erro).
    Cenário 5: destino por endereço/referência → resolvido antes, em
               GET /mobilidade/lugares.

    `duracao_estimada_min` (velocidade média) nunca some: é o que o
    front mostra quando não há ETA real (`tipo_estimativa == "teorica"`).
    Planejamento por horário de tabela é a US #115, fora de escopo.
    """
    opcoes = await run_in_threadpool(
        _rota_service.calcular, db, (origem_lat, origem_lng), (destino_lat, destino_lng)
    )
    if not opcoes:
        return []

    agora = datetime.now(timezone.utc)
    numeros_linha = {perna.numero for opcao in opcoes for perna in opcao.pernas}
    posicoes_por_linha = await _posicao_service.posicoes_das_linhas(numeros_linha)

    trajetos_por_perna: dict[tuple[str, str], TrajetoMedido] = {}
    for opcao in opcoes:
        for perna in opcao.pernas:
            chave = (perna.numero, perna.sentido)
            if chave in trajetos_por_perna:
                continue
            resolvido = _rota_service.trajeto_medido(db, perna.numero, perna.sentido)
            if resolvido is not None:
                trajetos_por_perna[chave] = resolvido[0]

    respostas = []
    for opcao in opcoes:
        estimativa = estimar_viagem(opcao, posicoes_por_linha, trajetos_por_perna, agora)
        respostas.append(
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
                        "espera_min": est_perna.espera_min,
                        "fonte_espera": est_perna.fonte,
                        "prefixo_veiculo": est_perna.prefixo_veiculo,
                        "intervalo_medio_min": est_perna.intervalo_medio_min,
                    }
                    for perna, est_perna in zip(opcao.pernas, estimativa.pernas)
                ],
                baldeacoes=opcao.baldeacoes,
                distancia_km=opcao.distancia_km,
                caminhada_metros=opcao.caminhada_metros,
                duracao_estimada_min=opcao.duracao_estimada_min,
                duracao_real_min=estimativa.duracao_real_min,
                tipo_estimativa=estimativa.tipo,
                calculado_em=agora.isoformat(),
            )
        )
    return respostas


@router.get("/paradas", response_model=ParadaDetalheResponse)
def obter_parada(lat: float, lng: float, db: Session = Depends(get_db)):
    """
    US #18 — Ver Detalhes de uma Parada.

    Cenário 1: parada encontrada → nome, código, linhas que passam por
               ela e os próximos horários previstos.
    Cenário 2: parada sem horário previsto cadastrado → resposta normal
               com `proximos_horarios` vazio; o front exibe o aviso.
    Cenário 3 (fechar o painel) é responsabilidade só do front.

    404 quando nenhuma linha cacheada tem parada perto de (lat, lng) —
    só acontece se o front mandar uma coordenada que não veio do próprio
    mapa (ex: chamada manual à API).
    """
    resultado = _parada_service.obter_por_coordenada(db, lat, lng)

    if resultado is None:
        raise HTTPException(status_code=404, detail="Parada não encontrada.")

    return ParadaDetalheResponse(
        nome=resultado.nome,
        codigo=resultado.codigo,
        lat=resultado.lat,
        lng=resultado.lng,
        linhas=[
            {"numero": l.numero, "nome": l.nome, "sentido": l.sentido}
            for l in resultado.linhas
        ],
        proximos_horarios=resultado.proximos_horarios,
    )


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


@router.get("/linhas/{numero_linha}/posicoes", response_model=PosicoesLinhaResponse)
async def posicoes_da_linha(
    numero_linha: str,
    lat: float | None = Query(None, description="Latitude do usuário (US #19)"),
    lng: float | None = Query(None, description="Longitude do usuário (US #19)"),
    db: Session = Depends(get_db),
):
    """
    US #16 — Rastrear Posição do Ônibus em Tempo Real.
    US #19 — Ver Tempo Estimado de Chegada (quando `lat`/`lng` informados).

    Cenário 1: veículos em operação → posições atuais no mapa.
    Cenário 2: atualização automática → o front repete esta chamada.
    Cenário 3: nenhum veículo em operação → `veiculos` vazio; com
               lat/lng informados, `proximo_horario_previsto` traz o
               horário teórico mais próximo em vez de um ETA.
    Cenário 4/5: cada veículo traz `eta_minutos` — calculado a partir da
               posição do usuário quando o veículo está em movimento, ou
               `None` quando parado/sem velocidade (a pílula então
               mostra só o número da linha).
    """
    veiculos = await _posicao_service.posicoes_da_linha(numero_linha)
    tem_localizacao_usuario = lat is not None and lng is not None

    # US #19 — quando dá para resolver a geometria da linha, o ETA é
    # medido ao longo do trajeto real (e descarta veículo de sentido
    # errado ou que já passou), não em linha reta. Sem rota ingerida
    # para esta linha, `eta_minutos_veiculo` cai sozinho para a
    # estimativa em linha reta original.
    trajeto_sentido = (
        _rota_service.trajeto_medido(db, numero_linha) if tem_localizacao_usuario else None
    )
    trajeto = trajeto_sentido[0] if trajeto_sentido else None
    sentido_resolvido = trajeto_sentido[1] if trajeto_sentido else None
    agora = datetime.now(timezone.utc)

    resposta_veiculos = [
        PosicaoVeiculoResponse(
            prefixo=v.prefixo,
            lat=v.lat,
            lng=v.lng,
            sentido=v.sentido,
            velocidade=v.velocidade,
            direcao=v.direcao,
            atualizado_em=v.atualizado_em.isoformat(),
            operadora=v.operadora,
            eta_minutos=(
                eta_minutos_veiculo(
                    v,
                    lat_alvo=lat,
                    lng_alvo=lng,
                    agora=agora,
                    trajeto=trajeto,
                    sentido_alvo=sentido_resolvido,
                )
                if tem_localizacao_usuario
                else None
            ),
        )
        for v in veiculos
    ]

    horario_previsto = None
    if tem_localizacao_usuario and not resposta_veiculos:
        linha_cacheada = (
            db.query(Linha).filter(Linha.numero == numero_linha).one_or_none()
        )
        if linha_cacheada is not None:
            horario_previsto = proximo_horario_previsto(
                linha_cacheada.horarios_previstos, datetime.now(FUSO_SEMOB)
            )

    return PosicoesLinhaResponse(
        numero=numero_linha,
        veiculos=resposta_veiculos,
        proximo_horario_previsto=horario_previsto,
    )


@router.get("/alertas")
def listar_alertas(
    servico: ServicoRastreamento = Depends(get_servico),
    usuario_id: str = Header(...),
    db: Session = Depends(get_db),
):
    uid = uuid.UUID(usuario_id)
    alertas = servico.listar_alertas(uid, db)
    return [
        {
            "id": str(a.id),
            "linha_id": a.linha_id,
            "status": a.status,
            "atraso_inicio_minutos": a.atraso_inicio_minutos,
            "ultimo_atraso_notificado": a.ultimo_atraso_notificado,
            "ultimo_alerta_enviado_em": a.ultimo_alerta_enviado_em,
            "criado_em": a.criado_em,
            "cancelado_em": a.cancelado_em,
        }
        for a in alertas
    ]


@router.get("/linhas-acompanhadas")
def listar_linhas_acompanhadas(
    servico: ServicoRastreamento = Depends(get_servico),
    usuario_id: str = Header(...),
    db: Session = Depends(get_db),
):
    uid = uuid.UUID(usuario_id)
    linhas = servico.listar_linhas_acompanhadas(uid, db)
    return [
        {
            "linha_id": l.linha_id,
            "criado_em": l.criado_em,
            "ativo": l.ativo,
        }
        for l in linhas
    ]
