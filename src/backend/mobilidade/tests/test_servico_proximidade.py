import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from mobilidade.models.alerta_proximidade import AlertaProximidade
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.providers.contratos_proximidade import (
    PreferenciasDeNotificacao,
    ViagemAtiva,
    ViagensAtivasProvisorias,
)
from mobilidade.services.servico_notificacoes import NotificadorMock
from mobilidade.services.servico_proximidade import (
    EVENTO_DISPARADO,
    EVENTO_ERRO,
    EVENTO_JA_DISPARADO,
    EVENTO_PREFERENCIAS,
    EVENTO_SEM_POSICAO,
    ServicoProximidade,
)

# Coordenadas de referência (Taguatinga — só como alvo de teste).
LAT_PARADA = -15.83
LNG_PARADA = -48.05

# 1 grau de latitude ≈ 111,2 km; a 60 km/h:
#   deslocamento 0,045° ≈  5,0 km → ETA ≈  5 min (dentro do limiar)
#   deslocamento 0,198° ≈ 22,0 km → ETA ≈ 22 min (fora do limiar padrão)
DESL_LONGE_GRAUS = 0.198
DESL_PERTO_GRAUS = 0.045


# ---------------------------------------------------------------------------
# Dublês das fontes injetadas (fakes de contrato, não MagicMock de ORM)
# ---------------------------------------------------------------------------


class _Viagens:
    def __init__(self, viagens):
        self._viagens = list(viagens)

    def listar_ativas(self):
        return list(self._viagens)


class _Veiculos:
    def __init__(self, mapa=None, falhar=False):
        self._mapa = mapa or {}
        self._falhar = falhar

    def obter_das_linhas(self, numeros_linha):
        if self._falhar:
            raise RuntimeError("feed de posicao fora do ar")
        return {n: self._mapa.get(n, []) for n in numeros_linha}


class _Preferencias:
    def __init__(self, pref):
        self._pref = pref
        self.consultados: list[uuid.UUID] = []

    def obter(self, usuario_id, db):
        self.consultados.append(usuario_id)
        return self._pref


# ---------------------------------------------------------------------------
# Fábricas de dados de teste
# ---------------------------------------------------------------------------


def _viagem(usuario_id=None, codigo="PR-00001", viagem_id=None):
    return ViagemAtiva(
        viagem_id=viagem_id or str(uuid.uuid4()),
        usuario_id=usuario_id or uuid.uuid4(),
        numero_linha="0.110",
        parada_destino_codigo=codigo,
        parada_destino_lat=LAT_PARADA,
        parada_destino_lng=LNG_PARADA,
        parada_destino_nome="Terminal Central",
    )


def _veiculo(deslocamento_graus=DESL_PERTO_GRAUS, velocidade=60.0):
    return PosicaoVeiculo(
        prefixo="TESTE01",
        lat=LAT_PARADA - deslocamento_graus,
        lng=LNG_PARADA,
        sentido=None,
        velocidade=velocidade,
        direcao=None,
        atualizado_em=datetime.now(timezone.utc),
        operadora="Operadora Teste",
    )


def _preferencias(**kwargs):
    return PreferenciasDeNotificacao(**kwargs)


def _servico(viagens, veiculos, preferencias, notificador=None):
    return ServicoProximidade(
        viagens=_Viagens(viagens),
        veiculos=_Veiculos(veiculos),
        preferencias=preferencias,
        notificador=notificador or NotificadorMock(),
    )


@pytest.fixture
def db():
    """Sessão SQLite em memória com só a tabela do alerta de proximidade."""
    engine = create_engine("sqlite://")
    AlertaProximidade.__table__.create(engine)
    sessao = sessionmaker(bind=engine)()
    yield sessao
    sessao.close()


# ---------------------------------------------------------------------------
# Cenário 1 — alerta de proximidade
# ---------------------------------------------------------------------------


def test_cenario1_dispara_quando_eta_abaixo_da_antecedencia(db):
    viagem = _viagem()
    notificador = NotificadorMock()
    servico = _servico(
        [viagem],
        {"0.110": [_veiculo()]},
        _Preferencias(_preferencias(antecedencia_minutos=10)),
        notificador,
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == [EVENTO_DISPARADO]
    alerta = db.query(AlertaProximidade).one()
    assert alerta.usuario_id == viagem.usuario_id
    assert alerta.viagem_id == viagem.viagem_id
    assert alerta.linha_id == "0.110"
    assert alerta.parada_destino_codigo == "PR-00001"
    assert alerta.parada_destino_nome == "Terminal Central"
    assert alerta.status == "disparado"
    assert alerta.eta_minutos == pytest.approx(5.0, abs=0.1)
    assert alerta.disparado_em is not None
    assert notificador.chamadas[0][0] == "proximidade"
    assert notificador.chamadas[0][3] == "Terminal Central"


def test_cenario1_nao_dispara_quando_eta_acima_da_antecedencia(db):
    notificador = NotificadorMock()
    servico = _servico(
        [_viagem()],
        {"0.110": [_veiculo(deslocamento_graus=DESL_LONGE_GRAUS)]},
        _Preferencias(_preferencias(antecedencia_minutos=10)),
        notificador,
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == []
    assert db.query(AlertaProximidade).count() == 0
    assert notificador.chamadas == []


def test_cenario1_respeita_antecedencia_configurada_pelo_usuario(db):
    # O mesmo ônibus a 22 min dispara para quem configurou 60 min...
    servico = _servico(
        [_viagem()],
        {"0.110": [_veiculo(deslocamento_graus=DESL_LONGE_GRAUS)]},
        _Preferencias(_preferencias(antecedencia_minutos=60)),
    )

    assert servico.verificar_proximidades(db) == [EVENTO_DISPARADO]

    # ...e não dispara para quem configurou 10 min.
    servico = _servico(
        [_viagem()],
        {"0.110": [_veiculo(deslocamento_graus=DESL_LONGE_GRAUS)]},
        _Preferencias(_preferencias(antecedencia_minutos=10)),
    )
    assert servico.verificar_proximidades(db) == []
    assert db.query(AlertaProximidade).count() == 1


# ---------------------------------------------------------------------------
# Cenário 2 — alerta uma única vez por parada na viagem
# ---------------------------------------------------------------------------


def test_cenario2_nao_repete_na_mesma_parada_da_mesma_viagem(db):
    viagem = _viagem()
    notificador = NotificadorMock()
    veiculos = {"0.110": [_veiculo()]}

    primeiro = _servico(
        [viagem], veiculos, _Preferencias(_preferencias()), notificador
    )
    segundo = _servico(
        [viagem], veiculos, _Preferencias(_preferencias()), notificador
    )

    assert primeiro.verificar_proximidades(db) == [EVENTO_DISPARADO]
    assert segundo.verificar_proximidades(db) == [EVENTO_JA_DISPARADO]

    assert db.query(AlertaProximidade).count() == 1
    assert len(notificador.chamadas) == 1


def test_cenario2_dispara_uma_vez_por_viagem(db):
    # Mesma parada, duas viagens distintas: cada viagem tem o seu alerta.
    viagem_a = _viagem()
    viagem_b = _viagem()
    servico = _servico(
        [viagem_a, viagem_b],
        {"0.110": [_veiculo()]},
        _Preferencias(_preferencias()),
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == [EVENTO_DISPARADO, EVENTO_DISPARADO]
    assert db.query(AlertaProximidade).count() == 2


def test_cenario2_indice_unico_bloqueia_segunda_insercao(db):
    # A proteção não é só do serviço: o banco recusa a duplicata, que é o
    # que fecha a porta para dois ciclos simultâneos.
    viagem = _viagem()
    alerta = AlertaProximidade(
        usuario_id=viagem.usuario_id,
        viagem_id=viagem.viagem_id,
        linha_id="0.110",
        parada_destino_codigo=viagem.parada_destino_codigo,
        status="disparado",
        eta_minutos=5.0,
        disparado_em=datetime.utcnow(),
    )
    db.add(alerta)
    db.commit()

    with pytest.raises(IntegrityError):
        db.add(
            AlertaProximidade(
                usuario_id=viagem.usuario_id,
                viagem_id=viagem.viagem_id,
                linha_id="0.110",
                parada_destino_codigo=viagem.parada_destino_codigo,
                status="disparado",
                eta_minutos=5.0,
                disparado_em=datetime.utcnow(),
            )
        )
        db.commit()
    db.rollback()


# ---------------------------------------------------------------------------
# Cenário 3 — preferências de notificação (US #29)
# ---------------------------------------------------------------------------


def test_cenario3_nao_dispara_com_notificacoes_desativadas(db):
    notificador = NotificadorMock()
    servico = _servico(
        [_viagem()],
        {"0.110": [_veiculo()]},
        _Preferencias(_preferencias(notificacoes_ativas=False)),
        notificador,
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == [EVENTO_PREFERENCIAS]
    assert db.query(AlertaProximidade).count() == 0
    assert notificador.chamadas == []


def test_cenario3_nao_dispara_com_alerta_de_chegada_desativado(db):
    servico = _servico(
        [_viagem()],
        {"0.110": [_veiculo()]},
        _Preferencias(_preferencias(alerta_chegada=False)),
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == [EVENTO_PREFERENCIAS]
    assert db.query(AlertaProximidade).count() == 0


def test_cenario3_consulta_preferencias_do_usuario_da_viagem(db):
    viagem = _viagem()
    preferencias = _Preferencias(_preferencias())
    servico = _servico([viagem], {"0.110": []}, preferencias)

    servico.verificar_proximidades(db)

    assert preferencias.consultados == [viagem.usuario_id]


# ---------------------------------------------------------------------------
# Cenário 4 — sem posição do veículo, sem alerta
# ---------------------------------------------------------------------------


def test_cenario4_sem_veiculos_nao_dispara(db):
    notificador = NotificadorMock()
    servico = _servico(
        [_viagem()],
        {"0.110": []},
        _Preferencias(_preferencias()),
        notificador,
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == [EVENTO_SEM_POSICAO]
    assert db.query(AlertaProximidade).count() == 0
    assert notificador.chamadas == []


def test_cenario4_veiculo_sem_velocidade_nao_dispara(db):
    servico = _servico(
        [_viagem()],
        {"0.110": [_veiculo(velocidade=None)]},
        _Preferencias(_preferencias()),
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == [EVENTO_SEM_POSICAO]
    assert db.query(AlertaProximidade).count() == 0


def test_cenario4_falha_na_fonte_nao_derruba_o_ciclo(db):
    # O contrato manda "nunca lançar"; se lançar mesmo assim, o serviço
    # engole a exceção e segue como "sem posição" (Cenário 4).
    notificador = NotificadorMock()
    servico = ServicoProximidade(
        viagens=_Viagens([_viagem()]),
        veiculos=_Veiculos(falhar=True),
        preferencias=_Preferencias(_preferencias()),
        notificador=notificador,
    )

    eventos = servico.verificar_proximidades(db)

    assert eventos == [EVENTO_SEM_POSICAO]
    assert notificador.chamadas == []


# ---------------------------------------------------------------------------
# Robustez do ciclo
# ---------------------------------------------------------------------------


def test_sem_viagens_ativas_o_ciclo_retorna_vazio(db):
    servico = _servico([], {"0.110": [_veiculo()]}, _Preferencias(_preferencias()))

    eventos = servico.verificar_proximidades(db)

    assert eventos == []


def test_viagem_ativa_provisoria_nao_tem_nada(db):
    # O provider provisório da #171 mantém o worker integrado e inerte.
    assert ViagensAtivasProvisorias().listar_ativas() == []

    servico = ServicoProximidade(
        viagens=ViagensAtivasProvisorias(),
        veiculos=_Veiculos({"0.110": [_veiculo()]}),
        preferencias=_Preferencias(_preferencias()),
        notificador=NotificadorMock(),
    )

    assert servico.verificar_proximidades(db) == []


def test_integrity_error_no_commit_nao_notifica():
    # Dois ciclos simultâneos: o commit perde a corrida e o alerta já foi
    # registrado pela outra transação — não pode notificar em duplicata.
    viagem = _viagem()
    notificador = NotificadorMock()
    servico = _servico(
        [viagem], {"0.110": [_veiculo()]}, _Preferencias(_preferencias()), notificador
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.commit.side_effect = IntegrityError("unique", "stmt", "params")

    eventos = servico.verificar_proximidades(mock_db)

    assert eventos == [EVENTO_JA_DISPARADO]
    mock_db.rollback.assert_called()
    assert notificador.chamadas == []


def test_erro_inesperado_na_viagem_nao_derruba_o_ciclo():
    viagem_a = _viagem()
    viagem_b = _viagem()
    notificador = NotificadorMock()
    servico = _servico(
        [viagem_a, viagem_b],
        {"0.110": [_veiculo()]},
        _Preferencias(_preferencias()),
        notificador,
    )

    mock_db = MagicMock()
    # A primeira viagem quebra na leitura das preferências; a segunda roda
    # normalmente (preferências devolvem objeto de verdade).
    preferencias_reais = _Preferencias(_preferencias())
    chamadas = {"n": 0}

    def _obter(usuario_id, db):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise RuntimeError("banco travou")
        return preferencias_reais.obter(usuario_id, db)

    servico.preferencias.obter = _obter
    mock_db.query.return_value.filter.return_value.first.return_value = None

    eventos = servico.verificar_proximidades(mock_db)

    assert eventos == [EVENTO_ERRO, EVENTO_DISPARADO]
    assert mock_db.rollback.called
    assert len(notificador.chamadas) == 1
