"""
Tempo do ônibus nas paradas de subir e descer de uma rota (issue #190).

Usa o trajeto sintético de test_rota_service.py (linha reta leste-oeste, um
ponto a cada ~107 m) e semeia `Parada`/`RotaParada` à mão, para cada asserção
poder ser conferida na mão: onde o ônibus está, onde estão as paradas de
subir e de descer, quantos metros há entre elas.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mobilidade.chegadas_da_rota import codigo_da_parada, vinculos_da_rota
from mobilidade.geometria import TrajetoMedido
from mobilidade.main import app
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.tests.test_rota_service import PREFIXO, _semear, _trajeto
from shared.database import SessionLocal

client = TestClient(app)

TRAJETO = _trajeto()
MEDIDO = TrajetoMedido(TRAJETO)
LINHA_A = f"{PREFIXO}R01"
LINHA_B = f"{PREFIXO}R02"

IDX_SOBE, IDX_DESCE = 40, 160
COD_SOBE, COD_DESCE, COD_OUTRA = "PR-R190S", "PR-R190D", "PR-R190X"

TODOS_OS_DIAS = {str(d): [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)] for d in range(7)}


# --------------------------------------------------------------------------
# semeadura
# --------------------------------------------------------------------------


def _limpar(db) -> None:
    for numero in (LINHA_A, LINHA_B):
        db.query(RotaParada).filter(RotaParada.numero == numero).delete(synchronize_session=False)
        db.query(RotaCelula).filter(RotaCelula.numero == numero).delete(synchronize_session=False)
        db.query(Rota).filter(Rota.numero == numero).delete(synchronize_session=False)
    db.query(Parada).filter(Parada.codigo.like("PR-R190%")).delete(synchronize_session=False)
    db.commit()


def _parada(db, codigo, indice, deslocar_lat=0.0) -> Parada:
    lat, lng = TRAJETO[indice]
    parada = Parada(codigo=codigo, nome=f"Parada {codigo}", lat=lat + deslocar_lat, lng=lng)
    db.add(parada)
    db.flush()
    return parada


def _vincular(db, parada, numero, indice, sentido="IDA"):
    db.add(
        RotaParada(
            numero=numero,
            sentido=sentido,
            parada_id=parada.id,
            ordem=indice // 20,
            indice_trajeto=indice,
            distancia_acumulada_m=MEDIDO.acumulado[indice],
            distancia_ao_trajeto_m=2.0,
        )
    )


@pytest.fixture
def db():
    """Linha A (IDA) com horários o dia todo, 60 min de percurso e as duas paradas."""
    sessao = SessionLocal()
    _limpar(sessao)
    _semear(sessao, LINHA_A, "IDA", TRAJETO)
    _semear(sessao, LINHA_B, "IDA", TRAJETO)
    sessao.flush()  # a SessionLocal do projeto tem autoflush desligado
    for numero in (LINHA_A, LINHA_B):
        rota = sessao.query(Rota).filter(Rota.numero == numero).one()
        rota.horarios_por_dia = TODOS_OS_DIAS
        rota.tempo_percurso_min = 60

    sobe = _parada(sessao, COD_SOBE, IDX_SOBE)
    desce = _parada(sessao, COD_DESCE, IDX_DESCE)
    _vincular(sessao, sobe, LINHA_A, IDX_SOBE)
    _vincular(sessao, desce, LINHA_A, IDX_DESCE)
    _vincular(sessao, sobe, LINHA_B, IDX_SOBE)
    _vincular(sessao, desce, LINHA_B, IDX_DESCE)
    sessao.commit()

    yield sessao
    _limpar(sessao)
    sessao.close()


# --------------------------------------------------------------------------
# veículos e chamadas
# --------------------------------------------------------------------------


def _veiculo(indice, velocidade=30.0, sentido="IDA", prefixo="440001", idade_s=5):
    lat, lng = TRAJETO[indice]
    return PosicaoVeiculo(
        prefixo=prefixo,
        lat=lat,
        lng=lng,
        sentido=sentido,
        velocidade=velocidade,
        direcao=90.0,
        atualizado_em=datetime.now(timezone.utc) - timedelta(seconds=idade_s),
        operadora="VIAÇÃO TESTE",
    )


def _com_posicoes(por_linha):
    async def falso(numeros):
        return {n: por_linha.get(n, []) for n in numeros}

    mock = AsyncMock(side_effect=falso)
    return patch("mobilidade.routes._posicao_service.posicoes_das_linhas", mock), mock


def _perna(numero=LINHA_A, sobe=COD_SOBE, desce=COD_DESCE, sentido="IDA"):
    return {"numero": numero, "sentido": sentido, "embarque_codigo": sobe, "desembarque_codigo": desce}


def _post(pernas, por_linha=None):
    patcher, _ = _com_posicoes(por_linha or {})
    with patcher:
        return client.post("/mobilidade/rotas/chegadas", json={"pernas": pernas})


def _minutos(de, ate, velocidade_kmh=30.0):
    return MEDIDO.metros_entre(de, ate) / (velocidade_kmh * 1000 / 60)


# ==========================================================================
# Código da parada de um ponto do trecho
# ==========================================================================


class TestCodigoDaParada:
    def _vinculos(self, db, numero=LINHA_A):
        return vinculos_da_rota(db, numero, "IDA")

    def test_ponto_em_cima_da_parada(self, db):
        lat, lng = TRAJETO[IDX_SOBE]
        assert codigo_da_parada(self._vinculos(db), lat, lng) == COD_SOBE

    def test_a_30_m_ainda_e_a_mesma_parada(self, db):
        lat, lng = TRAJETO[IDX_SOBE]
        assert codigo_da_parada(self._vinculos(db), lat + 0.00027, lng) == COD_SOBE

    def test_a_60_m_ja_nao_e(self, db):
        lat, lng = TRAJETO[IDX_SOBE]
        assert codigo_da_parada(self._vinculos(db), lat + 0.00055, lng) is None

    def test_escolhe_a_mais_proxima(self, db):
        perto = _parada(db, "PR-R190P", IDX_SOBE, deslocar_lat=0.0001)  # ~11 m
        _vincular(db, perto, LINHA_A, IDX_SOBE)
        db.commit()
        lat, lng = TRAJETO[IDX_SOBE]
        # O ponto está a 0 m da COD_SOBE e a ~11 m da outra.
        assert codigo_da_parada(self._vinculos(db), lat, lng) == COD_SOBE
        assert codigo_da_parada(self._vinculos(db), lat + 0.0001, lng) == "PR-R190P"

    def test_so_olha_paradas_da_mesma_rota(self, db):
        """Uma parada de OUTRA linha, colada no ponto, não vira o embarque desta."""
        outra = _parada(db, COD_OUTRA, 100)
        _vincular(db, outra, LINHA_B, 100)
        db.commit()
        lat, lng = TRAJETO[100]
        assert codigo_da_parada(self._vinculos(db, LINHA_A), lat, lng) is None
        assert codigo_da_parada(self._vinculos(db, LINHA_B), lat, lng) == COD_OUTRA

    def test_rota_sem_paradas_ingeridas(self, db):
        lat, lng = TRAJETO[IDX_SOBE]
        assert codigo_da_parada(vinculos_da_rota(db, "NAO.EXISTE", "IDA"), lat, lng) is None
        assert codigo_da_parada([], lat, lng) is None

    def test_raio_configuravel(self, db):
        lat, lng = TRAJETO[IDX_SOBE]
        assert codigo_da_parada(self._vinculos(db), lat + 0.00055, lng, raio_m=80) == COD_SOBE


class TestRotasDevolveOCodigo:
    def test_embarque_e_desembarque_trazem_parada_codigo(self, db):
        origem, destino = TRAJETO[IDX_SOBE], TRAJETO[IDX_DESCE]
        patcher, _ = _com_posicoes({})
        with patcher:
            r = client.get(
                "/mobilidade/rotas",
                params={
                    "origem_lat": origem[0],
                    "origem_lng": origem[1],
                    "destino_lat": destino[0],
                    "destino_lng": destino[1],
                },
            )
        assert r.status_code == 200
        pernas = [p for o in r.json() for p in o["pernas"] if p["numero"] == LINHA_A]
        assert pernas, "a linha semeada deveria aparecer como opção"
        assert pernas[0]["embarque"]["parada_codigo"] == COD_SOBE
        assert pernas[0]["desembarque"]["parada_codigo"] == COD_DESCE

    def test_ponto_sem_parada_ingerida_vem_nulo(self, db):
        """Sem `RotaParada` na rota, o código é `null` e a rota continua funcionando."""
        db.query(RotaParada).filter(RotaParada.numero == LINHA_A).delete(synchronize_session=False)
        db.commit()
        origem, destino = TRAJETO[IDX_SOBE], TRAJETO[IDX_DESCE]
        patcher, _ = _com_posicoes({})
        with patcher:
            r = client.get(
                "/mobilidade/rotas",
                params={
                    "origem_lat": origem[0],
                    "origem_lng": origem[1],
                    "destino_lat": destino[0],
                    "destino_lng": destino[1],
                },
            )
        assert r.status_code == 200
        pernas = [p for o in r.json() for p in o["pernas"] if p["numero"] == LINHA_A]
        assert pernas[0]["embarque"]["parada_codigo"] is None
        assert pernas[0]["desembarque"]["parada_codigo"] is None


# ==========================================================================
# POST /rotas/chegadas — ao vivo
# ==========================================================================


class TestChegadasAoVivo:
    def test_embarque_ao_vivo_ate_a_parada_de_subir(self, db):
        r = _post([_perna()], {LINHA_A: [_veiculo(20, prefixo="440077")]})

        assert r.status_code == 200
        emb = r.json()["pernas"][0]["embarque"]
        assert emb["fonte"] == "ao_vivo"
        assert emb["prefixo"] == "440077"
        assert emb["parada_codigo"] == COD_SOBE
        assert emb["eta_minutos"] == pytest.approx(_minutos(20, IDX_SOBE), abs=0.3)
        assert emb["horario_previsto"] is None

    def test_desembarque_e_do_mesmo_onibus_que_o_passageiro_pega(self, db):
        r = _post([_perna()], {LINHA_A: [_veiculo(20, prefixo="440077")]})

        perna = r.json()["pernas"][0]
        assert perna["desembarque"]["fonte"] == "ao_vivo"
        assert perna["desembarque"]["prefixo"] == "440077"
        assert perna["desembarque"]["eta_minutos"] == pytest.approx(
            _minutos(20, IDX_DESCE), abs=0.3
        )
        assert perna["desembarque"]["eta_minutos"] > perna["embarque"]["eta_minutos"]

    def test_com_varios_o_de_menor_eta_ao_embarque_dita_o_desembarque(self, db):
        perto = _veiculo(30, prefixo="PERTO")
        longe = _veiculo(10, prefixo="LONGE")
        r = _post([_perna()], {LINHA_A: [longe, perto]})

        perna = r.json()["pernas"][0]
        assert perna["embarque"]["prefixo"] == "PERTO"
        assert perna["desembarque"]["prefixo"] == "PERTO"

    def test_onibus_que_ja_passou_da_parada_de_subir_nao_serve_de_embarque(self, db):
        """Está entre as duas paradas: o passageiro já o perdeu. Cai no previsto."""
        r = _post([_perna()], {LINHA_A: [_veiculo(80, prefixo="PASSOU")]})

        perna = r.json()["pernas"][0]
        assert perna["embarque"]["fonte"] == "previsto"
        assert perna["embarque"]["prefixo"] is None
        assert perna["desembarque"]["fonte"] == "previsto"

    def test_onibus_de_sentido_oposto_e_ignorado(self, db):
        r = _post([_perna()], {LINHA_A: [_veiculo(20, sentido="VOLTA")]})
        assert r.json()["pernas"][0]["embarque"]["fonte"] == "previsto"

    def test_onibus_parado_nao_tem_eta_e_cai_no_previsto(self, db):
        r = _post([_perna()], {LINHA_A: [_veiculo(20, velocidade=0.0)]})
        assert r.json()["pernas"][0]["embarque"]["fonte"] == "previsto"

    def test_posicao_velha_nao_vale(self, db):
        r = _post([_perna()], {LINHA_A: [_veiculo(20, idade_s=10 * 60)]})
        assert r.json()["pernas"][0]["embarque"]["fonte"] == "previsto"


# ==========================================================================
# POST /rotas/chegadas — previsto e sem dado
# ==========================================================================


class TestChegadasPrevistas:
    def test_sem_onibus_usa_o_horario_previsto(self, db):
        r = _post([_perna()])

        perna = r.json()["pernas"][0]
        emb, desc = perna["embarque"], perna["desembarque"]
        assert emb["fonte"] == "previsto" and desc["fonte"] == "previsto"
        assert emb["horario_previsto"] and desc["horario_previsto"]
        assert emb["prefixo"] is None and desc["prefixo"] is None
        assert 0 <= emb["eta_minutos"] <= 60

    def test_previsto_do_desembarque_e_o_do_embarque_mais_o_trecho_do_percurso(self, db):
        """60 min de percurso × a fração do trajeto entre as duas paradas."""
        perna = _post([_perna()]).json()["pernas"][0]

        esperado = 60 * (MEDIDO.acumulado[IDX_DESCE] - MEDIDO.acumulado[IDX_SOBE]) / MEDIDO.comprimento_m
        diferenca = perna["desembarque"]["eta_minutos"] - perna["embarque"]["eta_minutos"]
        assert diferenca == pytest.approx(esperado, abs=0.3)

    def test_sem_onibus_e_sem_horarios_nao_inventa(self, db):
        rota = db.query(Rota).filter(Rota.numero == LINHA_A).one()
        rota.horarios_por_dia = None
        db.commit()

        perna = _post([_perna()]).json()["pernas"][0]
        for ponto in (perna["embarque"], perna["desembarque"]):
            assert ponto["eta_minutos"] is None
            assert ponto["fonte"] is None
        assert perna["embarque"]["parada_codigo"] == COD_SOBE

    def test_sem_tempo_de_percurso_o_desembarque_previsto_nao_inventa(self, db):
        rota = db.query(Rota).filter(Rota.numero == LINHA_A).one()
        rota.tempo_percurso_min = None
        db.commit()

        perna = _post([_perna()]).json()["pernas"][0]
        assert perna["desembarque"]["eta_minutos"] is None
        assert perna["desembarque"]["fonte"] is None


# ==========================================================================
# POST /rotas/chegadas — bordas
# ==========================================================================


class TestChegadasBordas:
    def test_descer_antes_de_subir_nao_tem_tempo_de_descida(self, db):
        # O ônibus (índice 20) chegaria à parada "de descer" (40) ANTES da de
        # subir (160): sem a guarda de ordem, sairia um tempo de descida.
        perna = _post(
            [_perna(sobe=COD_DESCE, desce=COD_SOBE)], {LINHA_A: [_veiculo(20)]}
        ).json()["pernas"][0]
        assert perna["embarque"]["fonte"] == "ao_vivo"
        assert perna["desembarque"]["eta_minutos"] is None
        assert perna["desembarque"]["fonte"] is None

    def test_subir_e_descer_na_mesma_parada_nao_tem_tempo_de_descida(self, db):
        perna = _post([_perna(desce=COD_SOBE)], {LINHA_A: [_veiculo(20)]}).json()["pernas"][0]
        assert perna["embarque"]["fonte"] == "ao_vivo"
        assert perna["desembarque"]["eta_minutos"] is None

    def test_codigo_que_nao_existe_devolve_sem_dado_e_nao_quebra(self, db):
        r = _post([_perna(sobe="PR-NAO-EXISTE", desce="PR-TAMBEM-NAO")], {LINHA_A: [_veiculo(20)]})

        assert r.status_code == 200
        perna = r.json()["pernas"][0]
        assert perna["embarque"] == {
            "parada_codigo": "PR-NAO-EXISTE",
            "eta_minutos": None,
            "fonte": None,
            "prefixo": None,
            "horario_previsto": None,
        }
        assert perna["desembarque"]["eta_minutos"] is None

    def test_parada_de_outra_linha_nao_serve(self, db):
        outra = _parada(db, COD_OUTRA, 100)
        _vincular(db, outra, LINHA_B, 100)
        db.commit()
        perna = _post([_perna(sobe=COD_OUTRA)], {LINHA_A: [_veiculo(20)]}).json()["pernas"][0]
        assert perna["embarque"]["eta_minutos"] is None

    def test_pontos_sem_codigo_voltam_vazios(self, db):
        r = _post([_perna(sobe=None, desce=None)], {LINHA_A: [_veiculo(20)]})
        assert r.status_code == 200
        perna = r.json()["pernas"][0]
        assert perna["embarque"]["parada_codigo"] is None
        assert perna["embarque"]["eta_minutos"] is None
        assert perna["desembarque"]["eta_minutos"] is None

    def test_so_o_desembarque_sem_embarque_nao_inventa(self, db):
        perna = _post([_perna(sobe=None)], {LINHA_A: [_veiculo(20)]}).json()["pernas"][0]
        assert perna["desembarque"]["eta_minutos"] is None

    def test_em_lote_mantem_a_ordem_e_le_o_feed_uma_vez(self, db):
        patcher, mock = _com_posicoes(
            {LINHA_A: [_veiculo(20, prefixo="AAA")], LINHA_B: [_veiculo(30, prefixo="BBB")]}
        )
        with patcher:
            r = client.post(
                "/mobilidade/rotas/chegadas",
                json={"pernas": [_perna(LINHA_B), _perna(LINHA_A)]},
            )

        pernas = r.json()["pernas"]
        assert [p["numero"] for p in pernas] == [LINHA_B, LINHA_A]
        assert pernas[0]["embarque"]["prefixo"] == "BBB"
        assert pernas[1]["embarque"]["prefixo"] == "AAA"
        assert mock.await_count == 1
        assert set(mock.await_args.args[0]) == {LINHA_A, LINHA_B}

    def test_calculado_em_vem_com_fuso(self, db):
        r = _post([_perna()])
        assert r.json()["calculado_em"].endswith("+00:00")


class TestValidacaoDoCorpo:
    @pytest.mark.parametrize(
        "corpo",
        [
            {},
            {"pernas": []},
            {"pernas": [_perna()] * 7},
            {"pernas": [{"numero": "", "sentido": "IDA"}]},
            {"pernas": [{"numero": LINHA_A, "sentido": ""}]},
            {"pernas": [{"numero": "x" * 21, "sentido": "IDA"}]},
            {"pernas": "nao-e-lista"},
        ],
    )
    def test_corpo_invalido_e_422(self, db, corpo):
        assert client.post("/mobilidade/rotas/chegadas", json=corpo).status_code == 422

    def test_seis_pernas_e_o_limite(self, db):
        assert _post([_perna()] * 6).status_code == 200
