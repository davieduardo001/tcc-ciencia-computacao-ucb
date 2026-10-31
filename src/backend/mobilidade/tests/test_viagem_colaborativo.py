"""
US #199 — endpoints POST/DELETE `/viagens/{id}/posicao`, o consentimento
no embarque, a revogação no "Cheguei" e a regra de nem log guardar
coordenada (RN-C5/RN-C9).

Reutiliza as fixtures do `test_viagem.py` (mesma linha, mesmas paradas,
mesmos usuários); o comportamento fino do armazenamento e da validação de
leitura vive em `test_posicoes_colaborativas.py`.
"""

import logging

import pytest
from sqlalchemy import text

from mobilidade import routes as _base
from mobilidade.models import Viagem
from mobilidade.posicoes_colaborativas import (
    INTERVALO_MINIMO_ENVIO_S,
    ServicoPosicoesColaborativas,
)
from mobilidade.tests.test_viagem import (  # noqa: F401 – `db` é fixture
    LAT_USUARIO,
    LNG_USUARIO,
    LINHA,
    OUTRO,
    PASSAGEIRO,
    _feed,
    _h,
    _veiculo,
    client,
    db,
)

# A ~3,3 km do traçado da linha (que vive todo em lat -15.80): a leitura
# desse ponto é descartada em `fora_do_tracado`.
LONGE_DO_TRACADO = (-15.83, -47.93)


@pytest.fixture
def colaborativos(monkeypatch):
    """Troca o singleton global por um limpo para cada teste."""
    instancia = ServicoPosicoesColaborativas()
    monkeypatch.setattr(_base, "_colaborativos", instancia)
    yield instancia


def _inserir(db, *, usuario=PASSAGEIRO, compartilha=True):
    """Viagem direto na base, já com (ou sem) o consentimento da US #199."""
    from mobilidade import viagem_service

    agora = viagem_service.agora_utc()
    viagem = Viagem(
        usuario_id=usuario,
        numero_linha=LINHA,
        sentido="IDA",
        veiculo_prefixo="440001",
        embarcou_em=agora,
        encerrada_em=None,
        motivo_encerramento=None,
        origem_embarque="manual",
        compartilha_posicao_em=agora if compartilha else None,
        consentimento_versao="v1-199" if compartilha else None,
    )
    db.add(viagem)
    db.commit()
    return viagem


def _post_posicao(viagem_id, *, usuario=PASSAGEIRO, ponto=(LAT_USUARIO, LNG_USUARIO), decisao_m=20.0):
    lat, lng = ponto
    return client.post(
        f"/mobilidade/viagens/{viagem_id}/posicao",
        json={"lat": lat, "lng": lng, "precisao_m": decisao_m},
        headers=_h(usuario),
    )


def _delete_posicao(viagem_id, *, usuario=PASSAGEIRO):
    return client.delete(f"/mobilidade/viagens/{viagem_id}/posicao", headers=_h(usuario))


# ==========================================================================
# Guardas
# ==========================================================================


def test_post_sem_x_user_id_e_401(db, colaborativos):
    viagem = _inserir(db)
    resposta = _post_posicao(viagem.id, usuario=None)
    assert resposta.status_code == 401


def test_post_de_outro_usuario_e_404(db, colaborativos):
    viagem = _inserir(db)  # viagem ativa do PASSAGEIRO

    resposta = _post_posicao(viagem.id, usuario=OUTRO)

    assert resposta.status_code == 404
    assert colaborativos._armazenamento.obter(viagem.id) == []


# ==========================================================================
# Consentimento no embarque
# ==========================================================================


def _embarcar(*, compartilha=None, consentimento=None):
    corpo = {"numero_linha": LINHA, "lat": LAT_USUARIO, "lng": LNG_USUARIO}
    if compartilha is not None:
        corpo["compartilha_posicao"] = compartilha
    if consentimento is not None:
        corpo["consentimento_versao"] = consentimento
    with _feed([_veiculo()]):
        return client.post("/mobilidade/viagens", json=corpo, headers=_h())


def test_embarcar_com_consentimento_grava_a_prova_no_banco(db):
    resposta = _embarcar(compartilha=True, consentimento="v1-199")

    assert resposta.status_code == 201
    assert resposta.json()["compartilha_posicao"] is True
    linha = db.query(Viagem).filter(Viagem.usuario_id == PASSAGEIRO).one()
    assert linha.compartilha_posicao_em is not None
    assert linha.consentimento_versao == "v1-199"


def test_embarcar_sem_toggle_nao_marca_consentimento(db):
    resposta = _embarcar()

    assert resposta.status_code == 201
    assert resposta.json()["compartilha_posicao"] is False
    linha = db.query(Viagem).filter(Viagem.usuario_id == PASSAGEIRO).one()
    assert linha.compartilha_posicao_em is None
    assert linha.consentimento_versao is None


def test_embarcar_com_consentimento_sem_versao_e_recusado(db):
    assert _embarcar(compartilha=True).status_code == 422


def test_embarcar_com_toggle_desligado_e_sem_consentimento_nao_exige_versao(db):
    # desligar compartilhamento não pede prova de consentimento
    assert _embarcar(compartilha=False).status_code == 201


# ==========================================================================
# POST — aceita, monetiza o trecho e devolve motivo
# ==========================================================================


def test_post_aceita_leitura_no_tracado(db, colaborativos):
    viagem = _inserir(db)

    resposta = _post_posicao(viagem.id)

    assert resposta.status_code == 202
    corpo = resposta.json()
    assert corpo["aceita"] is True
    assert corpo["motivo"] == "aceita"
    leituras = colaborativos._armazenamento.obter(viagem.id)
    assert len(leituras) == 1


def test_post_sem_consentimento_e_409(db, colaborativos):
    viagem = _inserir(db, compartilha=False)

    resposta = _post_posicao(viagem.id)

    assert resposta.status_code == 409
    assert colaborativos._armazenamento.obter(viagem.id) == []


def test_post_repetido_muito_cedo_e_429(db, colaborativos):
    viagem = _inserir(db)

    assert _post_posicao(viagem.id).status_code == 202
    assert _post_posicao(viagem.id).status_code == 429  # dentro dos 10 s

    # passado o intervalo, volta a aceitar
    colaborativos._ultimo_envio[viagem.id] -= INTERVALO_MINIMO_ENVIO_S + 0.1
    resposta = _post_posicao(viagem.id)
    assert resposta.status_code == 202


def test_post_fora_do_tracado_e_descartado_com_motivo(db, colaborativos):
    viagem = _inserir(db)

    resposta = _post_posicao(viagem.id, ponto=LONGE_DO_TRACADO)

    assert resposta.status_code == 202
    corpo = resposta.json()
    assert corpo["aceita"] is False
    assert corpo["motivo"] == "fora_do_tracado"
    assert colaborativos._armazenamento.obter(viagem.id) == []


# ==========================================================================
# DELETE — revogação (RN-C9)
# ==========================================================================


def test_delete_para_o_compartilhamento_e_liga_as_notas(db, colaborativos):
    viagem = _inserir(db)
    _post_posicao(viagem.id)

    resposta = _delete_posicao(viagem.id)

    assert resposta.status_code == 204
    db.refresh(viagem)
    assert viagem.compartilha_posicao_em is None  # deixa de fluir
    assert viagem.consentimento_versao == "v1-199"  # prova mantida
    assert colaborativos._armazenamento.obter(viagem.id) == []
    # e qualquer POST agora é recusado com 409: o consentimento acabou
    assert _post_posicao(viagem.id).status_code == 409


def test_delete_e_idempotente(db, colaborativos):
    viagem = _inserir(db)

    assert _delete_posicao(viagem.id).status_code == 204
    # segunda vez ainda 204: sem consentimento não é erro
    assert _delete_posicao(viagem.id).status_code == 204


def test_delete_de_viagem_alheia_e_404(db, colaborativos):
    viagem = _inserir(db)
    _post_posicao(viagem.id)

    assert _delete_posicao(viagem.id, usuario=OUTRO).status_code == 404
    # não revogou a dos outros
    db.refresh(viagem)
    assert viagem.compartilha_posicao_em is not None
    assert colaborativos._armazenamento.obter(viagem.id)  # leitura continua


# ==========================================================================
# "Cheguei" — encerrar apaga a leitura (RN-C8) na hora
# ==========================================================================


def test_cheguei_limpa_a_leitura_colaborativa(db, colaborativos):
    viagem = _inserir(db)
    _post_posicao(viagem.id)

    with _feed([_veiculo()]):
        resposta = client.post(f"/mobilidade/viagens/{viagem.id}/encerrar", headers=_h())

    assert resposta.status_code == 200
    assert colaborativos._armazenamento.obter(viagem.id) == []


# ==========================================================================
# LGPD — nem o log guarda coordenada (RN-C5)
# ==========================================================================


def test_nenhuma_coordenada_de_post_aparece_em_log(db, colaborativos, caplog):
    viagem = _inserir(db)

    with caplog.at_level(logging.DEBUG, logger="mobilidade.posicoes_colaborativas"):
        _post_posicao(viagem.id)  # aceita: latitude -15.80x
        _post_posicao(viagem.id, ponto=LONGE_DO_TRACADO)  # descarta: -15.83

    texto = caplog.text
    assert str(LAT_USUARIO) not in texto
    assert str(LNG_USUARIO) not in texto
    assert str(LONGE_DO_TRACADO[0]) not in texto
    assert str(LONGE_DO_TRACADO[1]) not in texto


def test_as_colunas_novas_nao_guardam_coordenada_no_banco(db):
    """As provas do consentimento não têm espaço para lat/lng (RN-C1)."""
    from mobilidade import viagem_service

    agora = viagem_service.agora_utc()
    viagem = Viagem(
        usuario_id=PASSAGEIRO,
        numero_linha=LINHA,
        sentido="IDA",
        veiculo_prefixo="440001",
        embarcou_em=agora,
        origem_embarque="manual",
        compartilha_posicao_em=agora,
        consentimento_versao="v1-199",
    )
    db.add(viagem)
    db.commit()
    db.refresh(viagem)

    dicionario = viagem.__dict__
    assert not any("lat" in chave.lower() or "lng" in chave.lower() for chave in dicionario)
