"""
US #171 — Pegar o ônibus: embarcar, acompanhar e encerrar a viagem.

Usa o trajeto sintético de test_rota_service.py (linha reta leste-oeste, um
ponto a cada ~107 m) e semeia `Parada`/`RotaParada` à mão, para cada
asserção poder ser conferida na mão: onde o ônibus está, onde estão as
paradas, o que sobra pela frente.
"""

import logging
import os
import subprocess
import sys
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from mobilidade import viagem_service as servico
from mobilidade.eta_service import eta_ate_indice
from mobilidade.geometria import TrajetoMedido, distancia_metros
from mobilidade.main import app
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.models.viagem import Viagem
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.providers.viagens_ativas_banco import ViagensAtivasDoBanco
from mobilidade.rota_service import RotaService
from mobilidade.tests.test_rota_service import PREFIXO, _semear, _trajeto
from shared.database import SessionLocal

client = TestClient(app)

TRAJETO = _trajeto()
MEDIDO = TrajetoMedido(TRAJETO)
LINHA = f"{PREFIXO}V01"
LINHA_CIRCULAR = f"{PREFIXO}V02"
LINHA_SEM_PARADAS = f"{PREFIXO}V03"
LINHA_DENSA = f"{PREFIXO}V04"

# Paradas da linha, em ordem de percurso.
IDX = {"A": 40, "B": 100, "C": 160}
COD = {"A": "PR-V171A", "B": "PR-V171B", "C": "PR-V171C"}
COD_FORA = "PR-V171Z"  # existe, mas não é parada desta linha

PASSAGEIRO = uuid.UUID("00000000-0000-4000-8000-000000000171")
OUTRO = uuid.UUID("00000000-0000-4000-8000-000000000172")
USUARIOS = [PASSAGEIRO, OUTRO]

# O passageiro está na parada B.
LAT_USUARIO, LNG_USUARIO = TRAJETO[IDX["B"]]


def _h(usuario=PASSAGEIRO):
    return {"X-User-Id": str(usuario)}


# --------------------------------------------------------------------------
# semeadura
# --------------------------------------------------------------------------


def _limpar(db) -> None:
    db.query(Viagem).filter(Viagem.usuario_id.in_(USUARIOS)).delete(synchronize_session=False)
    for numero in (LINHA, LINHA_CIRCULAR, LINHA_SEM_PARADAS, LINHA_DENSA):
        db.query(RotaParada).filter(RotaParada.numero == numero).delete(synchronize_session=False)
        db.query(RotaCelula).filter(RotaCelula.numero == numero).delete(synchronize_session=False)
        db.query(Rota).filter(Rota.numero == numero).delete(synchronize_session=False)
    db.query(Parada).filter(Parada.codigo.like("PR-V171%")).delete(synchronize_session=False)
    db.commit()


def _vincular(db, parada, numero, sentido, indice):
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
    sessao = SessionLocal()
    _limpar(sessao)
    # Linha comum (IDA) com as paradas A, B, C; uma parada de outra linha.
    _semear(sessao, LINHA, "IDA", TRAJETO)
    _semear(sessao, LINHA_CIRCULAR, "CIRCULAR", TRAJETO)
    _semear(sessao, LINHA_SEM_PARADAS, "IDA", TRAJETO)
    sessao.flush()  # a SessionLocal do projeto tem autoflush desligado

    paradas = {}
    for chave, indice in IDX.items():
        lat, lng = TRAJETO[indice]
        paradas[chave] = Parada(codigo=COD[chave], nome=f"Parada {chave}", lat=lat, lng=lng)
        sessao.add(paradas[chave])
    lat, lng = TRAJETO[10]
    sessao.add(Parada(codigo=COD_FORA, nome="Parada de outra linha", lat=lat, lng=lng))
    sessao.flush()

    for chave, indice in IDX.items():
        _vincular(sessao, paradas[chave], LINHA, "IDA", indice)
    # A circular só tem A e B.
    _vincular(sessao, paradas["A"], LINHA_CIRCULAR, "CIRCULAR", IDX["A"])
    _vincular(sessao, paradas["B"], LINHA_CIRCULAR, "CIRCULAR", IDX["B"])
    sessao.commit()

    yield sessao
    _limpar(sessao)
    sessao.close()


# --------------------------------------------------------------------------
# veículos e chamadas
# --------------------------------------------------------------------------


def _veiculo(indice=IDX["B"], *, prefixo="440001", sentido="IDA", idade_s=5, deslocar_lat=0.0):
    lat, lng = TRAJETO[indice]
    return PosicaoVeiculo(
        prefixo=prefixo,
        lat=lat + deslocar_lat,
        lng=lng,
        sentido=sentido,
        velocidade=30.0,
        direcao=90.0,
        atualizado_em=datetime.now(timezone.utc) - timedelta(seconds=idade_s),
        operadora="VIAÇÃO TESTE",
    )


def _feed(veiculos):
    return patch(
        "mobilidade.routes._posicao_service.posicoes_da_linha",
        AsyncMock(return_value=veiculos),
    )


def _embarcar(
    veiculos, *, linha=LINHA, destino=None, usuario=PASSAGEIRO, lat=None, lng=None, prefixo=None
):
    corpo = {
        "numero_linha": linha,
        "lat": LAT_USUARIO if lat is None else lat,
        "lng": LNG_USUARIO if lng is None else lng,
    }
    if destino is not None:
        corpo["parada_destino_codigo"] = destino
    if prefixo is not None:
        corpo["veiculo_prefixo"] = prefixo
    with _feed(veiculos):
        return client.post("/mobilidade/viagens", json=corpo, headers=_h(usuario))


def _ativa(veiculos, usuario=PASSAGEIRO):
    with _feed(veiculos):
        return client.get("/mobilidade/viagens/ativa", headers=_h(usuario))


def _inserir_viagem(db, *, usuario=PASSAGEIRO, linha=LINHA, destino=None, prefixo="440001",
                    sentido="IDA", embarcou_ha=timedelta(minutes=10), encerrada=False):
    agora = servico.agora_utc()
    viagem = Viagem(
        usuario_id=usuario,
        numero_linha=linha,
        sentido=sentido,
        veiculo_prefixo=prefixo,
        parada_destino_codigo=destino,
        embarcou_em=agora - embarcou_ha,
        encerrada_em=agora if encerrada else None,
        motivo_encerramento="usuario" if encerrada else None,
        origem_embarque="manual",
    )
    db.add(viagem)
    db.commit()
    return viagem


# ==========================================================================
# Identidade
# ==========================================================================


class TestIdentidade:
    def test_sem_x_user_id_nao_embarca(self, db):
        with _feed([_veiculo()]):
            r = client.post(
                "/mobilidade/viagens",
                json={"numero_linha": LINHA, "lat": LAT_USUARIO, "lng": LNG_USUARIO},
            )
        assert r.status_code == 401

    def test_sem_x_user_id_nao_consulta(self, db):
        assert client.get("/mobilidade/viagens/ativa").status_code == 401

    def test_x_user_id_invalido_e_401(self, db):
        r = client.get("/mobilidade/viagens/ativa", headers={"X-User-Id": "nao-e-uuid"})
        assert r.status_code == 401

    def test_o_dono_vem_do_header_e_nao_do_corpo(self, db):
        with _feed([_veiculo()]):
            r = client.post(
                "/mobilidade/viagens",
                json={
                    "numero_linha": LINHA,
                    "lat": LAT_USUARIO,
                    "lng": LNG_USUARIO,
                    "usuario_id": str(OUTRO),
                },
                headers=_h(PASSAGEIRO),
            )
        assert r.status_code == 201
        assert db.query(Viagem).one().usuario_id == PASSAGEIRO


# ==========================================================================
# Embarque (Cenários 1 e 4)
# ==========================================================================


class TestEmbarque:
    def test_cenario_1_veiculo_da_linha_perto_registra_a_viagem(self, db):
        r = _embarcar([_veiculo(prefixo="440007")])

        assert r.status_code == 201
        corpo = r.json()
        assert corpo["numero_linha"] == LINHA
        assert corpo["veiculo_prefixo"] == "440007"
        assert corpo["sentido"] == "IDA"
        assert corpo["encerrada_em"] is None
        assert corpo["embarcou_em"].endswith("Z") or corpo["embarcou_em"].endswith("+00:00")

        salva = db.query(Viagem).one()
        assert str(salva.id) == corpo["id"]
        assert salva.origem_embarque == "manual"

    def test_a_posicao_do_usuario_nao_e_persistida(self, db):
        """RN-06: nem coluna existe — não há onde guardar a trilha.

        US #199 acrescentou `compartilha_posicao_em` (prova de consentimento,
        data e hora) — o filtro fica só em coordenadas; a checagem de valores
        abaixo continua cobrindo todas as colunas da tabela.
        """
        colunas = {c["name"] for c in inspect(db.get_bind()).get_columns("viagem")}
        assert not {c for c in colunas if "lat" in c or "lng" in c or "coordenada" in c}

        _embarcar([_veiculo()])
        salva = db.query(Viagem).one()
        guardado = " ".join(str(getattr(salva, c)) for c in colunas)
        assert str(LAT_USUARIO)[:8] not in guardado
        assert str(LNG_USUARIO)[:8] not in guardado

    def test_aceita_veiculo_ate_o_raio_de_embarque(self, db):
        # ~78 m do usuário.
        r = _embarcar([_veiculo(deslocar_lat=0.0007)])
        assert r.status_code == 201

    def test_cenario_4_veiculo_longe_nao_registra(self, db):
        # ~133 m do usuário (fora do raio) e a ~3 km da parada dele (ETA de
        # vários minutos): nem o raio nem o "ônibus chegando" confirmam.
        r = _embarcar([_veiculo(70, deslocar_lat=0.0012)])

        assert r.status_code == 422
        assert "não conseguimos confirmar" in r.json()["detail"].lower()
        assert db.query(Viagem).count() == 0

    def test_cenario_4_sem_nenhum_veiculo_na_linha(self, db):
        assert _embarcar([]).status_code == 422
        assert db.query(Viagem).count() == 0

    def test_posicao_velha_nao_confirma_embarque(self, db):
        # O ônibus estava ali há 10 min; já andou.
        r = _embarcar([_veiculo(idade_s=10 * 60)])
        assert r.status_code == 422
        assert db.query(Viagem).count() == 0

    def test_veiculo_de_outra_linha_nao_conta(self, db):
        """O feed é consultado SÓ pela linha informada."""
        chamadas = []

        async def feed(numero):
            chamadas.append(numero)
            return [_veiculo()] if numero == "OUTRA.LINHA" else []

        with patch("mobilidade.routes._posicao_service.posicoes_da_linha", feed):
            r = client.post(
                "/mobilidade/viagens",
                json={"numero_linha": LINHA, "lat": LAT_USUARIO, "lng": LNG_USUARIO},
                headers=_h(),
            )
        assert r.status_code == 422
        assert chamadas == [LINHA]

    def test_com_varios_veiculos_vale_o_mais_proximo(self, db):
        longe = _veiculo(prefixo="LONGE", deslocar_lat=0.0008)  # ~89 m
        perto = _veiculo(prefixo="PERTO", deslocar_lat=0.0002)  # ~22 m
        r = _embarcar([longe, perto])
        assert r.status_code == 201
        assert r.json()["veiculo_prefixo"] == "PERTO"

    def test_popup_de_onibus_longe_e_recusado_mesmo_com_outro_da_linha_perto(self, db):
        """Issue #216: o ônibus tocado está longe; outro da linha está ao lado."""
        longe = _veiculo(70, prefixo="TOCADO", deslocar_lat=0.0012)
        perto = _veiculo(prefixo="OUTRO")

        r = _embarcar([longe, perto], prefixo="TOCADO")

        assert r.status_code == 422
        assert db.query(Viagem).count() == 0

    def test_popup_do_onibus_perto_registra_esse_veiculo(self, db):
        perto = _veiculo(prefixo="TOCADO")

        r = _embarcar([_veiculo(prefixo="OUTRO", deslocar_lat=0.0004), perto], prefixo="TOCADO")

        assert r.status_code == 201
        assert r.json()["veiculo_prefixo"] == "TOCADO"

    def test_sem_prefixo_qualquer_onibus_da_linha_perto_vale(self, db):
        """Embarque pela rota (#190): continua como antes."""
        r = _embarcar([_veiculo(70, prefixo="LONGE"), _veiculo(prefixo="PERTO")])
        assert r.status_code == 201
        assert r.json()["veiculo_prefixo"] == "PERTO"

    def test_veiculo_sem_sentido_embarca_com_sentido_nulo(self, db):
        r = _embarcar([_veiculo(sentido=None)])
        assert r.status_code == 201
        assert r.json()["sentido"] is None

    def test_corpo_invalido_e_422_do_schema(self, db):
        r = client.post(
            "/mobilidade/viagens",
            json={"numero_linha": LINHA, "lat": 999, "lng": LNG_USUARIO},
            headers=_h(),
        )
        assert r.status_code == 422

    def test_numero_da_linha_em_branco_e_recusado(self, db):
        r = client.post(
            "/mobilidade/viagens",
            json={"numero_linha": "   ", "lat": LAT_USUARIO, "lng": LNG_USUARIO},
            headers=_h(),
        )
        assert r.status_code == 422


class TestUmaViagemPorUsuario:
    def test_cenario_5_ja_em_viagem_devolve_409_e_nao_muda_a_atual(self, db):
        primeira = _embarcar([_veiculo(prefixo="PRIMEIRO")]).json()
        segunda = _embarcar([_veiculo(prefixo="SEGUNDO")])

        assert segunda.status_code == 409
        assert db.query(Viagem).count() == 1
        assert db.query(Viagem).one().veiculo_prefixo == "PRIMEIRO"
        assert str(db.query(Viagem).one().id) == primeira["id"]

    def test_outro_usuario_embarca_normalmente(self, db):
        assert _embarcar([_veiculo()]).status_code == 201
        assert _embarcar([_veiculo()], usuario=OUTRO).status_code == 201
        assert db.query(Viagem).count() == 2

    def test_o_banco_recusa_duas_ativas_do_mesmo_usuario(self, db):
        _inserir_viagem(db)
        with pytest.raises(IntegrityError):
            _inserir_viagem(db)
        db.rollback()

    def test_o_banco_aceita_varias_encerradas_e_uma_ativa(self, db):
        _inserir_viagem(db, encerrada=True)
        _inserir_viagem(db, encerrada=True)
        _inserir_viagem(db)  # a ativa
        assert db.query(Viagem).count() == 3

    def test_corrida_dois_toques_simultaneos_viram_409_e_nao_500(self, db):
        """
        A checagem da aplicação passou nos dois (ninguém tinha ativa ainda),
        mas o índice único parcial só deixa o primeiro entrar.
        """
        _inserir_viagem(db)
        with patch.object(servico, "viagem_ativa", return_value=None):
            with pytest.raises(servico.JaEmViagem):
                servico.embarcar(
                    db,
                    usuario_id=PASSAGEIRO,
                    numero_linha=LINHA,
                    lat=LAT_USUARIO,
                    lng=LNG_USUARIO,
                    parada_destino_codigo=None,
                    veiculos=[_veiculo()],
                    agora=servico.agora_utc(),
                )
        assert db.query(Viagem).count() == 1

    def test_depois_de_encerrar_pode_embarcar_de_novo(self, db):
        id_ = _embarcar([_veiculo()]).json()["id"]
        with _feed([]):
            client.post(f"/mobilidade/viagens/{id_}/encerrar", headers=_h())
        assert _embarcar([_veiculo()]).status_code == 201


class TestDestino:
    def test_destino_valido_fica_salvo(self, db):
        r = _embarcar([_veiculo()], destino=COD["C"])
        assert r.status_code == 201
        assert r.json()["parada_destino_codigo"] == COD["C"]

    def test_destino_desconhecido_e_422(self, db):
        r = _embarcar([_veiculo()], destino="PR-NAOEXISTE")
        assert r.status_code == 422
        assert "não encontrada" in r.json()["detail"]
        assert db.query(Viagem).count() == 0

    def test_destino_que_nao_e_da_linha_e_422(self, db):
        r = _embarcar([_veiculo()], destino=COD_FORA)
        assert r.status_code == 422
        assert "não faz parte desta linha" in r.json()["detail"]
        assert db.query(Viagem).count() == 0

    def test_linha_sem_paradas_ingeridas_aceita_o_destino(self, db):
        """Sem as paradas da linha não há como dizer que o destino é errado."""
        r = _embarcar([_veiculo()], linha=LINHA_SEM_PARADAS, destino=COD["A"])
        assert r.status_code == 201

    def test_sem_destino_tambem_embarca(self, db):
        r = _embarcar([_veiculo()])
        assert r.status_code == 201
        assert r.json()["parada_destino_codigo"] is None


# ==========================================================================
# Encerrar (Cenário 3 e 7)
# ==========================================================================


class TestEncerrar:
    def _criar(self):
        return _embarcar([_veiculo()]).json()["id"]

    def test_cenario_3_encerra_e_volta_ao_estado_normal(self, db):
        id_ = self._criar()

        r = client.post(f"/mobilidade/viagens/{id_}/encerrar", headers=_h())

        assert r.status_code == 200
        assert r.json()["encerrada_em"] is not None
        assert r.json()["motivo_encerramento"] == "usuario"
        assert _ativa([]).json() == {
            "ativa": False, "viagem": None, "sinal": None, "veiculo": None,
            "destino": None, "proxima_parada": None, "paradas_restantes": [],
            "alerta_proximidade": None,
        }

    def test_cenario_7_encerrar_duas_vezes_nao_da_erro_e_nao_muda_o_horario(self, db):
        id_ = self._criar()
        primeira = client.post(f"/mobilidade/viagens/{id_}/encerrar", headers=_h())
        segunda = client.post(f"/mobilidade/viagens/{id_}/encerrar", headers=_h())

        assert segunda.status_code == 200
        assert segunda.json()["encerrada_em"] == primeira.json()["encerrada_em"]

    def test_viagem_de_outro_usuario_e_404_e_continua_ativa(self, db):
        id_ = self._criar()

        r = client.post(f"/mobilidade/viagens/{id_}/encerrar", headers=_h(OUTRO))

        assert r.status_code == 404
        assert db.query(Viagem).one().encerrada_em is None

    def test_id_inexistente_e_404(self, db):
        r = client.post(f"/mobilidade/viagens/{uuid.uuid4()}/encerrar", headers=_h())
        assert r.status_code == 404

    def test_id_que_nao_e_uuid_e_422(self, db):
        r = client.post("/mobilidade/viagens/abc/encerrar", headers=_h())
        assert r.status_code == 422

    def test_sem_identidade_e_401(self, db):
        r = client.post(f"/mobilidade/viagens/{uuid.uuid4()}/encerrar")
        assert r.status_code == 401


# ==========================================================================
# Escolher o destino depois de embarcar
# ==========================================================================


def _destino(corpo, viagem_id, usuario=PASSAGEIRO):
    return client.put(
        f"/mobilidade/viagens/{viagem_id}/destino", json=corpo, headers=_h(usuario)
    )


class TestDefinirDestino:
    def _criar(self, destino=None):
        return _embarcar([_veiculo()], destino=destino).json()["id"]

    def test_escolhe_o_destino_depois_de_embarcar(self, db):
        id_ = self._criar()

        r = _destino({"parada_destino_codigo": COD["C"]}, id_)

        assert r.status_code == 200
        assert r.json()["parada_destino_codigo"] == COD["C"]
        db.expire_all()
        assert db.query(Viagem).one().parada_destino_codigo == COD["C"]

    def test_troca_o_destino(self, db):
        id_ = self._criar(destino=COD["B"])
        assert _destino({"parada_destino_codigo": COD["C"]}, id_).json()[
            "parada_destino_codigo"
        ] == COD["C"]

    def test_null_tira_o_destino(self, db):
        id_ = self._criar(destino=COD["B"])

        r = _destino({"parada_destino_codigo": None}, id_)

        assert r.status_code == 200
        assert r.json()["parada_destino_codigo"] is None

    def test_o_novo_destino_aparece_no_acompanhamento(self, db):
        id_ = self._criar()
        _destino({"parada_destino_codigo": COD["C"]}, id_)

        corpo = _ativa([_veiculo(indice=60)]).json()

        assert corpo["destino"]["codigo"] == COD["C"]
        assert [p["codigo"] for p in corpo["paradas_restantes"]] == [COD["B"], COD["C"]]

    def test_o_novo_destino_entra_no_alerta_da_172(self, db):
        id_ = self._criar()
        assert ViagensAtivasDoBanco().listar_ativas() == []

        _destino({"parada_destino_codigo": COD["C"]}, id_)

        assert [a.parada_destino_codigo for a in ViagensAtivasDoBanco().listar_ativas()] == [
            COD["C"]
        ]

    def test_parada_desconhecida_e_422_e_nao_muda_nada(self, db):
        id_ = self._criar(destino=COD["B"])

        r = _destino({"parada_destino_codigo": "PR-NAOEXISTE"}, id_)

        assert r.status_code == 422
        db.expire_all()
        assert db.query(Viagem).one().parada_destino_codigo == COD["B"]

    def test_parada_de_outra_linha_e_422(self, db):
        id_ = self._criar()
        r = _destino({"parada_destino_codigo": COD_FORA}, id_)
        assert r.status_code == 422
        assert "não faz parte desta linha" in r.json()["detail"]

    def test_viagem_encerrada_nao_muda_de_destino(self, db):
        id_ = self._criar()
        client.post(f"/mobilidade/viagens/{id_}/encerrar", headers=_h())

        r = _destino({"parada_destino_codigo": COD["C"]}, id_)

        assert r.status_code == 409
        db.expire_all()
        assert db.query(Viagem).one().parada_destino_codigo is None

    def test_viagem_expirada_nao_muda_de_destino(self, db):
        viagem = _inserir_viagem(db, embarcou_ha=timedelta(hours=6))
        assert _destino({"parada_destino_codigo": COD["C"]}, viagem.id).status_code == 409

    def test_viagem_de_outro_usuario_e_404_e_nao_muda(self, db):
        id_ = self._criar(destino=COD["B"])

        r = _destino({"parada_destino_codigo": COD["C"]}, id_, usuario=OUTRO)

        assert r.status_code == 404
        db.expire_all()
        assert db.query(Viagem).one().parada_destino_codigo == COD["B"]

    def test_id_inexistente_e_404(self, db):
        assert _destino({"parada_destino_codigo": COD["C"]}, uuid.uuid4()).status_code == 404

    def test_sem_identidade_e_401(self, db):
        r = client.put(
            f"/mobilidade/viagens/{uuid.uuid4()}/destino",
            json={"parada_destino_codigo": COD["C"]},
        )
        assert r.status_code == 401

    def test_codigo_vazio_e_422_do_schema(self, db):
        id_ = self._criar()
        assert _destino({"parada_destino_codigo": ""}, id_).status_code == 422


# ==========================================================================
# Expiração (Cenário 6)
# ==========================================================================


class TestExpiracao:
    def test_cenario_6_viagem_esquecida_expira(self, db):
        esquecida = _inserir_viagem(db, embarcou_ha=timedelta(hours=5))
        embarcou = esquecida.embarcou_em

        r = _ativa([])

        assert r.json()["ativa"] is False
        db.expire_all()
        salva = db.query(Viagem).one()
        assert salva.motivo_encerramento == "expirada"
        # Encerrada quando venceu, não quando alguém olhou.
        assert salva.encerrada_em == embarcou + servico.DURACAO_MAXIMA_VIAGEM

    def test_viagem_dentro_do_prazo_continua_ativa(self, db):
        _inserir_viagem(db, embarcou_ha=timedelta(hours=3, minutes=50))
        assert _ativa([]).json()["ativa"] is True

    def test_depois_de_expirar_pode_embarcar(self, db):
        _inserir_viagem(db, embarcou_ha=timedelta(hours=6))
        assert _embarcar([_veiculo()]).status_code == 201
        db.expire_all()
        assert db.query(Viagem).filter(Viagem.encerrada_em.is_(None)).count() == 1

    def test_expirar_so_mexe_nas_vencidas_do_usuario_pedido(self, db):
        _inserir_viagem(db, usuario=PASSAGEIRO, embarcou_ha=timedelta(hours=6))
        _inserir_viagem(db, usuario=OUTRO, embarcou_ha=timedelta(hours=6))

        servico.expirar_vencidas(db, servico.agora_utc(), usuario_id=PASSAGEIRO)

        db.expire_all()
        assert db.query(Viagem).filter(Viagem.usuario_id == PASSAGEIRO).one().encerrada_em
        assert db.query(Viagem).filter(Viagem.usuario_id == OUTRO).one().encerrada_em is None


# ==========================================================================
# Acompanhamento (Cenário 2)
# ==========================================================================


class TestAcompanhamento:
    def test_sem_viagem_diz_que_nao_ha(self, db):
        assert _ativa([_veiculo()]).json()["ativa"] is False

    def test_cenario_2_mostra_veiculo_proxima_parada_e_restantes_ate_o_destino(self, db):
        # Ônibus entre A (40) e B (100); o passageiro vai descer em C (160).
        _inserir_viagem(db, destino=COD["C"])

        corpo = _ativa([_veiculo(indice=60)]).json()

        assert corpo["ativa"] is True
        assert corpo["sinal"] == "ao_vivo"
        assert corpo["veiculo"]["prefixo"] == "440001"
        assert corpo["proxima_parada"]["codigo"] == COD["B"]
        assert [p["codigo"] for p in corpo["paradas_restantes"]] == [COD["B"], COD["C"]]
        assert corpo["destino"]["codigo"] == COD["C"]
        assert corpo["destino"]["ultrapassado"] is False

    def test_as_restantes_param_no_destino_e_nao_vao_ate_o_fim_da_linha(self, db):
        _inserir_viagem(db, destino=COD["B"])
        corpo = _ativa([_veiculo(indice=60)]).json()
        assert [p["codigo"] for p in corpo["paradas_restantes"]] == [COD["B"]]

    def test_parada_ja_passada_nao_aparece(self, db):
        _inserir_viagem(db, destino=COD["C"])
        corpo = _ativa([_veiculo(indice=120)]).json()  # já passou de A e B
        assert corpo["proxima_parada"]["codigo"] == COD["C"]
        assert [p["codigo"] for p in corpo["paradas_restantes"]] == [COD["C"]]

    def test_onibus_em_cima_da_parada_ainda_a_tem_como_proxima(self, db):
        # Metros = 0 não é "já passou": a parada onde o ônibus está parado
        # ainda é a próxima (e vale a mesma tolerância do ETA).
        _inserir_viagem(db, destino=COD["C"])
        em_cima = _ativa([_veiculo(indice=100)]).json()
        assert em_cima["proxima_parada"]["codigo"] == COD["B"]

    def test_parada_logo_atras_do_onibus_ainda_conta_como_chegando(self, db):
        # Mesma tolerância do ETA (50 m), para as duas telas não se
        # contradizerem. Ônibus ~21 m depois de B.
        _inserir_viagem(db, destino=COD["C"])
        _, lng = TRAJETO[100]
        logo_depois = replace(_veiculo(indice=100), lng=lng + 0.0002)
        corpo = _ativa([logo_depois]).json()
        assert corpo["proxima_parada"]["codigo"] == COD["B"]

    def test_destino_ultrapassado_avisa_e_zera_as_restantes(self, db):
        _inserir_viagem(db, destino=COD["A"])  # desceria em A...
        corpo = _ativa([_veiculo(indice=120)]).json()  # ...mas o ônibus já está depois de B

        assert corpo["destino"]["ultrapassado"] is True
        assert corpo["paradas_restantes"] == []
        # A próxima parada segue sendo informada.
        assert corpo["proxima_parada"]["codigo"] == COD["C"]

    def test_sem_destino_mostra_so_a_proxima_parada(self, db):
        _inserir_viagem(db, destino=None)
        corpo = _ativa([_veiculo(indice=60)]).json()
        assert corpo["proxima_parada"]["codigo"] == COD["B"]
        assert corpo["paradas_restantes"] == []
        assert corpo["destino"] is None

    def test_onibus_fora_do_feed_e_sem_sinal_e_sem_chute(self, db):
        _inserir_viagem(db, destino=COD["C"])
        corpo = _ativa([]).json()

        assert corpo["ativa"] is True
        assert corpo["sinal"] == "sem_sinal"
        assert corpo["veiculo"] is None
        assert corpo["proxima_parada"] is None
        assert corpo["paradas_restantes"] == []
        assert corpo["destino"]["codigo"] == COD["C"]

    def test_outro_onibus_da_linha_nao_e_o_meu(self, db):
        _inserir_viagem(db, prefixo="MEU")
        corpo = _ativa([_veiculo(prefixo="OUTRO")]).json()
        assert corpo["sinal"] == "sem_sinal"
        assert corpo["veiculo"] is None

    def test_posicao_velha_mostra_o_veiculo_mas_nao_chuta_a_proxima_parada(self, db):
        _inserir_viagem(db, destino=COD["C"])
        corpo = _ativa([_veiculo(indice=60, idade_s=10 * 60)]).json()

        assert corpo["sinal"] == "sem_sinal"
        assert corpo["veiculo"]["prefixo"] == "440001"
        assert corpo["proxima_parada"] is None

    def test_sentido_do_veiculo_sem_rota_ingerida_nao_chuta(self, db):
        # O veículo diz VOLTA; só há rota IDA (e não é circular).
        _inserir_viagem(db, sentido="VOLTA")
        corpo = _ativa([_veiculo(indice=60, sentido="VOLTA")]).json()
        assert corpo["sinal"] == "ao_vivo"
        assert corpo["proxima_parada"] is None

    def test_veiculo_sem_sentido_em_linha_nao_circular_nao_chuta(self, db):
        _inserir_viagem(db, sentido=None)
        corpo = _ativa([_veiculo(indice=60, sentido=None)]).json()
        assert corpo["sinal"] == "ao_vivo"
        assert corpo["proxima_parada"] is None

    def test_veiculo_longe_do_tracado_nao_chuta(self, db):
        _inserir_viagem(db)
        corpo = _ativa([_veiculo(indice=60, deslocar_lat=0.01)]).json()  # ~1,1 km fora
        assert corpo["proxima_parada"] is None

    def test_o_sentido_de_agora_do_veiculo_vale_mais_que_o_do_embarque(self, db):
        _inserir_viagem(db, sentido="VOLTA")  # embarcou como VOLTA...
        corpo = _ativa([_veiculo(indice=60, sentido="IDA")]).json()  # ...mas agora é IDA
        assert corpo["proxima_parada"]["codigo"] == COD["B"]

    def test_linha_circular_o_veiculo_nunca_diz_circular_e_ainda_assim_acha_a_rota(self, db):
        _inserir_viagem(db, linha=LINHA_CIRCULAR, sentido="IDA")
        corpo = _ativa([_veiculo(indice=60, sentido="IDA")]).json()
        assert corpo["proxima_parada"]["codigo"] == COD["B"]

    def test_linha_circular_depois_da_ultima_parada_da_a_volta(self, db):
        # Circular com A (40) e B (100); o ônibus está depois de B (130).
        _inserir_viagem(db, linha=LINHA_CIRCULAR, sentido=None, destino=COD["A"])
        corpo = _ativa([_veiculo(indice=130, sentido=None)]).json()

        assert corpo["proxima_parada"]["codigo"] == COD["A"]
        assert [p["codigo"] for p in corpo["paradas_restantes"]] == [COD["A"]]
        assert corpo["destino"]["ultrapassado"] is False

    def test_destino_que_sumiu_da_tabela_parada_nao_derruba_a_tela(self, db):
        _inserir_viagem(db, destino="PR-V171SUMIU")
        corpo = _ativa([_veiculo(indice=60)]).json()
        assert corpo["ativa"] is True
        assert corpo["destino"] is None
        assert corpo["proxima_parada"]["codigo"] == COD["B"]


# ==========================================================================
# Regras puras
# ==========================================================================


class _RotaDensa:
    """RotaService de mentira: um trajeto com um vértice a cada ~21 m."""

    def __init__(self, medido):
        self._medido = medido

    def trajeto_medido(self, db, numero, sentido=None):
        return (self._medido, sentido) if sentido == "IDA" else None


class TestToleranciaDaParada:
    """
    O trajeto sintético tem vértices a ~107 m, mais que os 50 m de tolerância,
    então a tolerância só aparece num trajeto denso — como os reais.
    """

    INDICE_PARADA = 500

    @pytest.fixture
    def denso(self, db):
        passo = 0.0002  # ~21 m de longitude
        lat, lng0 = TRAJETO[0]
        pontos = [(lat, lng0 + passo * i) for i in range(1000)]
        medido = TrajetoMedido(pontos)
        parada = Parada(codigo="PR-V171D", nome="Parada D", lat=pontos[500][0], lng=pontos[500][1])
        db.add(parada)
        db.flush()
        db.add(
            RotaParada(
                numero=LINHA_DENSA, sentido="IDA", parada_id=parada.id, ordem=0,
                indice_trajeto=self.INDICE_PARADA,
                distancia_acumulada_m=medido.acumulado[self.INDICE_PARADA],
                distancia_ao_trajeto_m=1.0,
            )
        )
        db.commit()
        return medido, pontos

    def _proxima(self, db, denso, indice_veiculo):
        medido, pontos = denso
        lat, lng = pontos[indice_veiculo]
        viagem = Viagem(
            usuario_id=PASSAGEIRO, numero_linha=LINHA_DENSA, sentido="IDA",
            veiculo_prefixo="440001", embarcou_em=servico.agora_utc(),
        )
        veiculo = replace(_veiculo(), lat=lat, lng=lng)
        progresso = servico.progresso_da_viagem(
            db, viagem, [veiculo], _RotaDensa(medido), datetime.now(timezone.utc)
        )
        return progresso.proxima_parada

    def test_parada_a_menos_de_50_m_atras_ainda_e_a_proxima(self, db, denso):
        # 2 vértices depois da parada = ~42 m.
        assert self._proxima(db, denso, self.INDICE_PARADA + 2).codigo == "PR-V171D"

    def test_parada_a_mais_de_50_m_atras_ja_passou(self, db, denso):
        # 3 vértices depois = ~64 m.
        assert self._proxima(db, denso, self.INDICE_PARADA + 3) is None

    def test_parada_a_frente_e_a_proxima(self, db, denso):
        assert self._proxima(db, denso, self.INDICE_PARADA - 40).codigo == "PR-V171D"


class TestVeiculoMaisProximo:
    def test_raio_e_o_da_decisao_d2(self):
        assert servico.RAIO_EMBARQUE_M == 100.0

    def test_na_borda_do_raio(self):
        agora = datetime.now(timezone.utc)
        lat, lng = TRAJETO[100]
        # ~99 m → dentro; ~111 m → fora.
        dentro = _veiculo(100, deslocar_lat=0.00089)
        fora = _veiculo(100, deslocar_lat=0.0010)
        assert distancia_metros(lat, lng, dentro.lat, dentro.lng) <= 100
        assert distancia_metros(lat, lng, fora.lat, fora.lng) > 100
        assert servico.veiculo_mais_proximo([dentro], lat, lng, agora) is dentro
        assert servico.veiculo_mais_proximo([fora], lat, lng, agora) is None

    def test_lista_vazia(self):
        assert servico.veiculo_mais_proximo([], 0.0, 0.0, datetime.now(timezone.utc)) is None


# ==========================================================================
# Raio de embarque configurável (issue #190)
# ==========================================================================


class TestRaioConfiguravel:
    def test_sem_variavel_usa_o_padrao(self, monkeypatch):
        monkeypatch.delenv("RAIO_EMBARQUE_M", raising=False)
        assert servico._limite_do_ambiente("RAIO_EMBARQUE_M", 100.0) == 100.0

    @pytest.mark.parametrize("bruto", ["", "   "])
    def test_em_branco_usa_o_padrao_sem_aviso(self, monkeypatch, caplog, bruto):
        monkeypatch.setenv("RAIO_EMBARQUE_M", bruto)
        with caplog.at_level(logging.WARNING, logger=servico.logger.name):
            assert servico._limite_do_ambiente("RAIO_EMBARQUE_M", 100.0) == 100.0
        assert caplog.records == []

    @pytest.mark.parametrize("bruto, esperado", [("250", 250.0), ("250.5", 250.5), (" 80 ", 80.0)])
    def test_valor_valido_e_usado(self, monkeypatch, bruto, esperado):
        monkeypatch.setenv("RAIO_EMBARQUE_M", bruto)
        assert servico._limite_do_ambiente("RAIO_EMBARQUE_M", 100.0) == esperado

    @pytest.mark.parametrize("bruto", ["abc", "0", "-5", "-0.1", "nan", "inf", "-inf", "12m"])
    def test_valor_invalido_cai_no_padrao_e_avisa(self, monkeypatch, caplog, bruto):
        monkeypatch.setenv("RAIO_EMBARQUE_M", bruto)
        with caplog.at_level(logging.WARNING, logger=servico.logger.name):
            assert servico._limite_do_ambiente("RAIO_EMBARQUE_M", 100.0) == 100.0
        assert any("RAIO_EMBARQUE_M" in r.getMessage() for r in caplog.records)

    def test_a_variavel_e_lida_quando_o_modulo_carrega(self):
        """Ponta a ponta: um processo novo com a variável vê o valor novo."""
        backend = Path(__file__).resolve().parents[2]
        codigo = "import mobilidade.viagem_service as s; print(s.RAIO_EMBARQUE_M)"
        for valor, esperado in (("250", "250.0"), ("lixo", "100.0"), (None, "100.0")):
            ambiente = {k: v for k, v in os.environ.items() if k != "RAIO_EMBARQUE_M"}
            if valor is not None:
                ambiente["RAIO_EMBARQUE_M"] = valor
            saida = subprocess.run(
                [sys.executable, "-c", codigo],
                cwd=backend,
                env=ambiente,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert saida.returncode == 0, saida.stderr
            assert saida.stdout.strip().splitlines()[-1] == esperado

    def test_raio_maior_aceita_o_embarque_na_linha_sem_paradas(self, db, monkeypatch):
        """
        Linha sem paradas ingeridas: só o raio decide (o "ônibus chegando"
        não se aplica). ~167 m recusa com 100 m e aceita com 200 m.
        """
        longe = _veiculo(deslocar_lat=0.0015)
        assert _embarcar([longe], linha=LINHA_SEM_PARADAS).status_code == 422

        monkeypatch.setattr(servico, "RAIO_EMBARQUE_M", 200.0)
        assert _embarcar([longe], linha=LINHA_SEM_PARADAS).status_code == 201

    def test_raio_menor_recusa_o_que_antes_aceitava(self, db, monkeypatch):
        monkeypatch.setattr(servico, "RAIO_EMBARQUE_M", 50.0)
        # ~78 m: dentro de 100 m, fora de 50 m.
        r = _embarcar([_veiculo(deslocar_lat=0.0007)], linha=LINHA_SEM_PARADAS)
        assert r.status_code == 422


# ==========================================================================
# Embarque com o ônibus chegando na parada do usuário (issue #190)
# A VALIDAR EM CAMPO: os limites de 400 m e 2 min são propostas.
# ==========================================================================


def _onibus(indice, *, velocidade=30.0, **kw):
    return replace(_veiculo(indice, **kw), velocidade=velocidade)


def _eta_para_b(veiculo):
    """ETA do veículo até a parada B (onde o passageiro está), no momento."""
    return eta_ate_indice(veiculo, MEDIDO, IDX["B"], "IDA", datetime.now(timezone.utc))


class TestEmbarqueComOnibusChegando:
    def test_aceita_quando_chega_dentro_do_limite_mesmo_fora_do_raio(self, db):
        # 8 vértices (~860 m) antes da parada B, a 30 km/h: ~1,7 min.
        chegando = _onibus(92, prefixo="CHEGANDO")
        lat, lng = TRAJETO[IDX["B"]]
        assert distancia_metros(lat, lng, chegando.lat, chegando.lng) > servico.RAIO_EMBARQUE_M
        assert _eta_para_b(chegando) <= servico.ETA_MAXIMO_EMBARQUE_MIN

        r = _embarcar([chegando])

        assert r.status_code == 201
        assert r.json()["veiculo_prefixo"] == "CHEGANDO"
        assert r.json()["sentido"] == "IDA"
        assert db.query(Viagem).one().origem_embarque == "manual"

    def test_recusa_quando_o_eta_passa_do_limite(self, db):
        # 20 vértices (~2,1 km) antes: ~4 min.
        devagar = _onibus(80)
        assert _eta_para_b(devagar) > servico.ETA_MAXIMO_EMBARQUE_MIN

        r = _embarcar([devagar])

        assert r.status_code == 422
        assert "não conseguimos confirmar" in r.json()["detail"].lower()
        assert db.query(Viagem).count() == 0

    def test_popup_de_onibus_longe_nao_herda_o_onibus_que_esta_chegando(self, db):
        """
        Issue #216: o usuário espera na parada B e OUTRO ônibus da linha está
        chegando (ETA dentro do limite). Tocar no popup do ônibus distante
        (carro 124931, a dezenas de km) não pode registrar embarque.
        """
        chegando = _onibus(92, prefixo="CHEGANDO")
        distante = _onibus(0, prefixo="124931")
        assert _eta_para_b(chegando) <= servico.ETA_MAXIMO_EMBARQUE_MIN

        r = _embarcar([distante, chegando], prefixo="124931")

        assert r.status_code == 422
        assert "não conseguimos confirmar" in r.json()["detail"].lower()
        assert db.query(Viagem).count() == 0

    def test_popup_do_onibus_que_esta_chegando_registra_esse_veiculo(self, db):
        chegando = _onibus(92, prefixo="CHEGANDO")
        outro = _onibus(0, prefixo="124931")

        r = _embarcar([outro, chegando], prefixo="CHEGANDO")

        assert r.status_code == 201
        assert r.json()["veiculo_prefixo"] == "CHEGANDO"

    def test_o_limite_de_tempo_e_inclusivo_e_configuravel(self, db, monkeypatch):
        onibus = _onibus(92)
        eta = _eta_para_b(onibus)

        monkeypatch.setattr(servico, "ETA_MAXIMO_EMBARQUE_MIN", eta + 0.3)
        assert _embarcar([onibus]).status_code == 201
        db.query(Viagem).delete()
        db.commit()

        monkeypatch.setattr(servico, "ETA_MAXIMO_EMBARQUE_MIN", eta - 0.3)
        assert _embarcar([onibus]).status_code == 422

    def test_sentido_oposto_nao_conta(self, db):
        r = _embarcar([_onibus(92, sentido="VOLTA")])
        assert r.status_code == 422

    def test_onibus_que_ja_passou_da_parada_nao_conta(self, db):
        # 8 vértices depois da parada B: já passou, não volta.
        passou = _onibus(108)
        assert _eta_para_b(passou) is None
        assert _embarcar([passou]).status_code == 422

    def test_onibus_parado_nao_tem_eta_e_nao_confirma(self, db):
        assert _embarcar([_onibus(92, velocidade=0.0)]).status_code == 422

    def test_posicao_velha_nao_confirma(self, db):
        assert _embarcar([_onibus(92, idade_s=10 * 60)]).status_code == 422

    def test_sem_paradas_ingeridas_so_vale_o_raio(self, db):
        r = _embarcar([_onibus(92)], linha=LINHA_SEM_PARADAS)
        assert r.status_code == 422

    def test_sem_parada_da_linha_perto_do_usuario_nao_vale(self, db):
        # O passageiro está ~1 km depois da parada B (nenhuma parada a 400 m)
        # e o ônibus está 8 vértices antes DELE — que seria ~1,7 min.
        lat, lng = TRAJETO[IDX["B"] + 10]
        r = _embarcar([_onibus(IDX["B"] + 2)], lat=lat, lng=lng)
        assert r.status_code == 422

    def test_com_varios_vale_o_de_menor_eta(self, db):
        lento = _onibus(85, prefixo="LENTO")  # ~3 min: fora do limite
        medio = _onibus(92, prefixo="MEDIO")  # ~1,7 min
        rapido = _onibus(95, prefixo="RAPIDO")  # ~1,2 min
        r = _embarcar([lento, medio, rapido])
        assert r.status_code == 201
        assert r.json()["veiculo_prefixo"] == "RAPIDO"

    def test_linha_circular_aceita_veiculo_que_reporta_ida(self, db):
        """O veículo de linha circular nunca reporta 'CIRCULAR' (feed real)."""
        r = _embarcar([_onibus(92, prefixo="CIRC")], linha=LINHA_CIRCULAR)
        assert r.status_code == 201
        assert r.json()["veiculo_prefixo"] == "CIRC"

    def test_destino_invalido_continua_recusando_antes_do_veiculo(self, db):
        r = _embarcar([_onibus(92)], destino="PR-NAOEXISTE")
        assert r.status_code == 422
        assert "parada de destino" in r.json()["detail"].lower()
        assert db.query(Viagem).count() == 0

    def test_destino_valido_e_gravado_no_embarque_chegando(self, db):
        r = _embarcar([_onibus(92)], destino=COD["C"])
        assert r.status_code == 201
        assert r.json()["parada_destino_codigo"] == COD["C"]


class TestEmbarqueChegandoNoServico:
    def test_a_regra_do_raio_vem_primeiro_e_nao_consulta_a_rota(self, db):
        rota = MagicMock()
        viagem = servico.embarcar(
            db,
            usuario_id=PASSAGEIRO,
            numero_linha=LINHA,
            lat=LAT_USUARIO,
            lng=LNG_USUARIO,
            parada_destino_codigo=None,
            veiculos=[_veiculo()],
            agora=servico.agora_utc(),
            rota_service=rota,
        )
        assert viagem.veiculo_prefixo == "440001"
        rota.trajeto_medido.assert_not_called()

    def test_sem_rota_service_o_comportamento_e_o_de_antes(self, db):
        with pytest.raises(servico.SemVeiculoProximo):
            servico.embarcar(
                db,
                usuario_id=PASSAGEIRO,
                numero_linha=LINHA,
                lat=LAT_USUARIO,
                lng=LNG_USUARIO,
                parada_destino_codigo=None,
                veiculos=[_onibus(92)],
                agora=servico.agora_utc(),
            )
        assert db.query(Viagem).count() == 0

    def test_sem_trajeto_nao_inventa(self, db):
        rota = MagicMock()
        rota.trajeto_medido.return_value = None
        achado = servico.veiculo_chegando_na_parada_do_usuario(
            db, rota, LINHA, [_onibus(92)], LAT_USUARIO, LNG_USUARIO, datetime.now(timezone.utc)
        )
        assert achado is None
        rota.trajeto_medido.assert_called_once_with(db, LINHA, "IDA")

    def test_sem_veiculos_devolve_none(self, db):
        achado = servico.veiculo_chegando_na_parada_do_usuario(
            db, MagicMock(), LINHA, [], LAT_USUARIO, LNG_USUARIO, datetime.now(timezone.utc)
        )
        assert achado is None

    def test_o_raio_da_parada_e_configuravel(self, db, monkeypatch):
        """Com o raio da parada em 1 m, o usuário (em cima da parada) ainda vale;
        deslocado ~110 m, deixa de valer."""
        monkeypatch.setattr(servico, "RAIO_PARADA_EMBARQUE_M", 50.0)
        rota = MagicMock()
        rota.trajeto_medido.return_value = (MEDIDO, "IDA")
        agora = datetime.now(timezone.utc)

        em_cima = servico.veiculo_chegando_na_parada_do_usuario(
            db, rota, LINHA, [_onibus(92)], LAT_USUARIO, LNG_USUARIO, agora
        )
        assert em_cima is not None

        deslocado = servico.veiculo_chegando_na_parada_do_usuario(
            db, rota, LINHA, [_onibus(92)], LAT_USUARIO + 0.001, LNG_USUARIO, agora
        )
        assert deslocado is None


# ==========================================================================
# Integração com a #172 (provider real)
# ==========================================================================


class TestProviderDaProximidade:
    def test_devolve_a_viagem_com_o_destino_resolvido(self, db):
        viagem = _inserir_viagem(db, destino=COD["C"])

        ativas = ViagensAtivasDoBanco().listar_ativas()

        assert len(ativas) == 1
        a = ativas[0]
        assert a.viagem_id == str(viagem.id)
        assert a.usuario_id == PASSAGEIRO
        assert a.numero_linha == LINHA
        assert a.parada_destino_codigo == COD["C"]
        assert (a.parada_destino_lat, a.parada_destino_lng) == TRAJETO[IDX["C"]]
        assert a.parada_destino_nome == "Parada C"
        # O alerta da #172 acompanha o ônibus da viagem, não o mais próximo.
        assert a.veiculo_prefixo == "440001"
        assert a.sentido == "IDA"

    def test_viagem_sem_destino_nao_entra(self, db):
        _inserir_viagem(db, destino=None)
        assert ViagensAtivasDoBanco().listar_ativas() == []

    def test_viagem_encerrada_nao_entra(self, db):
        _inserir_viagem(db, destino=COD["C"], encerrada=True)
        assert ViagensAtivasDoBanco().listar_ativas() == []

    def test_destino_que_sumiu_da_tabela_nao_entra(self, db):
        _inserir_viagem(db, destino="PR-V171SUMIU")
        assert ViagensAtivasDoBanco().listar_ativas() == []

    def test_viagem_vencida_nao_gera_alerta(self, db):
        _inserir_viagem(db, destino=COD["C"], embarcou_ha=timedelta(hours=6))
        assert ViagensAtivasDoBanco().listar_ativas() == []
        db.expire_all()
        assert db.query(Viagem).one().motivo_encerramento == "expirada"

    def test_varias_viagens_de_usuarios_diferentes(self, db):
        _inserir_viagem(db, usuario=PASSAGEIRO, destino=COD["B"])
        _inserir_viagem(db, usuario=OUTRO, destino=COD["C"])
        ativas = ViagensAtivasDoBanco().listar_ativas()
        assert {a.usuario_id for a in ativas} == {PASSAGEIRO, OUTRO}

    def test_banco_fora_vira_lista_vazia_e_nunca_excecao(self):
        def quebrada():
            raise RuntimeError("banco fora do ar")

        assert ViagensAtivasDoBanco(sessao_factory=quebrada).listar_ativas() == []

    def test_falha_na_consulta_vira_lista_vazia(self, db):
        class _Sessao:
            fechada = False

            def query(self, *a, **k):
                raise RuntimeError("tabela ausente")

            def close(self):
                _Sessao.fechada = True

        assert ViagensAtivasDoBanco(sessao_factory=_Sessao).listar_ativas() == []
        assert _Sessao.fechada is True  # a sessão não vaza

    def test_ciclo_completo_da_172_dispara_para_viagem_real(self, db):
        """Viagem criada pela API → worker de proximidade → alerta gravado."""
        from mobilidade.models.alerta_proximidade import AlertaProximidade
        from mobilidade.providers.contratos_proximidade import PreferenciasDeNotificacao
        from mobilidade.providers.eta_destino_trajeto import EtaDoDestinoPorTrajeto
        from mobilidade.services.servico_notificacoes import NotificadorMock
        from mobilidade.services.servico_proximidade import EVENTO_DISPARADO, ServicoProximidade

        class _Veiculos:
            def obter_das_linhas(self, numeros):
                # O ônibus da viagem, ~107 m antes do destino: ETA de segundos.
                return {n: [_veiculo(indice=IDX["C"] - 1, prefixo="440001")] for n in numeros}

        class _Prefs:
            def obter(self, usuario_id, db):
                return PreferenciasDeNotificacao()

        _embarcar([_veiculo(prefixo="440001")], destino=COD["C"])

        try:
            eventos = ServicoProximidade(
                viagens=ViagensAtivasDoBanco(),
                veiculos=_Veiculos(),
                preferencias=_Prefs(),
                notificador=NotificadorMock(),
                eta=EtaDoDestinoPorTrajeto(RotaService()),
            ).verificar_proximidades(db)

            assert EVENTO_DISPARADO in eventos
            alerta = db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).one()
            assert alerta.parada_destino_codigo == COD["C"]
            assert alerta.viagem_id == str(db.query(Viagem).one().id)
        finally:
            db.query(AlertaProximidade).filter_by(usuario_id=PASSAGEIRO).delete()
            db.commit()


# ==========================================================================
# Fiação
# ==========================================================================


def test_o_main_nao_usa_mais_o_provider_provisorio():
    import inspect as _inspect

    import mobilidade.main as principal

    fonte = _inspect.getsource(principal)
    assert "ViagensAtivasDoBanco()" in fonte
    assert "ViagensAtivasProvisorias()" not in fonte


def test_rotas_estao_registradas_sob_mobilidade():
    # O FastAPI desta versão embrulha routers incluídos; o OpenAPI é a fonte
    # estável do que de fato está publicado.
    paths = client.get("/openapi.json").json()["paths"]
    assert "post" in paths["/mobilidade/viagens"]
    assert "post" in paths["/mobilidade/viagens/{viagem_id}/encerrar"]
    assert "put" in paths["/mobilidade/viagens/{viagem_id}/destino"]
    assert "get" in paths["/mobilidade/viagens/ativa"]
