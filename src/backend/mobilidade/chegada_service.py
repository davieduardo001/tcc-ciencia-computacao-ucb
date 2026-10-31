# Chegadas numa parada física — card #179, ponto ⑤b.
#
# Responde "quando o ônibus chega NESTA parada" — e não "quando chega onde eu
# estou" (a pílula antiga media até o GPS do usuário) nem "quando sai do
# terminal" (o painel antigo mostrava a saída da origem como se fosse a
# passagem aqui).
#
# Duas fontes, nunca misturadas, e cada resposta diz qual usou (RN-10):
#
#  • ao_vivo  — distância restante ao longo do trajeto até a parada (o
#               `indice_trajeto` pré-calculado na ingestão, #173) dividida
#               pela velocidade efetivamente percorrida pelo ônibus (D3b).
#               O sentido vem do vínculo parada↔rota, não de heurística.
#  • previsto — sem ônibus a caminho: horário de SAÍDA do dia corrente +
#               tempo de percurso × fração do trajeto em que a parada está.
#               Só usa `horarios_por_dia` (RN-08: nunca mistura dia útil,
#               sábado e domingo) e nunca a lista antiga e plana da linha.
#
# Sem nenhuma das duas, devolve `eta_minutos=None` — RN-09, "não inventar".
# US #199 — entra uma terceira origem, intermediária (RN-C2/RN-C3):
#
#  • colaborativo — sem ônibus da SEMOB a caminho, mas com passageiros
#               compartilhando a posição do ônibus (consentimento LGPD,
#               leitura efêmera): o ETA usa o veículo "colaborativo"
#               injetado no PosicaoService, com o selo declarando a
#               origem. Nunca substitui um ao_vivo.
# Observado de verdade (média histórica de passagem) fica de fora: exigiria
# persistir passagens, e isso é uma decisão arquitetural à parte (D3-C).

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from math import cos, radians
from typing import Literal

from sqlalchemy.orm import Session

from mobilidade.eta_service import eta_ate_indice
from mobilidade.geometria import distancia_metros
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota
from mobilidade.parada_service import vinculos_por_linha
from mobilidade.posicao_service import FUSO_SEMOB, PosicaoService
from mobilidade.rota_service import RotaService
from mobilidade.semob_source import horarios_do_dia

# Uma passagem prevista mais distante que isso não ajuda quem está esperando
# (e, de madrugada, empurraria a próxima passagem do dia seguinte para a tela).
ETA_PREVISTO_MAXIMO_MIN = 12 * 60

# Quão longe da posição do usuário uma parada ainda conta como "a minha".
RAIO_PARADA_DO_USUARIO_M = 400.0

# Duas paradas, de sentidos diferentes, a até esta diferença de distância do
# usuário contam como empate (ele está no meio): as duas entram.
EMPATE_ENTRE_SENTIDOS_M = 15.0

_METROS_POR_GRAU = 111_000.0

FonteChegada = Literal["ao_vivo", "colaborativo", "previsto"]


@dataclass(frozen=True)
class ChegadaNaParada:
    numero: str
    nome: str
    rota_sentido: str
    eta_minutos: float | None
    fonte: FonteChegada | None
    prefixo: str | None = None
    horario_previsto: str | None = None
    veiculos_a_caminho: int = 0


@dataclass(frozen=True)
class ChegadasDaParada:
    parada: Parada
    chegadas: list[ChegadaNaParada]


def _hora_do_dia(dia: date, hhmm: str) -> datetime | None:
    try:
        horas, minutos = hhmm.split(":")
        return datetime(dia.year, dia.month, dia.day, int(horas), int(minutos), tzinfo=FUSO_SEMOB)
    except (ValueError, TypeError):
        return None


def passagem_prevista(
    rota: Rota,
    vinculo: RotaParada,
    comprimento_m: float | None,
    agora: datetime,
) -> tuple[datetime, float] | None:
    """
    Próxima passagem prevista NESTA parada: saída do terminal + o trecho do
    tempo de percurso proporcional ao quanto da rota já foi percorrido até
    a parada. Devolve (instante, minutos até lá) ou `None` quando falta dado.

    Olha o dia anterior, o de hoje e o seguinte: uma saída às 23:50 passa
    numa parada do meio do trajeto depois da meia-noite, e a primeira saída
    de amanhã pode ser a próxima passagem de quem espera à noite.
    """
    if rota.tempo_percurso_min is None or rota.horarios_por_dia is None:
        return None
    if not comprimento_m or comprimento_m <= 0:
        return None

    fracao = min(max(vinculo.distancia_acumulada_m / comprimento_m, 0.0), 1.0)
    percurso = timedelta(minutes=rota.tempo_percurso_min * fracao)
    agora_local = agora.astimezone(FUSO_SEMOB)

    proxima: datetime | None = None
    for deslocamento in (-1, 0, 1):
        dia = (agora_local + timedelta(days=deslocamento)).date()
        for hhmm in horarios_do_dia(rota.horarios_por_dia, dia.weekday()):
            saida = _hora_do_dia(dia, hhmm)
            if saida is None:
                continue
            passagem = saida + percurso
            if passagem < agora_local:
                continue
            if proxima is None or passagem < proxima:
                proxima = passagem

    if proxima is None:
        return None
    minutos = (proxima - agora_local).total_seconds() / 60
    if minutos > ETA_PREVISTO_MAXIMO_MIN:
        return None
    return proxima, minutos


async def chegadas_da_parada(
    db: Session,
    codigo: str,
    posicao_service: PosicaoService,
    rota_service: RotaService,
    agora: datetime | None = None,
    colaborativos=None,
) -> ChegadasDaParada | None:
    """
    Chegadas de cada linha que passa na parada `codigo`, as mais próximas
    primeiro. `None` quando o código não existe.

    US #199 — com `colaborativos`, veículos "colaborativos" entram no pool
    de posições por cima do feed; cada chegada declara se saiu de um
    ônibus da SEMOB (`ao_vivo`) ou de passageiro (`colaborativo`).
    """
    agora = agora or datetime.now(timezone.utc)

    parada = db.query(Parada).filter(Parada.codigo == codigo).one_or_none()
    if parada is None:
        return None

    vinculos = vinculos_por_linha(db, parada.id)
    if not vinculos:
        return ChegadasDaParada(parada=parada, chegadas=[])

    posicoes = await posicao_service.posicoes_das_linhas(
        vinculos.keys(), db=db, colaborativos=colaborativos
    )

    chegadas: list[ChegadaNaParada] = []
    for numero, (vinculo, rota) in vinculos.items():
        medido = rota_service.trajeto_medido(db, numero, rota.sentido)
        trajeto = medido[0] if medido else None

        etas: list[tuple[float, str, str]] = []
        if trajeto is not None:
            for veiculo in posicoes.get(numero, []):
                eta = eta_ate_indice(veiculo, trajeto, vinculo.indice_trajeto, rota.sentido, agora)
                if eta is not None:
                    etas.append((eta, veiculo.prefixo, veiculo.fonte))

        if etas:
            # O mais próximo vence; empate exato é da SEMOB (RN-C2). O selo
            # acompanha o vencedor — `colaborativo` quando ele é o fallback.
            melhor = min(etas, key=lambda e: (e[0], e[2] != "ao_vivo"))
            eta, prefixo, fonte_ao_vivo = melhor
            chegadas.append(
                ChegadaNaParada(
                    numero=numero,
                    nome=rota.nome,
                    rota_sentido=rota.sentido,
                    eta_minutos=round(eta, 1),
                    fonte=fonte_ao_vivo if fonte_ao_vivo == "colaborativo" else "ao_vivo",
                    prefixo=prefixo,
                    veiculos_a_caminho=len(etas),
                )
            )
            continue

        previsto = passagem_prevista(rota, vinculo, trajeto.comprimento_m if trajeto else None, agora)
        if previsto is not None:
            instante, minutos = previsto
            chegadas.append(
                ChegadaNaParada(
                    numero=numero,
                    nome=rota.nome,
                    rota_sentido=rota.sentido,
                    eta_minutos=round(minutos, 1),
                    fonte="previsto",
                    horario_previsto=instante.strftime("%H:%M"),
                )
            )
            continue

        chegadas.append(
            ChegadaNaParada(
                numero=numero,
                nome=rota.nome,
                rota_sentido=rota.sentido,
                eta_minutos=None,
                fonte=None,
            )
        )

    chegadas.sort(key=_ordem_de_exibicao)
    return ChegadasDaParada(parada=parada, chegadas=chegadas)


def _ordem_de_exibicao(c: ChegadaNaParada) -> tuple[int, float, str]:
    """Ao vivo antes de colaborativo antes de previsto antes de sem dado; dentro de cada grupo, o mais próximo."""
    grupo = {"ao_vivo": 0, "colaborativo": 1, "previsto": 2}.get(c.fonte or "", 3)
    return grupo, c.eta_minutos if c.eta_minutos is not None else float("inf"), c.numero


def paradas_proximas_do_usuario(
    db: Session,
    numero_linha: str,
    lat: float,
    lng: float,
    raio_m: float = RAIO_PARADA_DO_USUARIO_M,
) -> dict[str, tuple[Parada, RotaParada]]:
    """
    "Qual é a minha parada" para uma linha: por sentido, a parada dela mais
    próxima do usuário, dentro de `raio_m`. Fica só o sentido da parada MAIS
    próxima (o lado da rua em que a pessoa está) — ônibus do sentido oposto
    não servem a quem espera deste lado. Empate (usuário no meio da rua, a
    até EMPATE_ENTRE_SENTIDOS_M de diferença) mantém os dois.

    Vazio quando não há parada ingerida por perto — quem chama cai então na
    projeção do GPS no traçado, que é o que existia antes.
    """
    delta_lat = raio_m / _METROS_POR_GRAU
    delta_lng = delta_lat / max(cos(radians(lat)), 0.01)

    candidatas = (
        db.query(Parada, RotaParada)
        .join(RotaParada, RotaParada.parada_id == Parada.id)
        .filter(
            RotaParada.numero == numero_linha,
            Parada.lat.between(lat - delta_lat, lat + delta_lat),
            Parada.lng.between(lng - delta_lng, lng + delta_lng),
        )
        .all()
    )

    melhor_por_sentido: dict[str, tuple[Parada, RotaParada, float]] = {}
    for parada, vinculo in candidatas:
        distancia = distancia_metros(lat, lng, parada.lat, parada.lng)
        if distancia > raio_m:
            continue
        atual = melhor_por_sentido.get(vinculo.sentido)
        if atual is None or distancia < atual[2]:
            melhor_por_sentido[vinculo.sentido] = (parada, vinculo, distancia)

    if not melhor_por_sentido:
        return {}

    mais_perto = min(d for _, _, d in melhor_por_sentido.values())
    return {
        sentido: (parada, vinculo)
        for sentido, (parada, vinculo, distancia) in melhor_por_sentido.items()
        if distancia <= mais_perto + EMPATE_ENTRE_SENTIDOS_M
    }
