"""
Chegadas numa parada física (card #179, ⑤b) e "minha parada" da pílula.

Usa o trajeto sintético de test_rota_service.py (linha reta leste-oeste, um
ponto a cada ~110 m) e semeia `Parada`/`RotaParada` à mão, para que cada
asserção possa ser conferida na mão: onde o ônibus está, onde a parada está,
quantos metros há entre os dois.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mobilidade.chegada_service import (
    EMPATE_ENTRE_SENTIDOS_M,
    ETA_PREVISTO_MAXIMO_MIN,
    passagem_prevista,
    paradas_proximas_do_usuario,
)
from mobilidade.geometria import TrajetoMedido
from mobilidade.main import app
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.posicao_service import FUSO_SEMOB, PosicaoVeiculo
from mobilidade.tests.test_rota_service import PREFIXO, _semear, _trajeto
from shared.database import SessionLocal

client = TestClient(app)

TRAJETO = _trajeto()
MEDIDO = TrajetoMedido(TRAJETO)
INDICE_PARADA = 100
LINHA_A = f"{PREFIXO}A01"
LINHA_B = f"{PREFIXO}B02"
CODIGO = "PR-T179"
CODIGO_VOLTA = "PR-T180"

TODOS_OS_DIAS = {str(d): [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)] for d in range(7)}


# --------------------------------------------------------------------------
# semeadura
# --------------------------------------------------------------------------


def _limpar(db) -> None:
    for numero in (LINHA_A, LINHA_B):
        db.query(RotaParada).filter(RotaParada.numero == numero).delete(synchronize_session=False)
        db.query(RotaCelula).filter(RotaCelula.numero == numero).delete(synchronize_session=False)
        db.query(Rota).filter(Rota.numero == numero).delete(synchronize_session=False)
    db.query(Parada).filter(Parada.codigo.in_([CODIGO, CODIGO_VOLTA])).delete(synchronize_session=False)
    db.commit()


def _parada(db, codigo, indice, nome="Parada de teste") -> Parada:
    lat, lng = TRAJETO[indice]
    parada = Parada(codigo=codigo, nome=nome, lat=lat, lng=lng)
    db.add(parada)
    db.flush()
    return parada


def _vincular(db, parada, numero, sentido="IDA", indice=INDICE_PARADA, distancia_ao_trajeto=2.0):
    db.add(
        RotaParada(
            numero=numero,
            sentido=sentido,
            parada_id=parada.id,
            ordem=indice // 20,
            indice_trajeto=indice,
            distancia_acumulada_m=MEDIDO.acumulado[indice],
            distancia_ao_trajeto_m=distancia_ao_trajeto,
        )
    )


@pytest.fixture
def cenario():
    """Linha A (IDA) com horários o dia todo e tempo de percurso; parada no índice 100."""
    db = SessionLocal()
    _limpar(db)
    _semear(db, LINHA_A, "IDA", TRAJETO)
    db.flush()  # a SessionLocal do projeto tem autoflush desligado
    rota = db.query(Rota).filter(Rota.numero == LINHA_A).one()
    rota.horarios_por_dia = TODOS_OS_DIAS
    rota.tempo_percurso_min = 60
    parada = _parada(db, CODIGO, INDICE_PARADA)
    _vincular(db, parada, LINHA_A)
    db.commit()
    yield db
    _limpar(db)
    db.close()


# --------------------------------------------------------------------------
# veículos e chamadas
# --------------------------------------------------------------------------


def _veiculo(indice, velocidade=30.0, sentido="IDA", prefixo="440001", media=None, idade_s=5):
    lat, lng = TRAJETO[indice]
    return PosicaoVeiculo(
        prefixo=prefixo,
        lat=lat,
        lng=lng,
        sentido=sentido,
        velocidade=velocidade,
        direcao=0.0,
        atualizado_em=datetime.now(timezone.utc) - timedelta(seconds=idade_s),
        operadora="VIAÇÃO TESTE",
        velocidade_media_kmh=media,
    )


def _com_posicoes(por_linha: dict[str, list[PosicaoVeiculo]]):
    async def falso(numeros, *, db=None, colaborativos=None):
        return {n: por_linha.get(n, []) for n in numeros}

    return patch("mobilidade.routes._posicao_service.posicoes_das_linhas", AsyncMock(side_effect=falso))


def _chegadas(codigo=CODIGO):
    return client.get(f"/mobilidade/paradas/{codigo}/chegadas")


def _metros_ate_a_parada(indice_veiculo):
    return MEDIDO.metros_entre(indice_veiculo, INDICE_PARADA)


def _eta_esperado(indice_veiculo, velocidade_kmh):
    return _metros_ate_a_parada(indice_veiculo) / (velocidade_kmh * 1000 / 60)


# --------------------------------------------------------------------------
# GET /paradas/{codigo}/chegadas — ao vivo
# --------------------------------------------------------------------------


def test_onibus_a_caminho_da_parada_da_eta_ao_vivo_ate_ela(cenario):
    with _com_posicoes({LINHA_A: [_veiculo(60, velocidade=30.0)]}):
        resposta = _chegadas()

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["parada_codigo"] == CODIGO
    [chegada] = dados["chegadas"]
    assert chegada["numero"] == LINHA_A
    assert chegada["fonte"] == "ao_vivo"
    assert chegada["prefixo"] == "440001"
    assert chegada["veiculos_a_caminho"] == 1
    # distância ao longo do trajeto até a PARADA ÷ velocidade
    assert chegada["eta_minutos"] == pytest.approx(_eta_esperado(60, 30.0), abs=0.2)
    assert chegada["horario_previsto"] is None


def test_com_varios_onibus_vale_o_mais_proximo(cenario):
    longe = _veiculo(20, prefixo="LONGE")
    perto = _veiculo(80, prefixo="PERTO")

    with _com_posicoes({LINHA_A: [longe, perto]}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["prefixo"] == "PERTO"
    assert chegada["veiculos_a_caminho"] == 2


def test_onibus_que_ja_passou_da_parada_nao_conta_como_chegando(cenario):
    with _com_posicoes({LINHA_A: [_veiculo(INDICE_PARADA + 15)]}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["fonte"] != "ao_vivo"
    assert chegada["veiculos_a_caminho"] == 0


def test_onibus_do_sentido_oposto_nao_conta(cenario):
    with _com_posicoes({LINHA_A: [_veiculo(60, sentido="VOLTA")]}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["fonte"] != "ao_vivo"


def test_o_eta_usa_a_velocidade_media_e_nao_a_do_instante(cenario):
    instante = _veiculo(60, velocidade=60.0)
    media = _veiculo(60, velocidade=60.0, media=20.0)

    with _com_posicoes({LINHA_A: [instante]}):
        [so_instante] = _chegadas().json()["chegadas"]
    with _com_posicoes({LINHA_A: [media]}):
        [com_media] = _chegadas().json()["chegadas"]

    assert com_media["eta_minutos"] == pytest.approx(so_instante["eta_minutos"] * 3, rel=0.03)


def test_onibus_parado_na_janela_inteira_nao_da_eta_ao_vivo(cenario):
    parado = _veiculo(60, velocidade=0.0, media=0.5)

    with _com_posicoes({LINHA_A: [parado]}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["fonte"] != "ao_vivo"


def test_posicao_velha_nao_vira_eta(cenario):
    velho = _veiculo(60, idade_s=20 * 60)

    with _com_posicoes({LINHA_A: [velho]}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["fonte"] != "ao_vivo"


# --------------------------------------------------------------------------
# GET /paradas/{codigo}/chegadas — previsto e sem dado
# --------------------------------------------------------------------------


def test_sem_onibus_cai_no_horario_previsto_na_parada(cenario):
    with _com_posicoes({}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["fonte"] == "previsto"
    assert chegada["eta_minutos"] is not None and chegada["eta_minutos"] >= 0
    assert chegada["horario_previsto"] is not None and len(chegada["horario_previsto"]) == 5
    assert chegada["prefixo"] is None
    # saída a cada 30 min + o trecho do percurso: nunca mais de 30 min de espera
    assert chegada["eta_minutos"] <= 30.5


def test_sem_horario_nem_onibus_nao_inventa_numero(cenario):
    rota = cenario.query(Rota).filter(Rota.numero == LINHA_A).one()
    rota.horarios_por_dia = None
    cenario.commit()

    with _com_posicoes({}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["eta_minutos"] is None
    assert chegada["fonte"] is None


def test_sem_tempo_de_percurso_nao_ha_previsto(cenario):
    rota = cenario.query(Rota).filter(Rota.numero == LINHA_A).one()
    rota.tempo_percurso_min = None
    cenario.commit()

    with _com_posicoes({}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["eta_minutos"] is None and chegada["fonte"] is None


def test_ao_vivo_tem_prioridade_sobre_o_previsto(cenario):
    with _com_posicoes({LINHA_A: [_veiculo(60)]}):
        [chegada] = _chegadas().json()["chegadas"]

    assert chegada["fonte"] == "ao_vivo"
    assert chegada["horario_previsto"] is None


# --------------------------------------------------------------------------
# ordem, vínculos e erro
# --------------------------------------------------------------------------


def test_linhas_saem_ao_vivo_primeiro_depois_previsto_depois_sem_dado(cenario):
    # Linha B: sem horário e sem ônibus → "sem dado"
    _semear(cenario, LINHA_B, "IDA", TRAJETO)
    parada = cenario.query(Parada).filter(Parada.codigo == CODIGO).one()
    _vincular(cenario, parada, LINHA_B)
    cenario.commit()

    with _com_posicoes({LINHA_A: [_veiculo(60)]}):
        chegadas = _chegadas().json()["chegadas"]
    assert [c["numero"] for c in chegadas] == [LINHA_A, LINHA_B]
    assert [c["fonte"] for c in chegadas] == ["ao_vivo", None]

    # sem ônibus: A vira "previsto" (tem horário), B segue sem dado
    with _com_posicoes({}):
        chegadas = _chegadas().json()["chegadas"]
    assert [(c["numero"], c["fonte"]) for c in chegadas] == [(LINHA_A, "previsto"), (LINHA_B, None)]


def test_entre_dois_ao_vivo_o_mais_proximo_vem_primeiro(cenario):
    _semear(cenario, LINHA_B, "IDA", TRAJETO)
    parada = cenario.query(Parada).filter(Parada.codigo == CODIGO).one()
    _vincular(cenario, parada, LINHA_B)
    cenario.commit()

    with _com_posicoes({LINHA_A: [_veiculo(40)], LINHA_B: [_veiculo(90)]}):
        chegadas = _chegadas().json()["chegadas"]

    assert [c["numero"] for c in chegadas] == [LINHA_B, LINHA_A]
    assert chegadas[0]["eta_minutos"] < chegadas[1]["eta_minutos"]


def test_linha_que_casa_ida_e_volta_fica_so_com_o_lado_da_parada(cenario):
    # vias estreitas: a mesma parada aparece nas duas rotas dentro do raio de
    # vínculo; vale a de menor distância ao traçado.
    _semear(cenario, LINHA_A, "VOLTA", list(reversed(TRAJETO)))
    parada = cenario.query(Parada).filter(Parada.codigo == CODIGO).one()
    _vincular(cenario, parada, LINHA_A, sentido="VOLTA", indice=INDICE_PARADA, distancia_ao_trajeto=30.0)
    cenario.commit()

    with _com_posicoes({}):
        chegadas = _chegadas().json()["chegadas"]

    assert len(chegadas) == 1
    assert chegadas[0]["rota_sentido"] == "IDA"


def test_codigo_desconhecido_da_404(cenario):
    assert _chegadas("PR-NAO-EXISTE").status_code == 404


def test_parada_sem_linha_vinculada_devolve_lista_vazia(cenario):
    _parada(cenario, CODIGO_VOLTA, 150)
    cenario.commit()

    with _com_posicoes({}):
        resposta = _chegadas(CODIGO_VOLTA)

    assert resposta.status_code == 200
    assert resposta.json()["chegadas"] == []


def test_resposta_traz_calculado_em_para_o_cliente_saber_a_idade_do_dado(cenario):
    with _com_posicoes({}):
        dados = _chegadas().json()

    assert datetime.fromisoformat(dados["calculado_em"]).tzinfo is not None


# --------------------------------------------------------------------------
# passagem_prevista — pura, com relógio controlado
# --------------------------------------------------------------------------


def _rota(por_dia, percurso=60):
    return Rota(numero="X", sentido="IDA", nome="X", trajeto=[], paradas=[],
                horarios_por_dia=por_dia, tempo_percurso_min=percurso)


def _vinculo(fracao, comprimento=10_000.0):
    return RotaParada(numero="X", sentido="IDA", parada_id=1, ordem=0, indice_trajeto=0,
                      distancia_acumulada_m=fracao * comprimento, distancia_ao_trajeto_m=1.0)


def _local(dia, hhmm):
    horas, minutos = hhmm.split(":")
    return datetime(2026, 10, dia, int(horas), int(minutos), tzinfo=FUSO_SEMOB)


def test_passagem_e_saida_mais_a_fracao_do_percurso():
    # saída 08:00, percurso 60 min, parada na metade da rota → passa às 08:30
    rota = _rota({"0": ["08:00"]})  # 0 = segunda
    agora = _local(5, "08:10")  # 5/out/2026 é segunda

    instante, minutos = passagem_prevista(rota, _vinculo(0.5), 10_000.0, agora)

    assert instante.strftime("%H:%M") == "08:30"
    assert minutos == pytest.approx(20.0)


def test_parada_no_terminal_passa_na_hora_da_saida():
    rota = _rota({"0": ["09:00"]})

    instante, minutos = passagem_prevista(rota, _vinculo(0.0), 10_000.0, _local(5, "08:50"))

    assert instante.strftime("%H:%M") == "09:00"
    assert minutos == pytest.approx(10.0)


def test_passagem_que_ja_aconteceu_nao_conta():
    rota = _rota({"0": ["08:00", "10:00"]})  # percurso 60, metade → 08:30 e 10:30

    instante, _ = passagem_prevista(rota, _vinculo(0.5), 10_000.0, _local(5, "09:00"))

    assert instante.strftime("%H:%M") == "10:30"


def test_nunca_mistura_dia_util_com_fim_de_semana():
    # só tem horário no domingo (6); numa segunda, a próxima passagem é o
    # domingo seguinte — e isso passa de 12 h, então não é exibida.
    rota = _rota({"6": ["08:00"]})

    assert passagem_prevista(rota, _vinculo(0.5), 10_000.0, _local(5, "09:00")) is None


def test_saida_da_noite_anterior_pode_passar_depois_da_meia_noite():
    # saída ontem 23:30 + 60 min de percurso até o fim da rota → 00:30 de hoje
    rota = _rota({"6": ["23:30"], "0": []})  # domingo 4/out → passa na segunda 5/out

    instante, minutos = passagem_prevista(rota, _vinculo(1.0), 10_000.0, _local(5, "00:10"))

    assert instante.strftime("%d %H:%M") == "05 00:30"
    assert minutos == pytest.approx(20.0)


def test_primeira_saida_de_amanha_e_a_proxima_a_noite():
    rota = _rota({"0": ["05:30"], "1": ["05:30"]})  # nenhuma saída restante hoje

    instante, minutos = passagem_prevista(rota, _vinculo(0.0), 10_000.0, _local(5, "23:50"))

    assert instante.strftime("%d %H:%M") == "06 05:30"
    assert minutos == pytest.approx(340.0)
    assert minutos < ETA_PREVISTO_MAXIMO_MIN


def test_passagem_longe_demais_nao_e_exibida():
    rota = _rota({"0": ["20:00"]})

    # 08:00 → próxima passagem às 20:00 = 12 h, no limite; 07:59 passa do teto
    assert passagem_prevista(rota, _vinculo(0.0), 10_000.0, _local(5, "07:00")) is None


def test_sem_dado_nao_ha_passagem():
    assert passagem_prevista(_rota(None), _vinculo(0.5), 10_000.0, _local(5, "08:00")) is None
    assert passagem_prevista(_rota({"0": ["08:00"]}, percurso=None), _vinculo(0.5), 10_000.0, _local(5, "08:00")) is None
    assert passagem_prevista(_rota({"0": ["08:00"]}), _vinculo(0.5), None, _local(5, "08:00")) is None
    assert passagem_prevista(_rota({"0": ["08:00"]}), _vinculo(0.5), 0.0, _local(5, "08:00")) is None


def test_horario_malformado_e_ignorado_sem_quebrar():
    rota = _rota({"0": ["lixo", "25:99", "09:00"]})

    instante, _ = passagem_prevista(rota, _vinculo(0.0), 10_000.0, _local(5, "08:00"))

    assert instante.strftime("%H:%M") == "09:00"


# --------------------------------------------------------------------------
# paradas_proximas_do_usuario — "qual é a minha parada"
# --------------------------------------------------------------------------


@pytest.fixture
def duas_paradas_de_lados_opostos(cenario):
    """
    IDA (parada no índice 100) e VOLTA (parada no índice 104, ~450 m adiante,
    como o outro lado de uma avenida larga com retorno distante).
    """
    _semear(cenario, LINHA_A, "VOLTA", list(reversed(TRAJETO)))
    parada_volta = _parada(cenario, CODIGO_VOLTA, 100, nome="Parada do outro lado")
    _vincular(cenario, parada_volta, LINHA_A, sentido="VOLTA", indice=len(TRAJETO) - 1 - 100)
    cenario.commit()
    yield cenario


def test_minha_parada_e_a_mais_proxima_do_usuario(cenario):
    lat, lng = TRAJETO[INDICE_PARADA]

    alvos = paradas_proximas_do_usuario(cenario, LINHA_A, lat, lng + 0.0003)  # ~33 m

    assert list(alvos) == ["IDA"]
    assert alvos["IDA"][0].codigo == CODIGO


def test_parada_longe_demais_nao_e_a_minha(cenario):
    lat, lng = TRAJETO[INDICE_PARADA]

    # ~1,1 km ao norte
    assert paradas_proximas_do_usuario(cenario, LINHA_A, lat + 0.01, lng) == {}


def test_outra_linha_nao_aparece(cenario):
    lat, lng = TRAJETO[INDICE_PARADA]

    assert paradas_proximas_do_usuario(cenario, LINHA_B, lat, lng) == {}


def test_empate_entre_lados_mantem_os_dois(duas_paradas_de_lados_opostos):
    # as duas paradas estão no mesmo ponto (distância idêntica ao usuário)
    lat, lng = TRAJETO[INDICE_PARADA]

    alvos = paradas_proximas_do_usuario(duas_paradas_de_lados_opostos, LINHA_A, lat, lng)

    assert set(alvos) == {"IDA", "VOLTA"}


def test_usuario_mais_perto_de_um_lado_fica_so_com_ele(duas_paradas_de_lados_opostos):
    db = duas_paradas_de_lados_opostos
    # afasta a parada da VOLTA ~44 m (mais que o empate de EMPATE_ENTRE_SENTIDOS_M)
    volta = db.query(Parada).filter(Parada.codigo == CODIGO_VOLTA).one()
    volta.lat = volta.lat + 0.0004
    db.commit()
    lat, lng = TRAJETO[INDICE_PARADA]

    alvos = paradas_proximas_do_usuario(db, LINHA_A, lat, lng)

    assert list(alvos) == ["IDA"]
    assert 0.0004 * 111_000 > EMPATE_ENTRE_SENTIDOS_M


# --------------------------------------------------------------------------
# a pílula (GET /linhas/{numero}/posicoes) mede até a parada do usuário
# --------------------------------------------------------------------------


def _pilula(lat, lng, veiculos):
    with patch("mobilidade.routes._posicao_service.posicoes_da_linha", AsyncMock(return_value=veiculos)):
        return client.get(f"/mobilidade/linhas/{LINHA_A}/posicoes", params={"lat": lat, "lng": lng})


def test_pilula_mede_ate_a_parada_e_diz_qual(cenario):
    lat, lng = TRAJETO[INDICE_PARADA]

    resposta = _pilula(lat, lng + 0.0003, [_veiculo(60, velocidade=30.0)])

    [veiculo] = resposta.json()["veiculos"]
    assert veiculo["parada_codigo"] == CODIGO
    assert veiculo["parada_nome"] == "Parada de teste"
    assert veiculo["eta_minutos"] == pytest.approx(_eta_esperado(60, 30.0), abs=0.2)


def test_pilula_nao_mede_ate_o_gps_quando_ha_parada(cenario):
    # O usuário está ~220 m ANTES da parada, ainda dentro dos 400 m. Medir
    # até o GPS dele daria um ETA menor; quem espera, espera na parada.
    lat, lng = TRAJETO[INDICE_PARADA - 2]

    [veiculo] = _pilula(lat, lng, [_veiculo(60, velocidade=30.0)]).json()["veiculos"]

    assert veiculo["parada_codigo"] == CODIGO
    assert veiculo["eta_minutos"] == pytest.approx(_eta_esperado(60, 30.0), abs=0.2)


def test_pilula_usa_o_sentido_do_proprio_onibus(duas_paradas_de_lados_opostos):
    lat, lng = TRAJETO[INDICE_PARADA]  # empate: as duas paradas entram
    ida = _veiculo(60, sentido="IDA", prefixo="IDA001")
    volta = _veiculo(len(TRAJETO) - 1 - 60, sentido="VOLTA", prefixo="VOLTA1")

    veiculos = {v["prefixo"]: v for v in _pilula(lat, lng, [ida, volta]).json()["veiculos"]}

    assert veiculos["IDA001"]["parada_codigo"] == CODIGO
    assert veiculos["VOLTA1"]["parada_codigo"] == CODIGO_VOLTA
    assert veiculos["IDA001"]["eta_minutos"] is not None
    assert veiculos["VOLTA1"]["eta_minutos"] is not None


def test_pilula_onibus_do_lado_oposto_nao_ganha_eta(cenario):
    # só há parada da IDA por perto; um ônibus da VOLTA não serve a quem
    # espera deste lado — antes, a escolha do sentido "principal" da linha
    # decidia isso por sorte.
    lat, lng = TRAJETO[INDICE_PARADA]

    [veiculo] = _pilula(lat, lng, [_veiculo(60, sentido="VOLTA")]).json()["veiculos"]

    assert veiculo["eta_minutos"] is None
    assert veiculo["parada_codigo"] is None


def test_pilula_onibus_que_ja_passou_da_parada_fica_sem_eta(cenario):
    lat, lng = TRAJETO[INDICE_PARADA]

    [veiculo] = _pilula(lat, lng, [_veiculo(INDICE_PARADA + 10)]).json()["veiculos"]

    assert veiculo["eta_minutos"] is None


def test_pilula_sem_parada_ingerida_por_perto_usa_a_projecao_no_tracado(cenario):
    # remove os vínculos: a rota continua ingerida, mas não há `rota_parada`.
    cenario.query(RotaParada).filter(RotaParada.numero == LINHA_A).delete()
    cenario.commit()
    lat, lng = TRAJETO[INDICE_PARADA]

    [veiculo] = _pilula(lat, lng, [_veiculo(60, velocidade=30.0)]).json()["veiculos"]

    assert veiculo["eta_minutos"] is not None
    assert veiculo["parada_codigo"] is None  # sem parada de referência a informar


def test_pilula_sem_localizacao_nao_calcula_nada(cenario):
    with patch("mobilidade.routes._posicao_service.posicoes_da_linha", AsyncMock(return_value=[_veiculo(60)])):
        [veiculo] = client.get(f"/mobilidade/linhas/{LINHA_A}/posicoes").json()["veiculos"]

    assert veiculo["eta_minutos"] is None
    assert veiculo["parada_codigo"] is None
