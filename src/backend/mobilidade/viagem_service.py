# Pegar o ônibus (US #171) — embarcar, acompanhar e encerrar a viagem.
#
# Regras (PRD da #171):
#   RN-04  "Em viagem" só por indicação explícita E confirmada no servidor.
#   RN-06  LGPD: a posição do usuário valida o embarque e é descartada —
#          nada daqui grava latitude/longitude do passageiro.
#   RN-15  Uma viagem ativa por usuário (o banco garante, ver models/viagem.py).
#   RN-16  Confirmar = veículo DA LINHA, com posição recente, a até
#          RAIO_EMBARQUE_M do usuário; vários → o mais próximo.
#   RN-17  Viagem esquecida expira sozinha.
#
# O progresso (próxima parada, paradas restantes) é calculado na hora da
# leitura, a partir da posição ao vivo do veículo — não é persistido (ADR-04).

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mobilidade.eta_service import IDADE_MAXIMA_ETA_MIN, TOLERANCIA_NA_PARADA_M, TOLERANCIA_TRAJETO_M
from mobilidade.geometria import distancia_metros
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.viagem import Viagem
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.rota_service import RotaService

# RN-16. 100 m é a proposta do #179 (D2): perto o bastante para ser o
# ônibus em que a pessoa está, folgado para o erro de GPS do celular. É uma
# constante porque a medição em campo pode mudá-la.
RAIO_EMBARQUE_M = 100.0

# Posição mais velha que isso não confirma embarque: o ônibus já andou.
IDADE_MAXIMA_EMBARQUE_MIN = IDADE_MAXIMA_ETA_MIN

# RN-17. Uma viagem de ônibus no DF raramente passa de 2 h; 4 h dá margem
# sem deixar quem esqueceu de tocar "Cheguei" em "Em viagem" o dia todo.
DURACAO_MAXIMA_VIAGEM = timedelta(hours=4)

MOTIVO_USUARIO = "usuario"
MOTIVO_EXPIRADA = "expirada"

SINAL_AO_VIVO = "ao_vivo"
SINAL_SEM_SINAL = "sem_sinal"


class ErroDeViagem(Exception):
    """Base dos erros de negócio; a rota traduz cada um num status HTTP."""


class JaEmViagem(ErroDeViagem):
    """RN-15 — o usuário já tem uma viagem ativa."""


class SemVeiculoProximo(ErroDeViagem):
    """RN-16 — nenhum veículo da linha perto o bastante (Cenário 4)."""


class ParadaDesconhecida(ErroDeViagem):
    """O código de destino não existe na tabela `parada`."""


class ParadaForaDaLinha(ErroDeViagem):
    """A linha tem paradas ingeridas e o destino não é uma delas."""


class ViagemJaEncerrada(ErroDeViagem):
    """Não se muda o destino de uma viagem que já terminou."""


def agora_utc() -> datetime:
    """UTC sem fuso — o formato das colunas de data do projeto."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Embarque
# ---------------------------------------------------------------------------


def veiculo_mais_proximo(
    veiculos: list[PosicaoVeiculo], lat: float, lng: float, agora: datetime
) -> PosicaoVeiculo | None:
    """
    O veículo que confirma o embarque, ou None (RN-16).

    `agora` com fuso (as posições da SEMOB vêm com fuso).
    """
    candidatos: list[tuple[float, PosicaoVeiculo]] = []
    for veiculo in veiculos:
        idade_min = (agora - veiculo.atualizado_em).total_seconds() / 60
        if idade_min > IDADE_MAXIMA_EMBARQUE_MIN:
            continue
        distancia = distancia_metros(lat, lng, veiculo.lat, veiculo.lng)
        if distancia <= RAIO_EMBARQUE_M:
            candidatos.append((distancia, veiculo))
    if not candidatos:
        return None
    return min(candidatos, key=lambda c: c[0])[1]


def expirar_vencidas(db: Session, agora: datetime, usuario_id=None) -> int:
    """
    RN-17: encerra as viagens abertas há mais de DURACAO_MAXIMA_VIAGEM.

    `encerrada_em` recebe o instante em que a viagem venceu, não o de agora:
    é o mais próximo do que aconteceu. Roda antes de qualquer leitura de
    "viagem ativa", então ninguém enxerga uma viagem vencida.
    """
    consulta = db.query(Viagem).filter(
        Viagem.encerrada_em.is_(None),
        Viagem.embarcou_em <= agora - DURACAO_MAXIMA_VIAGEM,
    )
    if usuario_id is not None:
        consulta = consulta.filter(Viagem.usuario_id == usuario_id)

    vencidas = consulta.all()
    for viagem in vencidas:
        viagem.encerrada_em = viagem.embarcou_em + DURACAO_MAXIMA_VIAGEM
        viagem.motivo_encerramento = MOTIVO_EXPIRADA
    if vencidas:
        db.commit()
    return len(vencidas)


def viagem_ativa(db: Session, usuario_id, agora: datetime) -> Viagem | None:
    expirar_vencidas(db, agora, usuario_id)
    return (
        db.query(Viagem)
        .filter(Viagem.usuario_id == usuario_id, Viagem.encerrada_em.is_(None))
        .one_or_none()
    )


def _validar_destino(db: Session, numero_linha: str, codigo: str) -> None:
    parada = db.query(Parada).filter(Parada.codigo == codigo).one_or_none()
    if parada is None:
        raise ParadaDesconhecida(codigo)

    # Só dá para dizer "esta parada não é da linha" quando sabemos as
    # paradas da linha. Linha sem paradas ingeridas: não há como checar, e
    # recusar o embarque por isso puniria quem fez tudo certo.
    paradas_da_linha = (
        db.query(RotaParada.parada_id).filter(RotaParada.numero == numero_linha).all()
    )
    if paradas_da_linha and parada.id not in {p for (p,) in paradas_da_linha}:
        raise ParadaForaDaLinha(codigo)


def embarcar(
    db: Session,
    *,
    usuario_id,
    numero_linha: str,
    lat: float,
    lng: float,
    parada_destino_codigo: str | None,
    veiculos: list[PosicaoVeiculo],
    agora: datetime,
) -> Viagem:
    """
    Registra o embarque. `lat`/`lng` entram só na validação (RN-06).

    A ordem das checagens importa para a mensagem: primeiro "você já está
    em viagem", depois o destino, por último o veículo — o de mais custo
    (depende do feed) fica por último.
    """
    if viagem_ativa(db, usuario_id, agora) is not None:
        raise JaEmViagem()

    if parada_destino_codigo is not None:
        _validar_destino(db, numero_linha, parada_destino_codigo)

    veiculo = veiculo_mais_proximo(
        veiculos, lat, lng, agora=agora.replace(tzinfo=timezone.utc)
    )
    if veiculo is None:
        raise SemVeiculoProximo()

    viagem = Viagem(
        usuario_id=usuario_id,
        numero_linha=numero_linha,
        sentido=veiculo.sentido,
        veiculo_prefixo=veiculo.prefixo,
        parada_destino_codigo=parada_destino_codigo,
        embarcou_em=agora,
        origem_embarque="manual",
    )
    db.add(viagem)
    try:
        db.commit()
    except IntegrityError:
        # Dois toques simultâneos: o índice único parcial deixou passar só
        # o primeiro. O segundo é um "já está em viagem", não um erro 500.
        db.rollback()
        raise JaEmViagem()
    return viagem


def definir_destino(
    db: Session, *, usuario_id, viagem_id, parada_destino_codigo: str | None, agora: datetime
) -> Viagem | None:
    """
    Escolhe (ou troca, ou tira com `None`) a parada de destino da viagem em
    andamento. `None` quando a viagem não existe ou é de outra pessoa.

    Existe porque o jeito natural de escolher o destino é tocar na parada no
    mapa DEPOIS de embarcar. Vale a mesma validação do embarque.
    """
    expirar_vencidas(db, agora, usuario_id)
    viagem = (
        db.query(Viagem)
        .filter(Viagem.id == viagem_id, Viagem.usuario_id == usuario_id)
        .one_or_none()
    )
    if viagem is None:
        return None
    if viagem.encerrada_em is not None:
        raise ViagemJaEncerrada()

    if parada_destino_codigo is not None:
        _validar_destino(db, viagem.numero_linha, parada_destino_codigo)

    viagem.parada_destino_codigo = parada_destino_codigo
    db.commit()
    return viagem


def encerrar(db: Session, *, usuario_id, viagem_id, agora: datetime) -> Viagem | None:
    """
    Encerra a viagem do usuário. `None` quando ela não existe ou é de outra
    pessoa (a rota responde 404 nos dois casos, sem revelar qual).

    Idempotente: encerrar de novo devolve a viagem como está — tocar em
    "Cheguei" duas vezes, ou repetir a chamada depois de uma falha de rede,
    não pode virar erro.
    """
    viagem = (
        db.query(Viagem)
        .filter(Viagem.id == viagem_id, Viagem.usuario_id == usuario_id)
        .one_or_none()
    )
    if viagem is None:
        return None
    if viagem.encerrada_em is None:
        viagem.encerrada_em = agora
        viagem.motivo_encerramento = MOTIVO_USUARIO
        db.commit()
    return viagem


# ---------------------------------------------------------------------------
# Acompanhamento
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParadaDoTrajeto:
    codigo: str
    nome: str
    lat: float
    lng: float


@dataclass(frozen=True)
class DestinoDaViagem:
    parada: ParadaDoTrajeto
    ultrapassado: bool = False


@dataclass(frozen=True)
class Progresso:
    """
    O que o passageiro vê em viagem. Nada aqui é persistido.

    `veiculo` vem preenchido sempre que o ônibus está no feed, mesmo com
    posição velha — `sinal` diz se dá para confiar. `proxima_parada` e
    `paradas_restantes` só existem com sinal ao vivo e trajeto conhecido
    (RN-09: sem dado, a tela diz que não sabe, em vez de chutar).
    """

    sinal: str
    veiculo: PosicaoVeiculo | None = None
    destino: DestinoDaViagem | None = None
    proxima_parada: ParadaDoTrajeto | None = None
    paradas_restantes: list[ParadaDoTrajeto] = field(default_factory=list)


def _destino(db: Session, codigo: str | None) -> ParadaDoTrajeto | None:
    if not codigo:
        return None
    parada = db.query(Parada).filter(Parada.codigo == codigo).one_or_none()
    if parada is None:
        return None
    return ParadaDoTrajeto(parada.codigo, parada.nome, parada.lat, parada.lng)


def _paradas_a_frente(
    db: Session,
    rota_service: RotaService,
    numero_linha: str,
    sentidos: list[str],
    veiculo: PosicaoVeiculo,
) -> list[ParadaDoTrajeto] | None:
    """
    As paradas do trajeto que o veículo ainda não passou, na ordem em que
    ele as alcança. None quando não dá para saber (sem rota ingerida, ou
    o veículo está fora do traçado).
    """
    for sentido in sentidos:
        medido = rota_service.trajeto_medido(db, numero_linha, sentido)
        if medido is None:
            continue
        trajeto, sentido_rota = medido

        indice_veiculo = trajeto.indice_mais_proximo(
            (veiculo.lat, veiculo.lng), TOLERANCIA_TRAJETO_M
        )
        if indice_veiculo is None:
            return None

        vinculos = (
            db.query(RotaParada, Parada)
            .join(Parada, Parada.id == RotaParada.parada_id)
            .filter(
                and_(RotaParada.numero == numero_linha, RotaParada.sentido == sentido_rota)
            )
            .order_by(RotaParada.ordem)
            .all()
        )
        if not vinculos:
            return None

        # A parada até TOLERANCIA_NA_PARADA_M atrás do ônibus ainda conta
        # como "chegando" — mesma regra do ETA, para as duas telas não se
        # contradizerem.
        a_frente: list[ParadaDoTrajeto] = []
        para_tras: list[ParadaDoTrajeto] = []
        for vinculo, parada in vinculos:
            ponto = ParadaDoTrajeto(parada.codigo, parada.nome, parada.lat, parada.lng)
            metros = trajeto.metros_entre(indice_veiculo, vinculo.indice_trajeto)
            (a_frente if metros >= -TOLERANCIA_NA_PARADA_M else para_tras).append(ponto)

        # Linha circular: o que ficou para trás o ônibus alcança dando a
        # volta, então segue depois do que está à frente.
        if sentido_rota.strip().upper() == "CIRCULAR":
            return a_frente + para_tras
        return a_frente

    return None


def progresso_da_viagem(
    db: Session,
    viagem: Viagem,
    veiculos: list[PosicaoVeiculo],
    rota_service: RotaService,
    agora: datetime,
) -> Progresso:
    """`agora` com fuso, para comparar com a posição do veículo."""
    destino_parada = _destino(db, viagem.parada_destino_codigo)
    veiculo = next((v for v in veiculos if v.prefixo == viagem.veiculo_prefixo), None)

    if veiculo is None:
        return Progresso(
            sinal=SINAL_SEM_SINAL,
            destino=DestinoDaViagem(destino_parada) if destino_parada else None,
        )

    idade_min = (agora - veiculo.atualizado_em).total_seconds() / 60
    if idade_min > IDADE_MAXIMA_ETA_MIN:
        return Progresso(
            sinal=SINAL_SEM_SINAL,
            veiculo=veiculo,
            destino=DestinoDaViagem(destino_parada) if destino_parada else None,
        )

    # Vale o sentido de agora do veículo; o do embarque é o reserva. Para
    # linha circular o veículo nunca reporta "CIRCULAR" (ver eta_service),
    # então a rota circular entra sempre como última tentativa.
    sentidos = [s.strip().upper() for s in (veiculo.sentido, viagem.sentido) if s and s.strip()]
    sentidos = list(dict.fromkeys([*sentidos, "CIRCULAR"]))

    a_frente = _paradas_a_frente(db, rota_service, viagem.numero_linha, sentidos, veiculo)

    destino = None
    if destino_parada is not None:
        ultrapassado = a_frente is not None and destino_parada.codigo not in {
            p.codigo for p in a_frente
        }
        destino = DestinoDaViagem(destino_parada, ultrapassado=ultrapassado)

    if not a_frente:
        return Progresso(sinal=SINAL_AO_VIVO, veiculo=veiculo, destino=destino)

    restantes: list[ParadaDoTrajeto] = []
    if destino_parada is not None and not destino.ultrapassado:
        for parada in a_frente:
            restantes.append(parada)
            if parada.codigo == destino_parada.codigo:
                break

    return Progresso(
        sinal=SINAL_AO_VIVO,
        veiculo=veiculo,
        destino=destino,
        proxima_parada=a_frente[0],
        paradas_restantes=restantes,
    )
