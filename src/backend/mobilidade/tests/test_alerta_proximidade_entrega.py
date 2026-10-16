"""
US #172 — o aviso de proximidade chega ao app (entrega dentro do app).

O worker grava o alerta; `GET /viagens/ativa` devolve o pendente e o app o
confirma em `POST /viagens/{id}/alerta-proximidade/visto`. Cenário 2 (uma vez
só) continua no banco; aqui se prova que o aviso aparece uma vez para a
pessoa certa, e não volta depois de visto.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from mobilidade import alerta_proximidade_entrega as entrega
from mobilidade.models.alerta_proximidade import AlertaProximidade
from mobilidade.providers.contratos_proximidade import PreferenciasDeNotificacao
from mobilidade.providers.eta_destino_trajeto import EtaDoDestinoPorTrajeto
from mobilidade.providers.viagens_ativas_banco import ViagensAtivasDoBanco
from mobilidade.rota_service import RotaService
from mobilidade.services.servico_notificacoes import NotificadorMock
from mobilidade.services.servico_proximidade import EVENTO_DISPARADO, ServicoProximidade
from mobilidade.tests.test_viagem import (  # noqa: F401  (db é fixture)
    COD,
    IDX,
    OUTRO,
    PASSAGEIRO,
    _ativa,
    _embarcar,
    _h,
    _inserir_viagem,
    _veiculo,
    client,
    db,
)

USUARIOS = [PASSAGEIRO, OUTRO]


@pytest.fixture(autouse=True)
def sem_alertas(db):
    db.query(AlertaProximidade).filter(AlertaProximidade.usuario_id.in_(USUARIOS)).delete(
        synchronize_session=False
    )
    db.commit()
    yield
    db.query(AlertaProximidade).filter(AlertaProximidade.usuario_id.in_(USUARIOS)).delete(
        synchronize_session=False
    )
    db.commit()


def _alerta(db, viagem, *, usuario=None, status="disparado", ha=timedelta(minutes=1),
            codigo=COD["C"], eta=2.5, viagem_id=None):
    alerta = AlertaProximidade(
        usuario_id=usuario or viagem.usuario_id,
        viagem_id=viagem_id or str(viagem.id),
        linha_id=viagem.numero_linha,
        parada_destino_codigo=codigo,
        parada_destino_nome="Parada C",
        status=status,
        eta_minutos=eta,
        disparado_em=datetime.utcnow() - ha,
    )
    db.add(alerta)
    db.commit()
    return alerta


def _visto(viagem_id, usuario=PASSAGEIRO):
    return client.post(
        f"/mobilidade/viagens/{viagem_id}/alerta-proximidade/visto", headers=_h(usuario)
    )


def _pendente_na_api(veiculos=None):
    r = _ativa(veiculos or [_veiculo()])
    assert r.status_code == 200
    return r.json()["alerta_proximidade"]


class TestAvisoNaViagemAtiva:
    def test_sem_alerta_o_campo_vem_nulo(self, db):
        _inserir_viagem(db, destino=COD["C"])

        assert _pendente_na_api() is None

    def test_alerta_pendente_chega_com_o_que_a_tela_precisa(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        alerta = _alerta(db, viagem, eta=2.5)

        aviso = _pendente_na_api()

        assert aviso["id"] == str(alerta.id)
        assert aviso["parada_codigo"] == COD["C"]
        assert aviso["parada_nome"] == "Parada C"
        assert aviso["eta_minutos"] == 2.5
        # UTC com fuso explícito, senão o navegador lê como horário local.
        assert aviso["disparado_em"].endswith(("Z", "+00:00"))

    def test_nao_expoe_usuario_nem_viagem(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem)

        aviso = _pendente_na_api()

        assert "usuario_id" not in aviso
        assert "viagem_id" not in aviso

    def test_alerta_ja_visto_nao_volta(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem, status="entregue")

        assert _pendente_na_api() is None

    def test_alerta_de_outro_usuario_nunca_aparece(self, db):
        # Mesmo com o id da viagem do passageiro conhecido, o alerta é de OUTRO.
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem, usuario=OUTRO)

        assert _pendente_na_api() is None

    def test_alerta_de_outra_viagem_nao_aparece(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem, viagem_id=str(uuid.uuid4()))

        assert _pendente_na_api() is None

    def test_aviso_velho_nao_aparece(self, db):
        # Reabrir o app 20 min depois não mostra um "está chegando" de antes.
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem, ha=entrega.VALIDADE_DO_AVISO + timedelta(minutes=5))

        assert _pendente_na_api() is None

    def test_aviso_dentro_da_validade_aparece(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem, ha=entrega.VALIDADE_DO_AVISO - timedelta(minutes=2))

        assert _pendente_na_api() is not None

    def test_dois_alertas_pendentes_mostram_o_mais_recente(self, db):
        # Quem trocou de destino no meio da viagem pode ter dois.
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem, codigo=COD["B"], ha=timedelta(minutes=8))
        recente = _alerta(db, viagem, codigo=COD["C"], ha=timedelta(minutes=1))

        assert _pendente_na_api()["id"] == str(recente.id)

    def test_viagem_encerrada_nao_mostra_aviso(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem)
        client.post(f"/mobilidade/viagens/{viagem.id}/encerrar", headers=_h())

        corpo = _ativa([_veiculo()]).json()

        assert corpo["ativa"] is False
        assert corpo["alerta_proximidade"] is None


class TestConfirmarQueViu:
    def test_visto_faz_o_aviso_sumir(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem)
        assert _pendente_na_api() is not None

        r = _visto(viagem.id)

        assert r.status_code == 204
        assert r.content == b""
        assert _pendente_na_api() is None
        db.expire_all()
        assert db.query(AlertaProximidade).one().status == "entregue"

    def test_e_idempotente(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem)

        assert _visto(viagem.id).status_code == 204
        assert _visto(viagem.id).status_code == 204
        assert _pendente_na_api() is None

    def test_o_alerta_continua_gravado_para_nao_disparar_de_novo(self, db):
        # Cenário 2: "visto" muda o status; a linha fica, e o índice único
        # (viagem, parada) segue impedindo um segundo disparo.
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem)

        _visto(viagem.id)

        db.expire_all()
        assert db.query(AlertaProximidade).count() == 1

    def test_outro_usuario_nao_consegue_marcar_o_alerta_alheio(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem)

        r = _visto(viagem.id, usuario=OUTRO)

        assert r.status_code == 204  # não revela se o id existe
        assert _pendente_na_api() is not None

    def test_viagem_inexistente_nao_muda_nada(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        _alerta(db, viagem)

        assert _visto(uuid.uuid4()).status_code == 204
        assert _pendente_na_api() is not None

    def test_so_a_viagem_informada(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])
        alheio = _alerta(db, viagem, viagem_id=str(uuid.uuid4()))

        _visto(viagem.id)

        db.expire_all()
        assert db.get(AlertaProximidade, alheio.id).status == "disparado"

    def test_exige_identidade(self, db):
        r = client.post(f"/mobilidade/viagens/{uuid.uuid4()}/alerta-proximidade/visto")

        assert r.status_code == 401

    def test_id_de_viagem_invalido_e_422(self, db):
        r = client.post("/mobilidade/viagens/nao-e-uuid/alerta-proximidade/visto", headers=_h())

        assert r.status_code == 422


class TestDoWorkerAteATela:
    def test_ciclo_completo(self, db):
        """Embarca pela API → o worker avisa → o app vê → o app confirma → some."""

        class _Veiculos:
            def obter_das_linhas(self, numeros):
                # O ônibus da viagem, ~2 km antes do destino.
                return {n: [_veiculo(indice=IDX["C"] - 20, prefixo="440001")] for n in numeros}

        class _Prefs:
            def obter(self, usuario_id, db):
                return PreferenciasDeNotificacao()

        resposta = _embarcar([_veiculo(prefixo="440001")], destino=COD["C"])
        assert resposta.status_code == 201
        viagem_id = resposta.json()["id"]

        eventos = ServicoProximidade(
            viagens=ViagensAtivasDoBanco(),
            veiculos=_Veiculos(),
            preferencias=_Prefs(),
            notificador=NotificadorMock(),
            eta=EtaDoDestinoPorTrajeto(RotaService()),
        ).verificar_proximidades(db)
        assert EVENTO_DISPARADO in eventos

        feed = [_veiculo(indice=IDX["C"] - 20, prefixo="440001")]
        aviso = _pendente_na_api(feed)
        assert aviso is not None
        assert aviso["parada_codigo"] == COD["C"]
        assert 0 < aviso["eta_minutos"] <= 30

        assert _visto(viagem_id).status_code == 204
        assert _pendente_na_api(feed) is None
