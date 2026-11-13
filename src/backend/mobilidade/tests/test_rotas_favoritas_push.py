"""
US #22/#207 — aviso das rotas favoritas por Web Push.

- `decidir_aviso`: a regra da #22, em função pura;
- `montar_carga_rota_favorita`: o que a pessoa lê (LGPD);
- `FavoritasDoBanco`: SQL direto, em SQLite (mesmo desenho de
  test_destinatarios_banco.py — o teste não importa `colaboracao`);
- `EtaDoEmbarquePorTrajeto`: sobre o trajeto sintético de
  test_chegadas_da_rota.py;
- `ServicoRotasFavoritas`: fontes falsas, estado no banco de verdade.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from mobilidade import web_push
from mobilidade.models.aviso_rota_favorita import AvisoRotaFavorita
from mobilidade.providers.contratos_proximidade import PreferenciasDeNotificacao
from mobilidade.providers.contratos_rotas_favoritas import EtaEmbarque, FavoritaMonitorada
from mobilidade.providers.eta_embarque_trajeto import EtaDoEmbarquePorTrajeto
from mobilidade.providers.favoritas_banco import FavoritasDoBanco
from mobilidade.rota_service import RotaService
from mobilidade.services.servico_notificacoes import NotificadorMock
from mobilidade.services.servico_rotas_favoritas import (
    EVENTO_ANTECEDENCIA,
    EVENTO_ERRO,
    EVENTO_PREFERENCIAS,
    EVENTO_PROXIMIDADE,
    EVENTO_SEM_ETA,
    Decisao,
    ServicoRotasFavoritas,
    decidir_aviso,
)
from mobilidade.tests.test_chegadas_da_rota import (  # noqa: F401 — fixture `db`
    COD_DESCE,
    COD_SOBE,
    IDX_DESCE,
    IDX_SOBE,
    LINHA_A,
    TRAJETO,
    _veiculo,
    db,
)
from shared.database import SessionLocal

USUARIO = uuid.UUID("00000000-0000-4000-8000-00000000f207")


# ==========================================================================
# Regra da #22
# ==========================================================================


def _decidir(eta, ao_vivo=True, antecedencia=30, antec=False, prox=False):
    return decidir_aviso(antec, prox, eta, ao_vivo, antecedencia)


def test_fora_da_antecedencia_nao_avisa():
    assert _decidir(eta=33) is None


def test_dentro_da_antecedencia_avisa_uma_vez():
    assert _decidir(eta=28) is Decisao.ANTECEDENCIA
    assert _decidir(eta=20, antec=True) is None


def test_onibus_proximo_ao_vivo_avisa_mesmo_depois_da_antecedencia():
    assert _decidir(eta=4, antec=True) is Decisao.PROXIMIDADE
    assert _decidir(eta=2, antec=True, prox=True) is None


def test_onibus_proximo_so_pela_grade_nao_avisa():
    # "chega em 3 min" sem ônibus visto é o ônibus fantasma (RN-09).
    assert _decidir(eta=3, ao_vivo=False) is None


def test_antecedencia_pela_grade_avisa():
    # Com 30/60 min de antecedência quase nunca há ônibus ao vivo.
    assert _decidir(eta=25, ao_vivo=False) is Decisao.ANTECEDENCIA


def test_depois_do_aviso_de_proximo_nao_vem_lembrete_atrasado():
    assert _decidir(eta=8, prox=True) is None


def test_eta_que_volta_a_subir_encerra_a_corrida():
    assert _decidir(eta=36, antec=True, prox=True) is Decisao.FIM_DA_CORRIDA
    assert _decidir(eta=35, antec=True, prox=True) is None  # na margem, ainda é a mesma


def test_antecedencia_de_5_min_so_tem_o_aviso_de_proximo():
    assert _decidir(eta=5, antecedencia=5) is Decisao.PROXIMIDADE
    assert _decidir(eta=7, antecedencia=5) is None


# ==========================================================================
# Carga
# ==========================================================================


def test_carga_de_antecedencia_e_de_proximo():
    lembrete = web_push.montar_carga_rota_favorita("0.110", 28.4, proximo=False)
    proximo = web_push.montar_carga_rota_favorita("0.110", 1.2, proximo=True)

    assert lembrete["titulo"] == "Lembrete de rota"
    assert lembrete["corpo"] == "O ônibus da linha 0.110 chega em aproximadamente 28 minutos."
    assert proximo["titulo"] == "Ônibus próximo"
    assert proximo["corpo"].endswith("1 minuto.")


def test_aviso_de_proximo_substitui_o_lembrete_e_abre_a_linha():
    lembrete = web_push.montar_carga_rota_favorita("0.110", 28.0, proximo=False)
    proximo = web_push.montar_carga_rota_favorita("0.110", 3.0, proximo=True)

    assert lembrete["tag"] == proximo["tag"] == "rota:0.110"
    assert proximo["url"] == "/mapa?linha=0.110"


def test_tag_da_rota_favorita_e_distinta_das_outras():
    tags = {
        web_push.montar_carga_rota_favorita("0.110", 3.0, proximo=True)["tag"],
        web_push.montar_carga("0.110", "W3 Sul 502", 3.0)["tag"],
        web_push.montar_carga_atraso("0.110", 15.0, aumentou=False)["tag"],
        web_push.montar_carga_cancelamento("0.110", "06:00", None)["tag"],
    }
    assert len(tags) == 4


def test_carga_da_rota_favorita_so_tem_o_texto_que_a_pessoa_le():
    carga = web_push.montar_carga_rota_favorita("0.110", 3.0, proximo=True)

    assert set(carga) == {"titulo", "corpo", "url", "tag"}
    texto = json.dumps(carga)
    assert str(USUARIO) not in texto
    assert "lat" not in texto and "lng" not in texto


# ==========================================================================
# FavoritasDoBanco
# ==========================================================================

_DDL = """
CREATE TABLE rotas_favoritas (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL,
    numero_linha TEXT NOT NULL,
    label TEXT NOT NULL,
    origem_lat REAL NOT NULL,
    origem_lng REAL NOT NULL,
    destino_lat REAL NOT NULL,
    destino_lng REAL NOT NULL
);
CREATE TABLE inscricao_push (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL
);
"""


@pytest.fixture
def sqlite():
    engine = create_engine("sqlite://")
    with engine.begin() as conexao:
        for comando in _DDL.split(";"):
            if comando.strip():
                conexao.execute(text(comando))
    sessao = sessionmaker(bind=engine)()
    yield sessao
    sessao.close()


def _favoritar(db, usuario, linha="0.110"):
    db.execute(
        text(
            "INSERT INTO rotas_favoritas VALUES "
            "(:id, :usuario, :linha, 'Casa → Trabalho', -15.83, -48.04, -15.79, -47.88)"
        ),
        {"id": str(uuid.uuid4()), "usuario": str(usuario), "linha": linha},
    )
    db.commit()


def _inscrever_aparelho(db, usuario):
    db.execute(
        text("INSERT INTO inscricao_push VALUES (:id, :usuario)"),
        {"id": str(uuid.uuid4()), "usuario": str(usuario)},
    )
    db.commit()


def test_lista_so_favoritas_de_quem_tem_aparelho_inscrito(sqlite):
    com, sem = uuid.uuid4(), uuid.uuid4()
    _favoritar(sqlite, com, "0.110")
    _favoritar(sqlite, sem, "0.900")
    _inscrever_aparelho(sqlite, com)

    favoritas = FavoritasDoBanco().listar(sqlite)

    assert [(f.numero_linha, str(f.usuario_id)) for f in favoritas] == [("0.110", str(com))]
    assert favoritas[0].origem_lat == -15.83


def test_dois_aparelhos_nao_duplicam_a_favorita(sqlite):
    usuario = uuid.uuid4()
    _favoritar(sqlite, usuario)
    _inscrever_aparelho(sqlite, usuario)
    _inscrever_aparelho(sqlite, usuario)

    assert len(FavoritasDoBanco().listar(sqlite)) == 1


def test_falha_no_banco_devolve_lista_vazia():
    engine = create_engine("sqlite://")  # sem as tabelas
    sessao = sessionmaker(bind=engine)()

    assert FavoritasDoBanco().listar(sessao) == []


# ==========================================================================
# EtaDoEmbarquePorTrajeto (trajeto sintético da #190)
# ==========================================================================


def _favorita_no_trajeto(sobe=IDX_SOBE, desce=IDX_DESCE, linha=LINHA_A) -> FavoritaMonitorada:
    (olat, olng), (dlat, dlng) = TRAJETO[sobe], TRAJETO[desce]
    return FavoritaMonitorada(uuid.uuid4(), USUARIO, linha, olat, olng, dlat, dlng)


def test_eta_ao_vivo_ate_a_parada_de_embarque(db):
    eta = EtaDoEmbarquePorTrajeto(RotaService()).eta(
        _favorita_no_trajeto(), [_veiculo(IDX_SOBE - 20)], datetime.now(timezone.utc), db
    )

    assert eta is not None and eta.ao_vivo
    assert 0 < eta.eta_minutos < 10


def test_sem_onibus_usa_a_passagem_prevista(db):
    eta = EtaDoEmbarquePorTrajeto(RotaService()).eta(
        _favorita_no_trajeto(), [], datetime.now(timezone.utc), db
    )

    assert eta is not None and not eta.ao_vivo


def test_origem_longe_de_qualquer_parada_da_linha_nao_tem_eta(db):
    favorita = FavoritaMonitorada(uuid.uuid4(), USUARIO, LINHA_A, -10.0, -40.0, -10.1, -40.1)

    assert EtaDoEmbarquePorTrajeto(RotaService()).eta(
        favorita, [], datetime.now(timezone.utc), db
    ) is None


def test_onibus_que_ja_passou_do_embarque_nao_conta_como_ao_vivo(db):
    eta = EtaDoEmbarquePorTrajeto(RotaService()).eta(
        _favorita_no_trajeto(), [_veiculo(IDX_SOBE + 20)], datetime.now(timezone.utc), db
    )

    assert eta is None or not eta.ao_vivo


# ==========================================================================
# ServicoRotasFavoritas
# ==========================================================================


class _Favoritas:
    def __init__(self, *favoritas):
        self.favoritas = list(favoritas)

    def listar(self, db):
        return list(self.favoritas)


class _Veiculos:
    def obter_das_linhas(self, numeros):
        return {}


class _Preferencias:
    def __init__(self, **kwargs):
        self.pref = PreferenciasDeNotificacao(**kwargs)

    def obter(self, usuario_id, db):
        return self.pref


class _Eta:
    """ETA controlado pelo teste; `None` = sem dado."""

    def __init__(self, minutos=None, ao_vivo=True):
        self.minutos = minutos
        self.ao_vivo = ao_vivo

    def eta(self, favorita, veiculos, agora, db):
        if self.minutos is None:
            return None
        return EtaEmbarque(eta_minutos=self.minutos, ao_vivo=self.ao_vivo)


def _favorita(linha="0.110") -> FavoritaMonitorada:
    return FavoritaMonitorada(uuid.uuid4(), USUARIO, linha, -15.83, -48.04, -15.79, -47.88)


@pytest.fixture
def banco():
    sessao = SessionLocal()
    yield sessao
    sessao.rollback()
    sessao.query(AvisoRotaFavorita).delete(synchronize_session=False)
    sessao.commit()
    sessao.close()


def _servico(*favoritas, eta=None, notificador=None, **pref):
    notificador = notificador or NotificadorMock()
    servico = ServicoRotasFavoritas(
        favoritas=_Favoritas(*favoritas),
        veiculos=_Veiculos(),
        preferencias=_Preferencias(**pref),
        notificador=notificador,
        eta=eta or _Eta(),
    )
    return servico, notificador


def test_uma_corrida_inteira_gera_os_dois_avisos_uma_vez_cada(banco):
    favorita = _favorita()
    eta = _Eta()
    servico, notificador = _servico(favorita, eta=eta)

    sequencia = []
    for minutos in (40, 29, 20, 12, 4, 2, 1):
        eta.minutos = minutos
        sequencia.append(servico.verificar_ciclo(banco))

    assert sequencia == [[], [EVENTO_ANTECEDENCIA], [], [], [EVENTO_PROXIMIDADE], [], []]
    assert notificador.chamadas == [
        ("rota_favorita", str(USUARIO), "0.110", 29, False),
        ("rota_favorita", str(USUARIO), "0.110", 4, True),
    ]


def test_proximo_onibus_da_linha_e_uma_corrida_nova(banco):
    favorita = _favorita()
    eta = _Eta()
    servico, notificador = _servico(favorita, eta=eta)

    for minutos in (25, 3, 50, 25, 3):  # o 50 é o ônibus seguinte, depois que o primeiro passou
        eta.minutos = minutos
        servico.verificar_ciclo(banco)

    assert [c[4] for c in notificador.chamadas] == [False, True, False, True]


def test_o_estado_fica_no_banco_e_sobrevive_a_outra_instancia(banco):
    favorita = _favorita()
    primeiro, n1 = _servico(favorita, eta=_Eta(25))
    primeiro.verificar_ciclo(banco)

    # Outro processo (deploy novo, segunda máquina): não repete o aviso.
    segundo, n2 = _servico(favorita, eta=_Eta(24))
    assert segundo.verificar_ciclo(banco) == []
    assert len(n1.chamadas) == 1 and n2.chamadas == []


def test_notificacoes_desligadas_nao_avisam_nem_gravam_estado(banco):
    favorita = _favorita()
    servico, notificador = _servico(favorita, eta=_Eta(25), notificacoes_ativas=False)

    assert servico.verificar_ciclo(banco) == [EVENTO_PREFERENCIAS]
    assert notificador.chamadas == []
    assert banco.get(AvisoRotaFavorita, favorita.favorita_id) is None


def test_respeita_a_antecedencia_configurada(banco):
    favorita = _favorita()
    servico, notificador = _servico(favorita, eta=_Eta(25), antecedencia_minutos=10)

    assert servico.verificar_ciclo(banco) == []
    assert notificador.chamadas == []


def test_sem_eta_nao_avisa(banco):
    servico, notificador = _servico(_favorita(), eta=_Eta(None))

    assert servico.verificar_ciclo(banco) == [EVENTO_SEM_ETA]
    assert notificador.chamadas == []


def test_estado_de_favorita_que_sumiu_e_removido(banco):
    some, fica = _favorita(), _favorita("0.900")
    servico, _ = _servico(some, fica, eta=_Eta(25))
    servico.verificar_ciclo(banco)

    servico.favoritas.favoritas = [fica]
    servico.eta.minutos = 20
    servico.verificar_ciclo(banco)

    banco.expire_all()
    assert banco.get(AvisoRotaFavorita, some.favorita_id) is None
    assert banco.get(AvisoRotaFavorita, fica.favorita_id) is not None


def test_lista_vazia_nao_apaga_o_estado(banco):
    # É o que o provider devolve quando o banco falha: apagar faria o
    # ciclo seguinte repetir todos os avisos.
    favorita = _favorita()
    servico, _ = _servico(favorita, eta=_Eta(25))
    servico.verificar_ciclo(banco)

    servico.favoritas.favoritas = []
    servico.verificar_ciclo(banco)

    banco.expire_all()
    assert banco.get(AvisoRotaFavorita, favorita.favorita_id) is not None


def test_erro_em_uma_favorita_nao_interrompe_as_outras(banco):
    quebra, ok = _favorita("QUEBRA"), _favorita("0.110")

    class _EtaQuebra(_Eta):
        def eta(self, favorita, veiculos, agora, db):
            if favorita.numero_linha == "QUEBRA":
                raise RuntimeError("boom")
            return super().eta(favorita, veiculos, agora, db)

    servico, notificador = _servico(quebra, ok, eta=_EtaQuebra(25))

    assert servico.verificar_ciclo(banco) == [EVENTO_ERRO, EVENTO_ANTECEDENCIA]
    assert [c[2] for c in notificador.chamadas] == ["0.110"]


def test_preferencias_sao_lidas_uma_vez_por_usuario_no_ciclo(banco):
    class _Contadas(_Preferencias):
        chamadas = 0

        def obter(self, usuario_id, db):
            _Contadas.chamadas += 1
            return self.pref

    servico, _ = _servico(_favorita(), _favorita("0.900"), eta=_Eta(25))
    servico.preferencias = _Contadas()
    servico.verificar_ciclo(banco)

    assert _Contadas.chamadas == 1
