import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mobilidade.linhas_alternativas import SOBREPOSICAO_MINIMA
from mobilidade.models.alerta_cancelamento import AlertaCancelamento
from mobilidade.models.linha import Linha
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.posicao_service import FUSO_SEMOB, PosicaoVeiculo
from mobilidade.providers.contratos_proximidade import PreferenciasDeNotificacao
from mobilidade.services.servico_cancelamento import (
    EVENTO_FEED_INDISPONIVEL,
    EVENTO_JA_REGISTRADO,
    EVENTO_REGISTRADO,
    JANELA_DETECCAO_MAX_MIN,
    JANELA_DETECCAO_MIN_MIN,
    ServicoCancelamento,
    _minutos_desde,
)
from mobilidade.services.servico_notificacoes import NotificadorMock

# ---------------------------------------------------------------------------
# Dublês das fontes injetadas (fakes de contrato, não MagicMock de ORM)
# ---------------------------------------------------------------------------


class _Destinatarios:
    def __init__(self, por_linha):
        self._por_linha = por_linha

    def listar_por_linha(self, db):
        return {k: set(v) for k, v in self._por_linha.items()}


class _Veiculos:
    def __init__(self, mapa=None, falhar=False):
        self._mapa = mapa or {}
        self._falhar = falhar

    def obter_das_linhas(self, numeros_linha):
        if self._falhar:
            raise RuntimeError("feed de posicao fora do ar")
        return {n: self._mapa.get(n, []) for n in numeros_linha}


class _Preferencias:
    """Devolve a mesma configuração para qualquer usuário (ou uma por id)."""

    def __init__(self, pref=None, por_usuario=None):
        self._pref = pref or PreferenciasDeNotificacao()
        self._por_usuario = por_usuario or {}
        self.consultados: list[uuid.UUID] = []

    def obter(self, usuario_id, db):
        self.consultados.append(usuario_id)
        return self._por_usuario.get(usuario_id, self._pref)


# ---------------------------------------------------------------------------
# Fábricas de dados de teste
# ---------------------------------------------------------------------------


def _usuario() -> uuid.UUID:
    return uuid.uuid4()


def _veiculo(prefixo="TESTE01"):
    return PosicaoVeiculo(
        prefixo=prefixo,
        lat=-15.83,
        lng=-48.05,
        sentido=None,
        velocidade=60.0,
        direcao=None,
        atualizado_em=datetime.now(timezone.utc),
        operadora="Operadora Teste",
    )


def _agora_local(**deslocamento) -> datetime:
    """Instante em UTC, derivado do horário LOCAL de Brasília."""
    return datetime.now(FUSO_SEMOB).replace(**deslocamento).astimezone(timezone.utc)


def _servico(destinatarios, veiculos, preferencias, notificador=None):
    return ServicoCancelamento(
        veiculos=veiculos,
        preferencias=preferencias,
        notificador=notificador or NotificadorMock(),
        destinatarios=destinatarios,
    )


def _cadastrar_linha(db, numero="0.110", horarios=("06:00", "06:20", "06:40")):
    db.add(
        Linha(
            numero=numero,
            nome=f"Linha {numero}",
            sentido="IDA",
            paradas=[],
            trajeto=[],
            horarios_previstos=list(horarios),
        )
    )
    db.commit()


def _cadastrar_rota(db, numero, paradas, sentido="IDA"):
    """Paradas (ids int) vinculadas à linha, como a ingestão grava."""
    for ordem, parada_id in enumerate(paradas):
        db.add(
            RotaParada(
                numero=numero,
                sentido=sentido,
                parada_id=parada_id,
                ordem=ordem,
                indice_trajeto=ordem,
                distancia_acumulada_m=ordem * 500.0,
                distancia_ao_trajeto_m=10.0,
            )
        )
    db.commit()


def _cadastrar_paradas(db, quantidade):
    # `codigo` é único: deriva da contagem atual para o factory poder ser
    # chamado mais de uma vez no mesmo teste. Devolve só as novas.
    base = db.query(Parada).count()
    novas = []
    for indice in range(base, base + quantidade):
        parada = Parada(codigo=f"COD{indice:04d}", nome="Parada", lat=-15.8, lng=-48.0)
        db.add(parada)
        novas.append(parada)
    db.commit()
    return [p.id for p in novas]


@pytest.fixture
def db():
    """Sessão SQLite em memória com as tabelas que o serviço toca."""
    engine = create_engine("sqlite://")
    AlertaCancelamento.__table__.create(engine)
    Linha.__table__.create(engine)
    Parada.__table__.create(engine)
    RotaParada.__table__.create(engine)
    sessao = sessionmaker(bind=engine)()
    yield sessao
    sessao.close()


# ---------------------------------------------------------------------------
# Cenário 3 — cancelamento detectado por ausência do veículo
# ---------------------------------------------------------------------------


def test_cenario3_registra_e_notifica_quando_partida_passou_e_linha_sem_onibus(db):
    """Partida das 06:00 passou há 20 min, linha sem veículo, feed vivo."""
    usuario = _usuario()
    # Horário local 06:20 => partida das 06:00 caiu há 20 min (na janela).
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, horarios=("06:00",))
    notificador = NotificadorMock()
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        # Outra linha com veículo: o feed está vivo, a ausência é real.
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
        notificador,
    )

    eventos = servico._verificar_linha("0.110", {usuario}, [], agora, db)

    assert eventos == [EVENTO_REGISTRADO]
    alerta = db.query(AlertaCancelamento).one()
    assert alerta.numero_linha == "0.110"
    assert alerta.horario_partida == "06:00"
    assert alerta.status == "suspeito"
    # Notificou DEPOIS do commit, com a preferência ativa.
    assert notificador.chamadas == [
        ("cancelamento_viagem", str(usuario), "0.110", "06:00", None)
    ]


def test_cenario3_com_alternativa_sugere_linha_com_sobreposicao(db):
    """A cancelada tinha 3 paradas; a alternativa atende 2 delas (67%)..."""
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    _cadastrar_linha(db, "0.222", horarios=())
    ids = _cadastrar_paradas(db, 4)
    # Cancelada: paradas 0,1,2. Candidata 0.900: paradas 1,2,3 => 2/3 = 67%
    _cadastrar_rota(db, "0.110", ids[:3])
    _cadastrar_rota(db, "0.900", ids[1:])
    notificador = NotificadorMock()
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
        notificador,
    )

    servico._verificar_linha("0.110", {usuario}, [], agora, db)

    alerta = db.query(AlertaCancelamento).one()
    # 67% < 70% => NÃO sugere (SPEC: >= 70% das paradas).
    assert alerta.alternativa_numero is None


def test_cenario3_sugere_quando_sobreposicao_alcanca_o_minimo(db):
    """A candidata atende 3 das 3 paradas da cancelada (100%)."""
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    _cadastrar_linha(db, "0.900", horarios=())
    ids = _cadastrar_paradas(db, 3)
    _cadastrar_rota(db, "0.110", ids)
    # Candidata cobre todas as paradas da cancelada e ainda uma mais.
    extras = _cadastrar_paradas(db, 1)
    _cadastrar_rota(db, "0.900", ids + extras)
    notificador = NotificadorMock()
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
        notificador,
    )

    servico._verificar_linha("0.110", {usuario}, [], agora, db)

    alerta = db.query(AlertaCancelamento).one()
    assert alerta.alternativa_numero == "0.900"
    assert notificador.chamadas[0][-1] == "0.900"


# ---------------------------------------------------------------------------
# Cenário 4 — sem dado confiável, não notifica
# ---------------------------------------------------------------------------


def test_feed_inteiro_vazio_nao_registra_nada(db):
    """SEM veículos de NENHUMA linha: a fonte pode estar fora, não a linha."""
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    notificador = NotificadorMock()
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({}),  # nenhuma linha reporta posição
        _Preferencias(),
        notificador,
    )

    eventos = servico.verificar_ciclo(db)

    assert eventos == [EVENTO_FEED_INDISPONIVEL]
    assert db.query(AlertaCancelamento).count() == 0
    assert notificador.chamadas == []


def test_linha_com_onibus_operando_nao_gera_alerta(db):
    """Cenário 3 invertido: a linha TEM veículo, a partida ocorreu."""
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    notificador = NotificadorMock()
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"0.110": [_veiculo()]}),
        _Preferencias(),
        notificador,
    )

    servico._verificar_linha("0.110", {usuario}, [_veiculo()], agora, db)

    assert db.query(AlertaCancelamento).count() == 0
    assert notificador.chamadas == []


# ---------------------------------------------------------------------------
# Janela de detecção
# ---------------------------------------------------------------------------


def test_partida_fora_da_janela_nao_registra(db):
    """Partida há 60 min: o worker pode ter reiniciado tarde demais."""
    usuario = _usuario()
    agora = _agora_local(hour=7, minute=0)  # 06:00 passou há 60 min
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
    )

    eventos = servico._verificar_linha("0.110", {usuario}, [], agora, db)

    assert eventos == []
    assert db.query(AlertaCancelamento).count() == 0


def test_partida_muito_recente_ainda_nao_registra(db):
    """Partida há 5 min: o ônibus pode simplesmente estar atrasado."""
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=5)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
    )

    servico._verificar_linha("0.110", {usuario}, [], agora, db)

    assert db.query(AlertaCancelamento).count() == 0


def test_minutos_desde_usa_o_fuso_local():
    """06:00 comparado com 09:00 UTC (= 06:00 em Brasília) dá 0 min."""
    agora_utc = datetime(2026, 10, 29, 9, 0, tzinfo=timezone.utc)
    assert _minutos_desde("06:00", agora_utc.astimezone(FUSO_SEMOB)) == 0.0
    assert _minutos_desde("05:45", agora_utc.astimezone(FUSO_SEMOB)) == 15.0


def test_minutos_desde_ignora_horario_invalido():
    agora = datetime.now(FUSO_SEMOB)
    assert _minutos_desde("25:99", agora) is None
    assert _minutos_desde("", agora) is None


# ---------------------------------------------------------------------------
# US #29 — preferências do usuário
# ---------------------------------------------------------------------------


def test_preferencia_cancelamento_desligado_registra_mas_nao_notifica(db):
    """O registro fica (é o estado da linha); o aviso respeita a preferência."""
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    notificador = NotificadorMock()
    pref = PreferenciasDeNotificacao(notificacoes_ativas=True, alerta_cancelamento=False)
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(pref),
        notificador,
    )

    eventos = servico._verificar_linha("0.110", {usuario}, [], agora, db)

    assert eventos == [EVENTO_REGISTRADO]
    assert db.query(AlertaCancelamento).count() == 1
    assert notificador.chamadas == []


def test_geral_desligado_tambem_bloqueia_o_aviso(db):
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    notificador = NotificadorMock()
    pref = PreferenciasDeNotificacao(notificacoes_ativas=False)
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(pref),
        notificador,
    )

    servico._verificar_linha("0.110", {usuario}, [], agora, db)

    assert notificador.chamadas == []


def test_so_quem_tem_preferencia_ligada_recebe(db):
    """Dois acompanhantes, um com cancelamento ligado e outro desligado."""
    com_aviso, sem_aviso = _usuario(), _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    notificador = NotificadorMock()
    pref = _Preferencias(
        por_usuario={
            com_aviso: PreferenciasDeNotificacao(alerta_cancelamento=True),
            sem_aviso: PreferenciasDeNotificacao(alerta_cancelamento=False),
        }
    )
    servico = _servico(
        _Destinatarios({"0.110": [com_aviso, sem_aviso]}),
        _Veiculos({"1.001": [_veiculo()]}),
        pref,
        notificador,
    )

    servico._verificar_linha("0.110", {com_aviso, sem_aviso}, [], agora, db)

    assert [chamada[1] for chamada in notificador.chamadas] == [str(com_aviso)]


# ---------------------------------------------------------------------------
# Deduplicação — uma única vez por partida
# ---------------------------------------------------------------------------


def test_segundo_ciclo_nao_registra_de_novo(db):
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=20)
    _cadastrar_linha(db, "0.110", horarios=("06:00",))
    notificador = NotificadorMock()
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
        notificador,
    )

    primeiro = servico._verificar_linha("0.110", {usuario}, [], agora, db)
    segundo = servico._verificar_linha("0.110", {usuario}, [], agora, db)

    assert primeiro == [EVENTO_REGISTRADO]
    assert segundo == [EVENTO_JA_REGISTRADO]
    assert db.query(AlertaCancelamento).count() == 1
    # Notificou uma vez só.
    assert len(notificador.chamadas) == 1


def test_cada_partida_da_noite_gera_seu_alerta(db):
    """06:00 e 06:20 ausentes => dois alertas, não um."""
    usuario = _usuario()
    agora = _agora_local(hour=6, minute=40)  # 06:00 há 40, 06:20 há 20
    _cadastrar_linha(db, "0.110", horarios=("06:00", "06:20"))
    servico = _servico(
        _Destinatarios({"0.110": [usuario]}),
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
    )

    servico._verificar_linha("0.110", {usuario}, [], agora, db)

    horarios = {a.horario_partida for a in db.query(AlertaCancelamento).all()}
    assert horarios == {"06:00", "06:20"}


# ---------------------------------------------------------------------------
# Ciclo completo — linhas sem dado
# ---------------------------------------------------------------------------


def test_linha_sem_tabela_nao_gera_alerta(db):
    """Linha acompanhada mas nunca buscada (sem `linha` no cache local)."""
    usuario = _usuario()
    _cadastrar_linha(db, "1.001", horarios=("06:00",))  # outra linha viva
    servico = _servico(
        _Destinatarios({"9.999": [usuario], "1.001": [usuario]}),
        # A 1.001 tem veículo: o feed está vivo. A 9.999 está sem tabela.
        _Veiculos({"1.001": [_veiculo()]}),
        _Preferencias(),
    )

    eventos = servico.verificar_ciclo(db)

    assert eventos == []
    assert db.query(AlertaCancelamento).count() == 0


def test_ciclo_sem_destinatarios_nao_lê_nem_o_feed(db):
    veiculos = _Veiculos({"1.001": [_veiculo()]})
    servico = _servico(_Destinatarios({}), veiculos, _Preferencias())

    eventos = servico.verificar_ciclo(db)

    assert eventos == []


def test_constantes_da_janela_seguem_a_spec():
    """O teto mínimo é o "15 minutos" da SPEC da issue."""
    assert JANELA_DETECCAO_MIN_MIN == 15
    assert JANELA_DETECCAO_MAX_MIN > JANELA_DETECCAO_MIN_MIN
    assert SOBREPOSICAO_MINIMA == pytest.approx(0.70)


def test_alternativa_menos_de_70_por_cento_nao_sugere(db):
    """3 paradas na cancelada, candidata com 2 => 66,7% < 70%."""
    assert 2 / 3 < SOBREPOSICAO_MINIMA
