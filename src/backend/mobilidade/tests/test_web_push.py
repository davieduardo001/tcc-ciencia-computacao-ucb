"""
US #172 (continuação) — Web Push (VAPID) do alerta de proximidade.

Nada aqui fala com a rede: o envio é um dublê injetado, e o único código do
pywebpush exercitado de verdade é a exceção `WebPushException`, que o
notificador precisa interpretar (404/410 = inscrição expirada).

As chaves VAPID e as chaves de inscrição são geradas na hora, em memória.
Nenhuma chave real é usada nem gravada.
"""

import base64
import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from pywebpush import WebPushException

from mobilidade import web_push
from mobilidade.main import app
from mobilidade.models.alerta_proximidade import AlertaProximidade
from mobilidade.models.inscricao_push import InscricaoPush
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.providers.contratos_proximidade import (
    PreferenciasDeNotificacao,
    ViagemAtiva,
)
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.services.servico_proximidade import (
    EVENTO_DISPARADO,
    EVENTO_JA_DISPARADO,
    EVENTO_PREFERENCIAS,
    EVENTO_SEM_POSICAO,
    ServicoProximidade,
)
from mobilidade.workers.monitoramento import (
    criar_worker,
    intervalo_proximidade_do_ambiente,
)
from shared.database import SessionLocal

client = TestClient(app)

USUARIO = uuid.UUID("00000000-0000-4000-8000-00000000a172")
OUTRO = uuid.UUID("00000000-0000-4000-8000-00000000a173")
USUARIOS = [USUARIO, OUTRO]


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def _ponto(chave) -> bytes:
    return chave.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )


def _par_vapid() -> tuple[str, str]:
    chave = ec.generate_private_key(ec.SECP256R1())
    privada = _b64(chave.private_numbers().private_value.to_bytes(32, "big"))
    return _b64(_ponto(chave)), privada


def _chaves_inscricao() -> dict:
    """Chaves como o navegador as gera: P-256 não comprimida e 16 bytes."""
    return {
        "p256dh": _b64(_ponto(ec.generate_private_key(ec.SECP256R1()))),
        "auth": _b64(os.urandom(16)),
    }


def _endpoint() -> str:
    return f"https://fcm.googleapis.com/fcm/send/{uuid.uuid4().hex}"


def _corpo(endpoint=None, chaves=None) -> dict:
    return {"endpoint": endpoint or _endpoint(), "keys": chaves or _chaves_inscricao()}


def _h(usuario=USUARIO) -> dict:
    return {"X-User-Id": str(usuario)}


PUBLICA, PRIVADA = _par_vapid()
ASSUNTO = "mailto:movecity@example.com"


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------


def _limpar(sessao) -> None:
    sessao.rollback()
    sessao.query(InscricaoPush).filter(InscricaoPush.usuario_id.in_(USUARIOS)).delete(
        synchronize_session=False
    )
    sessao.query(AlertaProximidade).filter(AlertaProximidade.usuario_id.in_(USUARIOS)).delete(
        synchronize_session=False
    )
    sessao.commit()


@pytest.fixture
def db():
    sessao = SessionLocal()
    _limpar(sessao)
    yield sessao
    _limpar(sessao)
    sessao.close()


@pytest.fixture(autouse=True)
def _cache_da_configuracao():
    web_push._validar_configuracao.cache_clear()
    yield
    web_push._validar_configuracao.cache_clear()


@pytest.fixture
def com_vapid(monkeypatch):
    monkeypatch.setenv("VAPID_PUBLIC_KEY", PUBLICA)
    monkeypatch.setenv("VAPID_PRIVATE_KEY", PRIVADA)
    monkeypatch.setenv("VAPID_SUBJECT", ASSUNTO)


@pytest.fixture
def sem_vapid(monkeypatch):
    for nome in ("VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY", "VAPID_SUBJECT"):
        monkeypatch.delenv(nome, raising=False)


def _config() -> web_push.ConfiguracaoVapid:
    return web_push.ConfiguracaoVapid(PUBLICA, PRIVADA, ASSUNTO)


# --------------------------------------------------------------------------
# configuração VAPID
# --------------------------------------------------------------------------


def test_sem_variaveis_o_push_fica_indisponivel_sem_barulho(sem_vapid, caplog):
    with caplog.at_level(logging.DEBUG, logger="mobilidade.web_push"):
        config = web_push.configuracao_vapid_do_ambiente()

    assert config.disponivel is False
    assert caplog.records == []  # é o estado normal de quem não ligou o push


def test_com_as_tres_variaveis_corretas_o_push_fica_disponivel(com_vapid):
    config = web_push.configuracao_vapid_do_ambiente()

    assert config.disponivel is True
    assert config.chave_publica == PUBLICA
    assert config.claims == {"sub": ASSUNTO}


@pytest.mark.parametrize("faltando", ["VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY", "VAPID_SUBJECT"])
def test_configuracao_incompleta_desliga_o_push_e_cita_so_o_nome_da_variavel(
    com_vapid, monkeypatch, caplog, faltando
):
    monkeypatch.delenv(faltando)

    with caplog.at_level(logging.WARNING, logger="mobilidade.web_push"):
        config = web_push.configuracao_vapid_do_ambiente()

    assert config.disponivel is False
    assert faltando in caplog.text
    assert PRIVADA not in caplog.text and PUBLICA not in caplog.text


def test_assunto_sem_mailto_ou_https_desliga_o_push(com_vapid, monkeypatch):
    monkeypatch.setenv("VAPID_SUBJECT", "movecity@example.com")

    assert web_push.configuracao_vapid_do_ambiente().disponivel is False


def test_chave_privada_invalida_desliga_o_push_sem_derrubar(com_vapid, monkeypatch, caplog):
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "isto-nao-e-uma-chave")

    with caplog.at_level(logging.WARNING, logger="mobilidade.web_push"):
        config = web_push.configuracao_vapid_do_ambiente()

    assert config.disponivel is False
    assert "isto-nao-e-uma-chave" not in caplog.text


def test_chave_publica_que_nao_e_do_par_desliga_o_push(com_vapid, monkeypatch, caplog):
    outra_publica, _ = _par_vapid()
    monkeypatch.setenv("VAPID_PUBLIC_KEY", outra_publica)

    with caplog.at_level(logging.ERROR, logger="mobilidade.web_push"):
        config = web_push.configuracao_vapid_do_ambiente()

    assert config.disponivel is False
    assert "não corresponde" in caplog.text


def test_configuracao_errada_avisa_uma_vez_so(com_vapid, monkeypatch, caplog):
    monkeypatch.delenv("VAPID_SUBJECT")

    with caplog.at_level(logging.WARNING, logger="mobilidade.web_push"):
        for _ in range(5):
            web_push.configuracao_vapid_do_ambiente()

    assert len(caplog.records) == 1


# --------------------------------------------------------------------------
# endpoint da inscrição (anti-SSRF)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://fcm.googleapis.com/fcm/send/abc123",
        "https://fcm.googleapis.com/wp/abc123",
        "https://updates.push.services.mozilla.com/wpush/v2/abc123",
        "https://web.push.apple.com/QGxyz-123",
        "https://wns2-par02p.notify.windows.com/w/?token=abc123",
        "https://FCM.GoogleAPIs.com/fcm/send/abc123",
        "https://fcm.googleapis.com:443/fcm/send/abc123",
    ],
)
def test_aceita_os_servicos_de_push_dos_navegadores(endpoint):
    assert web_push.endpoint_permitido(endpoint) is True


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        "http://fcm.googleapis.com/fcm/send/abc",  # sem TLS
        "https://localhost/x",
        "https://127.0.0.1/x",
        "https://169.254.169.254/latest/meta-data/",  # metadados de nuvem
        "https://10.0.0.5/x",
        "https://[::1]/x",
        "https://example.com/x",
        "https://fcm.googleapis.com.evil.com/x",  # prefixo enganoso
        "https://evil.com/fcm.googleapis.com",
        "https://fcm.googleapis.com@evil.com/x",  # credenciais na URL
        "https://evil.com\\@fcm.googleapis.com/x",  # barra invertida
        "https://fcm.googleapis.com:8443/x",  # porta diferente de 443
        "https://fcm.googleapis.com./x",  # FQDN com ponto final
        "https://fcm.googleapis.com",  # sem caminho
        "https://notify.windows.com/x",  # só os subdomínios
        "https://evilnotify.windows.com/x",
        "https://fcm.googleapis.com/x y",  # espaço
        "https://fcm.googleapis.com/x\nHost: evil.com",  # quebra de linha
        "ftp://fcm.googleapis.com/x",
        "//fcm.googleapis.com/x",
    ],
)
def test_recusa_qualquer_outro_destino(endpoint):
    assert web_push.endpoint_permitido(endpoint) is False


def test_chaves_da_inscricao_precisam_ter_o_formato_do_navegador():
    chaves = _chaves_inscricao()
    assert web_push.chaves_validas(chaves["p256dh"], chaves["auth"]) is True

    assert web_push.chaves_validas("", chaves["auth"]) is False
    assert web_push.chaves_validas(chaves["p256dh"], "") is False
    assert web_push.chaves_validas("aaaa", chaves["auth"]) is False  # curta
    assert web_push.chaves_validas(chaves["p256dh"], _b64(b"curta")) is False
    assert web_push.chaves_validas("não é base64!", chaves["auth"]) is False
    # 65 bytes, mas sem o prefixo 0x04 do ponto não comprimido
    assert web_push.chaves_validas(_b64(b"\x02" + b"\x00" * 64), chaves["auth"]) is False


# --------------------------------------------------------------------------
# carga (LGPD)
# --------------------------------------------------------------------------


def test_carga_tem_so_o_texto_que_a_pessoa_le():
    carga = web_push.montar_carga("0.110", "W3 Sul 502", 3.4)

    assert set(carga) == {"titulo", "corpo", "url", "tag"}
    assert carga["titulo"] == "Sua parada está chegando"
    assert carga["corpo"] == "Linha 0.110 · W3 Sul 502: chega em 3 min."
    assert carga["url"] == "/mapa"


def test_carga_nao_carrega_coordenada_nem_identificador():
    texto = json.dumps(web_push.montar_carga("0.110", "W3 Sul 502", 3.4))

    for proibido in ("lat", "lng", "usuario", "viagem", "prefixo"):
        assert proibido not in texto.lower()


def test_carga_com_menos_de_um_minuto_nao_diz_zero():
    assert "menos de 1 min" in web_push.montar_carga("0.110", "W3 Sul 502", 0.3)["corpo"]


def test_carga_limita_o_nome_da_parada():
    carga = web_push.montar_carga("0.110", "X" * 500, 2)

    assert len(carga["corpo"]) < 130


def test_carga_sem_nome_de_parada_continua_legivel():
    assert web_push.montar_carga("0.110", "", 2)["corpo"] == "Linha 0.110: chega em 2 min."


# --------------------------------------------------------------------------
# rotas
# --------------------------------------------------------------------------


def test_rotas_exigem_identidade():
    assert client.get("/mobilidade/push/chave").status_code == 401
    assert client.put("/mobilidade/push/inscricao", json=_corpo()).status_code == 401
    assert (
        client.request("DELETE", "/mobilidade/push/inscricao", json={"endpoint": _endpoint()}).status_code
        == 401
    )


def test_chave_publica_indisponivel_sem_configuracao(sem_vapid):
    r = client.get("/mobilidade/push/chave", headers=_h())

    assert r.status_code == 200
    assert r.json() == {"disponivel": False, "chave_publica": None}


def test_chave_publica_disponivel_com_configuracao(com_vapid):
    r = client.get("/mobilidade/push/chave", headers=_h())

    assert r.status_code == 200
    assert r.json() == {"disponivel": True, "chave_publica": PUBLICA}
    assert PRIVADA not in r.text


def test_chave_publica_nunca_expoe_a_privada(com_vapid):
    r = client.get("/mobilidade/push/chave", headers=_h())

    assert "privada" not in r.text.lower()


def test_registrar_sem_vapid_responde_503_e_nao_grava(sem_vapid, db):
    r = client.put("/mobilidade/push/inscricao", json=_corpo(), headers=_h())

    assert r.status_code == 503
    assert db.query(InscricaoPush).count() == 0


def test_registrar_grava_a_inscricao_do_usuario_da_sessao(com_vapid, db):
    corpo = _corpo()

    r = client.put("/mobilidade/push/inscricao", json=corpo, headers=_h())

    assert r.status_code == 200
    assert r.json() == {"ativa": True}
    linha = db.query(InscricaoPush).filter(InscricaoPush.endpoint == corpo["endpoint"]).one()
    assert linha.usuario_id == USUARIO
    assert linha.p256dh == corpo["keys"]["p256dh"]
    assert linha.auth == corpo["keys"]["auth"]


def test_o_dono_vem_da_sessao_e_nunca_do_corpo(com_vapid, db):
    corpo = _corpo() | {"usuario_id": str(OUTRO), "usuarioId": str(OUTRO)}

    client.put("/mobilidade/push/inscricao", json=corpo, headers=_h(USUARIO))

    linha = db.query(InscricaoPush).filter(InscricaoPush.endpoint == corpo["endpoint"]).one()
    assert linha.usuario_id == USUARIO


def test_aceita_o_json_do_navegador_com_campos_a_mais(com_vapid, db):
    # PushSubscription.toJSON() inclui expirationTime
    corpo = _corpo() | {"expirationTime": None}

    r = client.put("/mobilidade/push/inscricao", json=corpo, headers=_h())

    assert r.status_code == 200


def test_registrar_duas_vezes_o_mesmo_aparelho_nao_duplica(com_vapid, db):
    corpo = _corpo()

    client.put("/mobilidade/push/inscricao", json=corpo, headers=_h())
    r = client.put("/mobilidade/push/inscricao", json=corpo, headers=_h())

    assert r.status_code == 200
    assert db.query(InscricaoPush).filter(InscricaoPush.usuario_id == USUARIO).count() == 1


def test_o_aparelho_que_muda_de_conta_muda_de_dono_sem_duplicar(com_vapid, db):
    endpoint = _endpoint()
    client.put("/mobilidade/push/inscricao", json=_corpo(endpoint), headers=_h(USUARIO))

    client.put("/mobilidade/push/inscricao", json=_corpo(endpoint), headers=_h(OUTRO))

    linhas = db.query(InscricaoPush).filter(InscricaoPush.endpoint == endpoint).all()
    assert len(linhas) == 1
    assert linhas[0].usuario_id == OUTRO


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.com/push/abc",
        "http://fcm.googleapis.com/fcm/send/abc",
        "https://169.254.169.254/latest/meta-data/",
        "https://fcm.googleapis.com.evil.com/x",
    ],
)
def test_registrar_recusa_endpoint_fora_dos_servicos_de_push(com_vapid, db, endpoint):
    r = client.put("/mobilidade/push/inscricao", json=_corpo(endpoint), headers=_h())

    assert r.status_code == 422
    assert "não aceita" in r.json()["detail"]
    assert db.query(InscricaoPush).count() == 0


def test_registrar_recusa_chaves_invalidas(com_vapid, db):
    chaves = {"p256dh": "aaaa", "auth": "bbbb"}

    r = client.put("/mobilidade/push/inscricao", json=_corpo(chaves=chaves), headers=_h())

    assert r.status_code == 422
    assert db.query(InscricaoPush).count() == 0


@pytest.mark.parametrize("corpo", [{}, {"endpoint": _endpoint()}, {"keys": {}}, {"endpoint": "", "keys": {}}])
def test_registrar_recusa_corpo_incompleto(com_vapid, corpo):
    assert client.put("/mobilidade/push/inscricao", json=corpo, headers=_h()).status_code == 422


def test_limite_de_aparelhos_por_usuario_apaga_os_mais_antigos(com_vapid, db):
    endpoints = [_endpoint() for _ in range(web_push.LIMITE_INSCRICOES_POR_USUARIO + 2)]
    for endpoint in endpoints:
        assert client.put("/mobilidade/push/inscricao", json=_corpo(endpoint), headers=_h()).status_code == 200

    restantes = {
        i.endpoint for i in db.query(InscricaoPush).filter(InscricaoPush.usuario_id == USUARIO).all()
    }
    assert restantes == set(endpoints[2:])


def test_o_limite_de_um_usuario_nao_apaga_o_aparelho_de_outro(com_vapid, db):
    do_outro = _endpoint()
    client.put("/mobilidade/push/inscricao", json=_corpo(do_outro), headers=_h(OUTRO))

    for _ in range(web_push.LIMITE_INSCRICOES_POR_USUARIO + 2):
        client.put("/mobilidade/push/inscricao", json=_corpo(), headers=_h(USUARIO))

    assert db.query(InscricaoPush).filter(InscricaoPush.endpoint == do_outro).count() == 1


def test_remover_apaga_a_inscricao_do_proprio_usuario(com_vapid, db):
    corpo = _corpo()
    client.put("/mobilidade/push/inscricao", json=corpo, headers=_h())

    r = client.request("DELETE", "/mobilidade/push/inscricao", json={"endpoint": corpo["endpoint"]}, headers=_h())

    assert r.status_code == 204
    assert db.query(InscricaoPush).count() == 0


def test_remover_funciona_mesmo_sem_vapid_configurado(sem_vapid, db):
    # Desligar o push no servidor não pode impedir quem quer sair.
    endpoint = _endpoint()
    db.add(InscricaoPush(usuario_id=USUARIO, endpoint=endpoint, **_chaves_inscricao()))
    db.commit()

    r = client.request("DELETE", "/mobilidade/push/inscricao", json={"endpoint": endpoint}, headers=_h())

    assert r.status_code == 204
    assert db.query(InscricaoPush).count() == 0


def test_remover_e_idempotente(com_vapid, db):
    r1 = client.request("DELETE", "/mobilidade/push/inscricao", json={"endpoint": _endpoint()}, headers=_h())
    r2 = client.request("DELETE", "/mobilidade/push/inscricao", json={"endpoint": _endpoint()}, headers=_h())

    assert r1.status_code == r2.status_code == 204


def test_remover_nao_apaga_nem_revela_a_inscricao_de_outro_usuario(com_vapid, db):
    corpo = _corpo()
    client.put("/mobilidade/push/inscricao", json=corpo, headers=_h(OUTRO))

    r = client.request("DELETE", "/mobilidade/push/inscricao", json={"endpoint": corpo["endpoint"]}, headers=_h(USUARIO))

    assert r.status_code == 204  # mesma resposta de "não existia"
    assert db.query(InscricaoPush).filter(InscricaoPush.endpoint == corpo["endpoint"]).count() == 1


# --------------------------------------------------------------------------
# notificador
# --------------------------------------------------------------------------


class _Envios:
    """Dublê do `enviar`: guarda o que seria mandado e pode falhar sob demanda."""

    def __init__(self, falhas=None):
        self.chamadas: list[dict] = []
        self.falhas = falhas or {}  # endpoint -> exceção

    def __call__(self, inscricao, carga, chave_privada, claims, timeout):
        self.chamadas.append(
            {
                "inscricao": inscricao,
                "carga": json.loads(carga),
                "chave_privada": chave_privada,
                "claims": claims,
                "timeout": timeout,
            }
        )
        erro = self.falhas.get(inscricao["endpoint"])
        if erro is not None:
            raise erro


def _inscrever(db, usuario=USUARIO, endpoint=None) -> InscricaoPush:
    linha = InscricaoPush(usuario_id=usuario, endpoint=endpoint or _endpoint(), **_chaves_inscricao())
    db.add(linha)
    db.commit()
    return linha


def _notificador(envios, **kwargs) -> web_push.NotificadorWebPush:
    return web_push.NotificadorWebPush(_config(), SessionLocal, enviar=envios, **kwargs)


def _erro_http(status: int) -> WebPushException:
    return WebPushException("falhou", response=SimpleNamespace(status_code=status))


def _restantes(db, usuario=USUARIO) -> set[str]:
    db.expire_all()
    return {i.endpoint for i in db.query(InscricaoPush).filter(InscricaoPush.usuario_id == usuario).all()}


def test_notificador_sem_configuracao_vapid_nao_faz_nada(db):
    _inscrever(db)
    envios = _Envios()
    notificador = web_push.NotificadorWebPush(
        web_push.ConfiguracaoVapid(), SessionLocal, enviar=envios
    )

    notificador.alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert envios.chamadas == []


def test_notificador_envia_para_cada_aparelho_do_usuario(db):
    a, b = _inscrever(db), _inscrever(db)
    envios = _Envios()

    _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert {c["inscricao"]["endpoint"] for c in envios.chamadas} == {a.endpoint, b.endpoint}
    primeira = envios.chamadas[0]
    assert primeira["chave_privada"] == PRIVADA
    assert primeira["claims"] == {"sub": ASSUNTO}
    assert primeira["timeout"] == web_push.TIMEOUT_SEGUNDOS
    assert set(primeira["inscricao"]["keys"]) == {"p256dh", "auth"}


def test_notificador_nao_envia_para_aparelhos_de_outro_usuario(db):
    _inscrever(db, OUTRO)
    envios = _Envios()

    _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert envios.chamadas == []


def test_notificador_manda_a_carga_sem_dados_pessoais(db):
    _inscrever(db)
    envios = _Envios()

    _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    carga = envios.chamadas[0]["carga"]
    assert set(carga) == {"titulo", "corpo", "url", "tag"}
    assert str(USUARIO) not in json.dumps(carga)


@pytest.mark.parametrize("status", [404, 410])
def test_inscricao_expirada_no_servico_de_push_e_removida(db, status):
    expirada, viva = _inscrever(db), _inscrever(db)
    envios = _Envios(falhas={expirada.endpoint: _erro_http(status)})

    _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert _restantes(db) == {viva.endpoint}


@pytest.mark.parametrize("status", [400, 401, 403, 413, 429, 500, 502, 503])
def test_outros_erros_mantem_a_inscricao_e_anotam_a_falha(db, status):
    linha = _inscrever(db)
    envios = _Envios(falhas={linha.endpoint: _erro_http(status)})

    _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert _restantes(db) == {linha.endpoint}
    db.expire_all()
    assert db.query(InscricaoPush).one().ultima_falha_em is not None


def test_falha_de_rede_mantem_a_inscricao_e_nao_levanta(db):
    linha = _inscrever(db)
    envios = _Envios(falhas={linha.endpoint: ConnectionError("rede fora")})

    _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert _restantes(db) == {linha.endpoint}


def test_uma_falha_nao_impede_o_envio_aos_outros_aparelhos(db):
    ruim, bom = _inscrever(db), _inscrever(db)
    envios = _Envios(falhas={ruim.endpoint: ConnectionError("rede fora")})

    _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert {c["inscricao"]["endpoint"] for c in envios.chamadas} == {ruim.endpoint, bom.endpoint}


def test_notificador_nunca_levanta_nem_se_o_banco_falhar():
    def sessao_quebrada():
        raise RuntimeError("banco fora do ar")

    notificador = web_push.NotificadorWebPush(_config(), sessao_quebrada, enviar=_Envios())

    notificador.alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)  # não levanta


def test_notificador_nunca_levanta_com_usuario_invalido(db):
    _notificador(_Envios()).alerta_proximidade("isto-nao-e-uuid", "0.110", "W3 Sul 502", 3.0)


def test_logs_nunca_trazem_endpoint_nem_chaves(db, caplog):
    expirada, instavel = _inscrever(db), _inscrever(db)
    envios = _Envios(
        falhas={
            expirada.endpoint: _erro_http(410),
            # a mensagem de erro de bibliotecas HTTP costuma conter a URL
            instavel.endpoint: ConnectionError(f"falha ao conectar em {instavel.endpoint}"),
        }
    )

    with caplog.at_level(logging.DEBUG, logger="mobilidade.web_push"):
        _notificador(envios).alerta_proximidade(str(USUARIO), "0.110", "W3 Sul 502", 3.0)

    assert caplog.records, "esperava ao menos um registro de log"
    for linha in (expirada, instavel):
        assert linha.endpoint not in caplog.text
        assert linha.p256dh not in caplog.text
        assert linha.auth not in caplog.text
    assert PRIVADA not in caplog.text


def test_com_executor_o_envio_acontece_em_outra_thread(db):
    _inscrever(db)
    envios = _Envios()
    with ThreadPoolExecutor(max_workers=2) as executor:
        _notificador(envios, executor=executor).alerta_proximidade(
            str(USUARIO), "0.110", "W3 Sul 502", 3.0
        )
    # sair do `with` espera as threads terminarem

    assert len(envios.chamadas) == 1


def test_enviar_com_pywebpush_usa_ttl_curto_urgencia_alta_e_nao_altera_os_claims(monkeypatch):
    capturado = {}

    def falso(**kwargs):
        capturado.update(kwargs)
        kwargs["vapid_claims"]["aud"] = "https://fcm.googleapis.com"  # o que o pywebpush faz

    monkeypatch.setattr(web_push, "webpush", falso)
    claims = {"sub": ASSUNTO}

    web_push.enviar_com_pywebpush({"endpoint": "e", "keys": {}}, "{}", PRIVADA, claims, 7.0)

    assert capturado["ttl"] == web_push.TTL_SEGUNDOS <= 300
    assert capturado["headers"] == {"Urgency": "high"}
    assert capturado["timeout"] == 7.0
    assert capturado["vapid_private_key"] == PRIVADA
    assert claims == {"sub": ASSUNTO}  # a cópia é que foi alterada


def test_o_alerta_de_atraso_continua_sem_efeito_neste_notificador(db):
    _inscrever(db)
    envios = _Envios()
    notificador = _notificador(envios)

    notificador.alerta_disparado(str(USUARIO), "0.110", 5.0)
    notificador.alerta_atualizado(str(USUARIO), "0.110", 5.0)
    notificador.alerta_cancelado(str(USUARIO), "0.110")

    assert envios.chamadas == []


# --------------------------------------------------------------------------
# integração com o ServicoProximidade real
# --------------------------------------------------------------------------

LAT_PARADA, LNG_PARADA = -15.83, -48.05


class _Viagens:
    def __init__(self, *viagens):
        self._viagens = list(viagens)

    def listar_ativas(self):
        return list(self._viagens)


class _Veiculos:
    def __init__(self, mapa):
        self._mapa = mapa

    def obter_das_linhas(self, numeros):
        return {n: self._mapa.get(n, []) for n in numeros}


class _Preferencias:
    def __init__(self, **kwargs):
        self._pref = PreferenciasDeNotificacao(**kwargs)

    def obter(self, usuario_id, db):
        return self._pref


class _Eta:
    def __init__(self, valor):
        self._valor = valor

    def eta_minutos(self, viagem, veiculo, agora, db):
        return self._valor


def _viagem(usuario=USUARIO) -> ViagemAtiva:
    return ViagemAtiva(
        viagem_id=str(uuid.uuid4()),
        usuario_id=usuario,
        numero_linha="0.110",
        parada_destino_codigo="PR-A172",
        parada_destino_lat=LAT_PARADA,
        parada_destino_lng=LNG_PARADA,
        parada_destino_nome="Terminal Central",
        veiculo_prefixo="TESTE01",
    )


def _veiculo() -> PosicaoVeiculo:
    return PosicaoVeiculo(
        prefixo="TESTE01",
        lat=LAT_PARADA - 0.02,
        lng=LNG_PARADA,
        sentido=None,
        velocidade=40.0,
        direcao=None,
        atualizado_em=datetime.now(timezone.utc),
        operadora="Operadora Teste",
    )


def _servico(envios, viagem, preferencias, veiculos=None, eta=3.0) -> ServicoProximidade:
    return ServicoProximidade(
        viagens=_Viagens(viagem),
        veiculos=_Veiculos({"0.110": [_veiculo()]} if veiculos is None else veiculos),
        preferencias=preferencias,
        notificador=_notificador(envios),
        eta=_Eta(eta),
    )


def test_alerta_dispara_o_push_para_os_aparelhos_do_passageiro(db):
    _inscrever(db)
    envios = _Envios()
    servico = _servico(envios, _viagem(), _Preferencias(antecedencia_minutos=10))

    assert servico.verificar_proximidades(db) == [EVENTO_DISPARADO]

    assert len(envios.chamadas) == 1
    assert "Terminal Central" in envios.chamadas[0]["carga"]["corpo"]


def test_preferencias_desativadas_nao_geram_push(db):
    _inscrever(db)
    envios = _Envios()

    for preferencias in (
        _Preferencias(notificacoes_ativas=False),
        _Preferencias(alerta_chegada=False),
    ):
        servico = _servico(envios, _viagem(), preferencias)
        assert servico.verificar_proximidades(db) == [EVENTO_PREFERENCIAS]

    assert envios.chamadas == []


def test_o_mesmo_alerta_nao_gera_dois_pushes(db):
    _inscrever(db)
    envios = _Envios()
    servico = _servico(envios, _viagem(), _Preferencias(antecedencia_minutos=10))

    primeiro = servico.verificar_proximidades(db)
    segundo = servico.verificar_proximidades(db)

    assert primeiro == [EVENTO_DISPARADO]
    assert segundo == [EVENTO_JA_DISPARADO]
    assert len(envios.chamadas) == 1


def test_sem_posicao_do_onibus_da_viagem_nao_ha_push(db):
    _inscrever(db)
    envios = _Envios()
    servico = _servico(envios, _viagem(), _Preferencias(), veiculos={"0.110": []})

    assert servico.verificar_proximidades(db) == [EVENTO_SEM_POSICAO]
    assert envios.chamadas == []


def test_passageiro_sem_aparelho_inscrito_continua_com_o_aviso_no_app(db):
    envios = _Envios()
    servico = _servico(envios, _viagem(), _Preferencias(antecedencia_minutos=10))

    assert servico.verificar_proximidades(db) == [EVENTO_DISPARADO]

    assert envios.chamadas == []
    assert db.query(AlertaProximidade).filter(AlertaProximidade.usuario_id == USUARIO).count() == 1


def test_falha_no_push_nao_desfaz_o_alerta_registrado(db):
    linha = _inscrever(db)
    envios = _Envios(falhas={linha.endpoint: ConnectionError("rede fora")})
    servico = _servico(envios, _viagem(), _Preferencias(antecedencia_minutos=10))

    assert servico.verificar_proximidades(db) == [EVENTO_DISPARADO]

    assert db.query(AlertaProximidade).filter(AlertaProximidade.usuario_id == USUARIO).count() == 1


# --------------------------------------------------------------------------
# intervalo do worker
# --------------------------------------------------------------------------


@pytest.mark.parametrize("valor", [None, "", "  ", "abc", "-5", "0", "19", "1.5"])
def test_intervalo_do_ambiente_invalido_ou_ausente_mantem_o_padrao(monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("WORKER_PROXIMIDADE_INTERVAL_SECONDS", raising=False)
    else:
        monkeypatch.setenv("WORKER_PROXIMIDADE_INTERVAL_SECONDS", valor)

    assert intervalo_proximidade_do_ambiente() is None


@pytest.mark.parametrize("valor,esperado", [("20", 20), ("60", 60), (" 90 ", 90)])
def test_intervalo_do_ambiente_valido(monkeypatch, valor, esperado):
    monkeypatch.setenv("WORKER_PROXIMIDADE_INTERVAL_SECONDS", valor)

    assert intervalo_proximidade_do_ambiente() == esperado


def _intervalo_do_job(scheduler, job_id):
    return scheduler.get_job(job_id).trigger.interval.total_seconds()


def test_worker_mantem_o_intervalo_geral_por_padrao():
    scheduler = criar_worker(MagicMock(), intervalo_minutos=5, servico_proximidade=MagicMock())

    assert _intervalo_do_job(scheduler, "monitoramento-proximidade") == 300
    assert _intervalo_do_job(scheduler, "monitoramento-atrasos") == 300


def test_worker_aceita_ciclo_mais_curto_so_para_a_proximidade():
    scheduler = criar_worker(
        MagicMock(),
        intervalo_minutos=5,
        servico_proximidade=MagicMock(),
        intervalo_proximidade_segundos=60,
    )

    assert _intervalo_do_job(scheduler, "monitoramento-proximidade") == 60
    assert _intervalo_do_job(scheduler, "monitoramento-atrasos") == 300  # #27 intocado


# --------------------------------------------------------------------------
# ligação no main.py
# --------------------------------------------------------------------------


def test_main_usa_o_notificador_nulo_sem_vapid(sem_vapid):
    from mobilidade import main as principal

    fake_app = SimpleNamespace(state=SimpleNamespace())

    notificador = principal._notificador_de_proximidade(fake_app)

    assert isinstance(notificador, NotificadorNulo)
    assert not isinstance(notificador, web_push.NotificadorWebPush)
    assert not hasattr(fake_app.state, "executor_push")


def test_main_usa_web_push_quando_o_vapid_esta_configurado(com_vapid):
    from mobilidade import main as principal

    fake_app = SimpleNamespace(state=SimpleNamespace())

    notificador = principal._notificador_de_proximidade(fake_app)
    try:
        assert isinstance(notificador, web_push.NotificadorWebPush)
        assert notificador.config.disponivel
        assert fake_app.state.executor_push is not None
    finally:
        fake_app.state.executor_push.shutdown(wait=False)


def test_main_com_vapid_incoerente_volta_ao_notificador_nulo(com_vapid, monkeypatch):
    from mobilidade import main as principal

    outra_publica, _ = _par_vapid()
    monkeypatch.setenv("VAPID_PUBLIC_KEY", outra_publica)
    fake_app = SimpleNamespace(state=SimpleNamespace())

    notificador = principal._notificador_de_proximidade(fake_app)

    assert not isinstance(notificador, web_push.NotificadorWebPush)
