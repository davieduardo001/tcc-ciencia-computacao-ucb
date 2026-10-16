# Web Push (VAPID) do alerta de proximidade — US #172, continuação.
#
# O alerta já era calculado e aparecia DENTRO do app. Isto leva o aviso até
# quem está com o celular no bolso ou a tela bloqueada, que é o ponto da US
# ("me preparar para descer sem precisar ficar olhando o mapa").
#
# Peças, nesta ordem de leitura:
#
#   ConfiguracaoVapid / configuracao_vapid_do_ambiente
#       as três variáveis de ambiente. Faltando qualquer uma, ou estando as
#       chaves inconsistentes, o push fica INDISPONÍVEL e o sistema segue
#       como antes (aviso só dentro do app). Nunca derruba o boot.
#
#   endpoint_permitido
#       a inscrição traz uma URL escolhida pelo cliente, para a qual o
#       servidor vai fazer POST. Sem filtro isso é SSRF: qualquer pessoa
#       logada faria o backend chamar um endereço interno. Só aceitamos os
#       serviços de push dos navegadores.
#
#   montar_carga
#       o que viaja no push. Sem coordenadas, sem identificador de usuário
#       ou de viagem (LGPD): só o texto que a pessoa vai ler.
#
#   registrar_inscricao / remover_inscricao
#       persistência, compartilhada pelas rotas e pelo notificador.
#
#   NotificadorWebPush
#       implementa o contrato de notificador do alerta de proximidade. Roda
#       na thread do worker, depois do commit do alerta: nunca levanta
#       exceção (um erro aqui não pode desfazer nem repetir o alerta, que já
#       está registrado) e envia em threads próprias, para um serviço de
#       push lento não atrasar o ciclo dos demais usuários.
#
# O alerta de ATRASO (#27) usa outro notificador e NÃO é tocado: herdamos de
# NotificadorNulo só para ter os métodos que esta US não usa como no-op.

from __future__ import annotations

import base64
import json
import logging
import math
import os
import re
import uuid
from collections.abc import Callable
from concurrent.futures import Executor
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid
from pywebpush import WebPushException, webpush
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mobilidade.models.inscricao_push import InscricaoPush
from mobilidade.services.servico_notificacoes import NotificadorNulo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Limites
# ---------------------------------------------------------------------------

# Quanto o serviço de push guarda a mensagem se o aparelho estiver sem
# rede. "Sua parada está chegando" entregue 10 minutos depois é pior do que
# não entregue: a pessoa já passou dela.
TTL_SEGUNDOS = 120

# Tempo máximo esperando o serviço de push responder.
TIMEOUT_SEGUNDOS = 10.0

# Aparelhos por pessoa. Passou disso, a inscrição mais antiga sai.
LIMITE_INSCRICOES_POR_USUARIO = 5

# Código HTTP com que o serviço de push diz "esta inscrição não existe mais"
# (404) ou "foi cancelada" (410). Nesses dois casos a linha é apagada; os
# demais erros são passageiros e só registram a falha.
STATUS_INSCRICAO_EXPIRADA = (404, 410)

# ---------------------------------------------------------------------------
# Configuração VAPID
# ---------------------------------------------------------------------------


def _b64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def _decodificar_b64url(texto: str) -> bytes | None:
    if not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", texto or ""):
        return None
    try:
        return base64.urlsafe_b64decode(texto.rstrip("=") + "=" * (-len(texto.rstrip("=")) % 4))
    except Exception:
        return None


def derivar_chave_publica(chave_privada: str) -> str:
    """
    Chave pública (`applicationServerKey`, base64url do ponto não comprimido)
    que corresponde à privada. Levanta ValueError se a privada não for uma
    chave VAPID válida.
    """
    vapid = Vapid.from_string(chave_privada)
    ponto = vapid.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return _b64url(ponto)


@dataclass(frozen=True)
class ConfiguracaoVapid:
    chave_publica: str = ""
    chave_privada: str = ""
    assunto: str = ""

    @property
    def disponivel(self) -> bool:
        return bool(self.chave_publica and self.chave_privada and self.assunto)

    @property
    def claims(self) -> dict:
        return {"sub": self.assunto}


@lru_cache(maxsize=8)
def _validar_configuracao(publica: str, privada: str, assunto: str) -> ConfiguracaoVapid:
    """
    Valida o trio e devolve a configuração, ou uma vazia (push indisponível).

    Em cache pelos valores: a rota que informa a chave pública é chamada a
    cada abertura da tela, e um aviso de configuração errada a cada chamada
    afogaria o log. Nenhum valor de chave vai para o log — só o NOME da
    variável.
    """
    informadas = {
        "VAPID_PUBLIC_KEY": publica,
        "VAPID_PRIVATE_KEY": privada,
        "VAPID_SUBJECT": assunto,
    }
    faltando = [nome for nome, valor in informadas.items() if not valor]
    if len(faltando) == len(informadas):
        # Estado normal de quem não ligou o push: nada a avisar.
        return ConfiguracaoVapid()
    if faltando:
        logger.warning(
            "Web Push desligado: configuração VAPID incompleta (faltando: %s).",
            ", ".join(faltando),
        )
        return ConfiguracaoVapid()

    if not (assunto.startswith("mailto:") or assunto.startswith("https://")):
        logger.warning(
            "Web Push desligado: VAPID_SUBJECT deve começar com 'mailto:' ou 'https://'."
        )
        return ConfiguracaoVapid()

    try:
        derivada = derivar_chave_publica(privada)
    except Exception:
        logger.warning("Web Push desligado: VAPID_PRIVATE_KEY não é uma chave VAPID válida.")
        return ConfiguracaoVapid()

    if derivada != publica:
        # Inscrições feitas com uma chave pública não recebem mensagens
        # assinadas por outra privada: todo envio falharia em silêncio.
        logger.error(
            "Web Push desligado: VAPID_PUBLIC_KEY não corresponde à VAPID_PRIVATE_KEY."
        )
        return ConfiguracaoVapid()

    return ConfiguracaoVapid(chave_publica=publica, chave_privada=privada, assunto=assunto)


def configuracao_vapid_do_ambiente() -> ConfiguracaoVapid:
    def ler(nome: str) -> str:
        return (os.environ.get(nome) or "").strip()

    return _validar_configuracao(
        ler("VAPID_PUBLIC_KEY"), ler("VAPID_PRIVATE_KEY"), ler("VAPID_SUBJECT")
    )


# ---------------------------------------------------------------------------
# Endpoint da inscrição (anti-SSRF)
# ---------------------------------------------------------------------------

# Serviços de push dos navegadores. Chrome, Edge, Brave, Opera e Samsung
# Internet usam o FCM; Firefox usa a Mozilla; Safari (macOS e iOS) usa a
# Apple; o Edge antigo usa o Windows (WNS). Um serviço novo exige mudar esta
# lista de propósito.
HOSTS_PUSH_PERMITIDOS = frozenset(
    {
        "fcm.googleapis.com",
        "updates.push.services.mozilla.com",
        "web.push.apple.com",
    }
)
SUFIXOS_PUSH_PERMITIDOS = (".notify.windows.com",)

# A URL inteira precisa ser ASCII "de URL" — sem espaço, barra invertida ou
# caractere de controle — para que o que validamos aqui seja exatamente o
# que o cliente HTTP vai interpretar. Só 443.
_ENDPOINT = re.compile(
    r"https://(?P<host>[a-z0-9][a-z0-9.-]*)(?::443)?"
    r"(?P<resto>/[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]*)",
    re.IGNORECASE,
)


def endpoint_permitido(endpoint: str) -> bool:
    achado = _ENDPOINT.fullmatch(endpoint or "")
    if achado is None:
        return False
    host = achado.group("host").lower()
    return host in HOSTS_PUSH_PERMITIDOS or any(
        host.endswith(sufixo) and len(host) > len(sufixo) for sufixo in SUFIXOS_PUSH_PERMITIDOS
    )


def chaves_validas(p256dh: str, auth: str) -> bool:
    """p256dh = ponto P-256 não comprimido (65 bytes, começa em 0x04); auth = 16 bytes."""
    ponto = _decodificar_b64url(p256dh)
    segredo = _decodificar_b64url(auth)
    return (
        ponto is not None
        and len(ponto) == 65
        and ponto[0] == 0x04
        and segredo is not None
        and len(segredo) == 16
    )


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------

URL_AO_CLICAR = "/mapa"
_MAX_NOME_PARADA = 80


def montar_carga(numero_linha: str, parada: str, eta_minutos: float) -> dict:
    """
    O que a pessoa vai ler. LGPD: nada de coordenada, de usuário ou de
    viagem — só linha, nome da parada (informação pública) e o tempo.
    """
    minutos = round(eta_minutos)
    tempo = "menos de 1 min" if minutos < 1 else f"{minutos} min"
    nome = (parada or "").strip()[:_MAX_NOME_PARADA]
    destino = f" · {nome}" if nome else ""
    return {
        "titulo": "Sua parada está chegando",
        "corpo": f"Linha {numero_linha}{destino}: chega em {tempo}.",
        "url": URL_AO_CLICAR,
        "tag": "proximidade",
    }


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------


def registrar_inscricao(
    db: Session, usuario_id: uuid.UUID, endpoint: str, p256dh: str, auth: str
) -> bool:
    """
    Cria ou atualiza a inscrição deste aparelho. Devolve True se foi criada.

    O endpoint é único. Se ele já pertence a outra conta (o aparelho
    mudou de mãos sem a saída da conta anterior chegar a limpar), a linha
    passa a ser desta pessoa em vez de duplicar. Acima de
    LIMITE_INSCRICOES_POR_USUARIO aparelhos, os mais antigos saem.
    """
    for _tentativa in range(2):
        existente = db.query(InscricaoPush).filter(InscricaoPush.endpoint == endpoint).first()
        criada = existente is None
        try:
            if existente is not None:
                existente.usuario_id = usuario_id
                existente.p256dh = p256dh
                existente.auth = auth
                existente.ultima_falha_em = None
            else:
                db.add(
                    InscricaoPush(
                        usuario_id=usuario_id, endpoint=endpoint, p256dh=p256dh, auth=auth
                    )
                )
            db.flush()
            _aparar_excedentes(db, usuario_id)
            db.commit()
            return criada
        except IntegrityError:
            # Dois pedidos simultâneos do mesmo aparelho: o outro criou a
            # linha primeiro. Relê e atualiza.
            db.rollback()
    raise RuntimeError("Não foi possível registrar a inscrição push.")


def _aparar_excedentes(db: Session, usuario_id: uuid.UUID) -> None:
    mais_novas = (
        db.query(InscricaoPush.id)
        .filter(InscricaoPush.usuario_id == usuario_id)
        .order_by(InscricaoPush.criado_em.desc(), InscricaoPush.id)
        .limit(LIMITE_INSCRICOES_POR_USUARIO)
        .all()
    )
    manter = [linha.id for linha in mais_novas]
    db.query(InscricaoPush).filter(
        InscricaoPush.usuario_id == usuario_id, InscricaoPush.id.notin_(manter)
    ).delete(synchronize_session=False)


def remover_inscricao(db: Session, usuario_id: uuid.UUID, endpoint: str) -> bool:
    """
    Remove a inscrição, mas só se for DESTA pessoa: quem não é dono não
    descobre se o endpoint existe nem consegue apagar a de outro. Idempotente.
    """
    apagadas = (
        db.query(InscricaoPush)
        .filter(InscricaoPush.usuario_id == usuario_id, InscricaoPush.endpoint == endpoint)
        .delete(synchronize_session=False)
    )
    db.commit()
    return apagadas > 0


# ---------------------------------------------------------------------------
# Envio
# ---------------------------------------------------------------------------

# (inscricao {"endpoint", "keys": {"p256dh", "auth"}}, carga em JSON,
#  chave privada, claims, timeout) -> None; levanta WebPushException.
Enviador = Callable[[dict, str, str, dict, float], None]


def enviar_com_pywebpush(
    inscricao: dict, carga: str, chave_privada: str, claims: dict, timeout: float
) -> None:
    webpush(
        subscription_info=inscricao,
        data=carga,
        vapid_private_key=chave_privada,
        # o pywebpush acrescenta `aud` e `exp` ao dicionário: passar cópia
        vapid_claims=dict(claims),
        timeout=timeout,
        ttl=TTL_SEGUNDOS,
        headers={"Urgency": "high"},
    )


def _status_http(erro: Exception) -> int | None:
    status = getattr(erro, "status_code", None)
    if status is None:
        status = getattr(getattr(erro, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


@dataclass(frozen=True)
class _Destino:
    id: uuid.UUID
    endpoint: str
    p256dh: str
    auth: str


class NotificadorWebPush(NotificadorNulo):
    """
    Notificador do alerta de proximidade que entrega por Web Push.

    Sem chaves VAPID válidas é um no-op. Com `executor`, cada envio roda em
    thread própria; sem ele (testes) roda na hora, na mesma thread.
    """

    def __init__(
        self,
        config: ConfiguracaoVapid,
        session_factory: Callable[[], Session],
        enviar: Enviador = enviar_com_pywebpush,
        executor: Executor | None = None,
        timeout: float = TIMEOUT_SEGUNDOS,
    ) -> None:
        self.config = config
        self._session_factory = session_factory
        self._enviar = enviar
        self._executor = executor
        self._timeout = timeout

    def alerta_proximidade(
        self,
        usuario_id: str,
        numero_linha: str,
        parada_destino: str,
        eta_minutos: float,
    ) -> None:
        if not self.config.disponivel:
            return
        try:
            carga = json.dumps(
                montar_carga(numero_linha, parada_destino, eta_minutos), ensure_ascii=False
            )
            destinos = self._destinos_do_usuario(uuid.UUID(str(usuario_id)))
            for destino in destinos:
                if self._executor is not None:
                    self._executor.submit(self._enviar_para, destino, carga)
                else:
                    self._enviar_para(destino, carga)
        except Exception:
            # O alerta já foi registrado (o serviço notifica DEPOIS do
            # commit). Se levantássemos, ele cairia no tratamento de erro
            # do ciclo e seria contado como falha, sem desfazer nada.
            logger.warning("Falha ao despachar o Web Push do alerta de proximidade", exc_info=True)

    # ------------------------------------------------------------------

    def _destinos_do_usuario(self, usuario_id: uuid.UUID) -> list[_Destino]:
        db = self._session_factory()
        try:
            linhas = db.query(InscricaoPush).filter(InscricaoPush.usuario_id == usuario_id).all()
            return [_Destino(i.id, i.endpoint, i.p256dh, i.auth) for i in linhas]
        finally:
            db.close()

    def _enviar_para(self, destino: _Destino, carga: str) -> None:
        inscricao = {"endpoint": destino.endpoint, "keys": {"p256dh": destino.p256dh, "auth": destino.auth}}
        try:
            self._enviar(inscricao, carga, self.config.chave_privada, self.config.claims, self._timeout)
        except WebPushException as erro:
            status = _status_http(erro)
            if status in STATUS_INSCRICAO_EXPIRADA:
                self._apagar(destino.id)
                logger.info("Inscrição push expirada, removida | inscricao=%s | status=%s", destino.id, status)
            else:
                self._registrar_falha(destino.id)
                logger.warning("Falha ao enviar Web Push | inscricao=%s | status=%s", destino.id, status)
        except Exception:
            # Rede fora, timeout, chave malformada: o aparelho continua
            # inscrito, mas a falha fica anotada. exc_info omitido de
            # propósito: a mensagem do erro pode conter a URL do endpoint.
            self._registrar_falha(destino.id)
            logger.warning("Falha ao enviar Web Push | inscricao=%s | erro=inesperado", destino.id)

    def _apagar(self, inscricao_id: uuid.UUID) -> None:
        db = self._session_factory()
        try:
            db.query(InscricaoPush).filter(InscricaoPush.id == inscricao_id).delete(
                synchronize_session=False
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.warning("Falha ao remover inscrição push | inscricao=%s", inscricao_id)
        finally:
            db.close()

    def _registrar_falha(self, inscricao_id: uuid.UUID) -> None:
        db = self._session_factory()
        try:
            db.query(InscricaoPush).filter(InscricaoPush.id == inscricao_id).update(
                {"ultima_falha_em": datetime.utcnow()}, synchronize_session=False
            )
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
