"""
US #199 — fallback colaborativo: armazenamento efêmero, validação de
leitura e produção do veículo "colaborativo".

Estes testes usam SQLite em memória com SÓ a tabela `viagem` (as leituras
nunca tocam banco) e dublês do trajeto — a regra de encaixe (RN-C4) e os
contratos do ETA por trajeto são da geometria real, testados lá.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mobilidade.geometria import TrajetoMedido
from mobilidade.models import Rota
from mobilidade.models.viagem import Viagem
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.posicoes_colaborativas import (
    INTERVALO_MINIMO_ENVIO_S,
    LEITURAS_MAXIMAS,
    MOTIVO_ACEITA,
    MOTIVO_FORA_DO_TRACADO,
    MOTIVO_VELOCIDADE_IMPOSSIVEL,
    ArmazenamentoEmMemoria,
    EnvioAdiantado,
    LeituraColaborativa,
    ServicoPosicoesColaborativas,
)

USUARIO = uuid.UUID("00000000-0000-4000-8000-000000000199")

# Traçado reto leste–oeste (~11 km, vértices a ~530 m como o feed real),
# com uma leitura bem no meio dele, outra a ~55 m (dentro das 150 m do
# RN-C4) e outra a ~3,3 km para o norte.
TRACADO = [(-15.80, -48.10 + 0.005 * i) for i in range(21)]
NO_MEIO = (-15.80, -48.05)
LEVEMENTE_EM = (-15.8005, -48.05)
FORA_DA_LINHA = (-15.83, -48.05)


def _instante(segundos_atras: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=segundos_atras)


def _leitura(segundos_atras: float, ponto=NO_MEIO) -> LeituraColaborativa:
    return LeituraColaborativa(
        instante=_instante(segundos_atras), lat=ponto[0], lng=ponto[1]
    )


class _Trajetos:
    """Dublê do RotaService: devolve trajeto só para os sentidos declarados."""

    def __init__(self, por_sentido: dict[str, list[tuple[float, float]]]):
        self._por_sentido = {
            sentido.strip().upper(): TrajetoMedido(pontos)
            for sentido, pontos in por_sentido.items()
        }

    def trajeto_medido(self, db, numero, sentido=None):
        medido = self._por_sentido.get((sentido or "").strip().upper())
        if medido is None:
            return None
        return (medido, sentido)


@pytest.fixture
def db():
    """Sessão SQLite em memória com só as tabelas `viagem` e `rota`."""
    engine = create_engine("sqlite://")
    Viagem.__table__.create(engine)
    Rota.__table__.create(engine)
    sessao = sessionmaker(bind=engine)()
    # Sentidos da linha conforme o serviço real lê da base (RN-C4).
    sessao.add(
        Rota(numero="0.001", sentido="IDA", nome="Linha 0.001", trajeto=[], paradas=[])
    )
    sessao.add(
        Rota(numero="0.001", sentido="VOLTA", nome="Linha 0.001", trajeto=[], paradas=[])
    )
    sessao.commit()
    yield sessao
    sessao.close()


def _viagem_na_sessao(
    db,
    *,
    linha="0.001",
    compartilha=True,
    encerrada=False,
    prefixo="440001",
    sentido="IDA",
    usuario=USUARIO,
) -> Viagem:
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    viagem = Viagem(
        usuario_id=usuario or uuid.uuid4(),
        numero_linha=linha,
        sentido=sentido,
        veiculo_prefixo=prefixo,
        embarcou_em=agora,
        encerrada_em=agora if encerrada else None,
        motivo_encerramento="usuario" if encerrada else None,
        origem_embarque="manual",
        compartilha_posicao_em=agora if compartilha else None,
        consentimento_versao="v1" if compartilha else None,
    )
    db.add(viagem)
    db.commit()
    return viagem


def _semob(
    prefixo="999999",
    ponto=LEVEMENTE_EM,
    sentido="IDA",
    idade_s=5,
    fonte="ao_vivo",
) -> PosicaoVeiculo:
    return PosicaoVeiculo(
        prefixo=prefixo,
        lat=ponto[0],
        lng=ponto[1],
        sentido=sentido,
        velocidade=30.0,
        direcao=90.0,
        atualizado_em=_instante(idade_s),
        operadora="SEMOB TESTE",
        fonte=fonte,
    )


# ==========================================================================
# Armazenamento (guardar / obter / apagar / expirar)
# ==========================================================================


def test_guardar_e_obter_devolve_as_leituras_guardadas():
    armazenamento = ArmazenamentoEmMemoria()
    armazenamento.guardar(uuid.UUID(int=1), _leitura(60, NO_MEIO))
    armazenamento.guardar(uuid.UUID(int=1), _leitura(10, LEVEMENTE_EM))

    leituras = armazenamento.obter(uuid.UUID(int=1))

    assert [l.lat for l in leituras] == [NO_MEIO[0], LEVEMENTE_EM[0]]
    assert [l.lng for l in leituras] == [NO_MEIO[1], LEVEMENTE_EM[1]]


def test_obter_nao_devolve_leitura_vencida():
    armazenamento = ArmazenamentoEmMemoria()
    armazenamento.guardar(uuid.UUID(int=1), _leitura(60))
    armazenamento.guardar(uuid.UUID(int=1), _leitura(121))  # vencida (>120 s)

    restantes = armazenamento.obter(uuid.UUID(int=1))

    # a de 121 s venceu; a de 60 s ainda está boa → sobra uma
    assert len(restantes) == 1
    # e a poda aconteceu na própria leitura: nada volta depois
    assert armazenamento.obter(uuid.UUID(int=1)) == restantes


def test_obter_de_viagem_desconhecida_e_lista_vazia():
    assert ArmazenamentoEmMemoria().obter(uuid.UUID(int=42)) == []


def test_apagar_limpa_a_leitura_na_hora():
    armazenamento = ArmazenamentoEmMemoria()
    armazenamento.guardar(uuid.UUID(int=1), _leitura(10))

    armazenamento.apagar(uuid.UUID(int=1))

    assert armazenamento.obter(uuid.UUID(int=1)) == []


def test_expirar_conta_descartadas_e_mantem_ao_vivo():
    armazenamento = ArmazenamentoEmMemoria()
    armazenamento.guardar(uuid.UUID(int=1), _leitura(10))
    armazenamento.guardar(uuid.UUID(int=1), _leitura(200))  # vencida
    armazenamento.guardar(uuid.UUID(int=2), _leitura(300))  # vencida

    assert armazenamento.expirar() == 2
    assert len(armazenamento.obter(uuid.UUID(int=1))) == 1
    assert armazenamento.obter(uuid.UUID(int=2)) == []


def test_o_teto_de_leituras_e_respeitado():
    armazenamento = ArmazenamentoEmMemoria()
    for i in range(LEITURAS_MAXIMAS + 5):
        armazenamento.guardar(uuid.UUID(int=1), _leitura(10 + i * 0.1))

    assert len(armazenamento.obter(uuid.UUID(int=1))) == LEITURAS_MAXIMAS


# ==========================================================================
# registrar — anti-martelada, velocidade impossível, traçado
# ==========================================================================


def _servico(intervalo_s: float = 0.0) -> ServicoPosicoesColaborativas:
    # intervalo 0 nos testes de regra; o intervalo real tem teste próprio
    return ServicoPosicoesColaborativas(intervalo_minimo_s=intervalo_s)


def _registrar(
    servico, viagem, ponto, *, db, agora=None, trajetos=_Trajetos({"IDA": TRACADO, "VOLTA": TRACADO})
):
    return servico.registrar(
        db, viagem, ponto[0], ponto[1], rota_service=trajetos, agora=agora or _instante(0)
    )


def test_primeira_leitura_dentro_do_tracado_e_aceita(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()

    assert _registrar(servico, viagem, NO_MEIO, db=db) == MOTIVO_ACEITA
    assert len(servico._armazenamento.obter(viagem.id)) == 1


def test_leitura_fora_do_tracado_e_descartada_sem_guardar(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()

    assert _registrar(servico, viagem, FORA_DA_LINHA, db=db) == MOTIVO_FORA_DO_TRACADO
    assert servico._armazenamento.obter(viagem.id) == []


def test_linha_sem_tracado_ingerido_nao_recebe_leitura(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()

    motivo = servico.registrar(
        db, viagem, *NO_MEIO, rota_service=_Trajetos({}), agora=_instante(0)
    )

    assert motivo == MOTIVO_FORA_DO_TRACADO


def test_salto_mais_rapido_que_onibus_algum_e_descartado(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()
    t0 = _instante(20)

    assert _registrar(servico, viagem, NO_MEIO, db=db, agora=t0) == MOTIVO_ACEITA

    # ~500 m em 10 s ≈ 180 km/h: nenhum ônibus faz isso (RN-C4b).
    salto = (-15.8045, -48.05)
    motivo = servico.registrar(
        db,
        viagem,
        salto[0],
        salto[1],
        rota_service=_Trajetos({"IDA": TRACADO, "VOLTA": TRACADO}),
        agora=t0 + timedelta(seconds=10),
    )

    assert motivo == MOTIVO_VELOCIDADE_IMPOSSIVEL
    leituras = servico._armazenamento.obter(viagem.id)
    assert len(leituras) == 1  # o salto não entrou no histórico
    assert leituras[0].lat == NO_MEIO[0]


def test_respeita_o_intervalo_minimo_de_envio(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico(INTERVALO_MINIMO_ENVIO_S)

    assert _registrar(servico, viagem, NO_MEIO, db=db) == MOTIVO_ACEITA

    with pytest.raises(EnvioAdiantado):
        _registrar(servico, viagem, LEVEMENTE_EM, db=db)


def test_passado_o_intervalo_aceita_de_novo(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico(INTERVALO_MINIMO_ENVIO_S)
    t0 = _instante(30)

    assert _registrar(servico, viagem, NO_MEIO, db=db, agora=t0) == MOTIVO_ACEITA
    # o relógio interno da viagem recua o equivalente a um intervalo — em
    # produção quem espera é o cliente, aqui simulamos o tempo ter passado.
    servico._ultimo_envio[viagem.id] -= INTERVALO_MINIMO_ENVIO_S + 0.1

    assert (
        _registrar(servico, viagem, LEVEMENTE_EM, db=db, agora=t0 + timedelta(seconds=10))
        == MOTIVO_ACEITA
    )


# ==========================================================================
# veiculos — o fallback e a prioridade da SEMOB (RN-C2)
# ==========================================================================


def _semear_leituras(servico, viagem_id, pontos, agora):
    inicio = agora - timedelta(seconds=60)
    for i, ponto in enumerate(pontos):
        servico._armazenamento.guardar(
            viagem_id,
            LeituraColaborativa(
                instante=inicio + timedelta(seconds=i * 30), lat=ponto[0], lng=ponto[1]
            ),
        )


def test_viagem_compartilhando_gera_veiculo_colaborativo(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()
    agora = datetime.now(timezone.utc)
    _semear_leituras(servico, viagem.id, [NO_MEIO, LEVEMENTE_EM], agora)

    veiculos = servico.veiculos(db, {"0.001"}, {}, agora)["0.001"]

    assert len(veiculos) == 1
    v = veiculos[0]
    assert v.fonte == "colaborativo"
    assert v.operadora == "colaborativo"
    assert v.prefixo == "440001"  # o do ônibus em que embarcou
    assert v.sentido == "IDA"
    assert (v.lat, v.lng) == LEVEMENTE_EM  # a última leitura vence
    assert v.velocidade is None
    assert v.velocidade_media_kmh is not None  # 60 s de janela ≥ 30 s


def test_uma_leitura_so_bem_veiculo_sem_media(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()
    agora = datetime.now(timezone.utc)
    _semear_leituras(servico, viagem.id, [NO_MEIO], agora)

    veiculos = servico.veiculos(db, {"0.001"}, {}, agora)["0.001"]

    assert len(veiculos) == 1
    assert veiculos[0].velocidade_media_kmh is None


def test_viagens_encerradas_sem_consentimento_ou_de_outra_linha_sao_ignoradas(db):
    _viagem_na_sessao(db, encerrada=True, usuario=None)
    _viagem_na_sessao(db, compartilha=False, usuario=None)
    _viagem_na_sessao(db, linha="0.002", usuario=None)  # ativa e compartilhando, mas de outra linha
    servico = _servico()
    agora = datetime.now(timezone.utc)

    assert servico.veiculos(db, {"0.001"}, {}, agora) == {}


def test_onibus_da_semob_com_o_mesmo_prefixo_vence(db):
    viagem = _viagem_na_sessao(db, prefixo="440001")
    servico = _servico()
    agora = datetime.now(timezone.utc)
    _semear_leituras(servico, viagem.id, [NO_MEIO, LEVEMENTE_EM], agora)

    resultado = servico.veiculos(
        db, {"0.001"}, {"0.001": [_semob(prefixo="440001")]}, agora
    )

    assert resultado == {}  # RN-C2: o feed da SEMOB cobre, o fallback fica fora


def test_onibus_da_semob_do_lado_da_leitura_vence(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()
    agora = datetime.now(timezone.utc)
    _semear_leituras(servico, viagem.id, [NO_MEIO, LEVEMENTE_EM], agora)

    # Outro prefixo, mesmo sentido, a ~78 m da leitura: cobertura SEMOB.
    perto = (-15.8007, NO_MEIO[1])
    resultado = servico.veiculos(
        db,
        {"0.001"},
        {"0.001": [_semob(prefixo="999999", ponto=perto, sentido="IDA")]},
        agora,
    )

    assert resultado == {}


def test_onibus_da_semob_de_sentido_oposto_nao_cobre(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()
    agora = datetime.now(timezone.utc)
    _semear_leituras(servico, viagem.id, [NO_MEIO, LEVEMENTE_EM], agora)

    resultado = servico.veiculos(
        db,
        {"0.001"},
        {"0.001": [_semob(prefixo="999999", ponto=LEVEMENTE_EM, sentido="VOLTA")]},
        agora,
    )

    assert len(resultado["0.001"]) == 1  # a leitura segue colaborativa


def test_veiculos_da_linha_errada_nao_interferem(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()
    agora = datetime.now(timezone.utc)
    _semear_leituras(servico, viagem.id, [NO_MEIO, LEVEMENTE_EM], agora)

    resultado = servico.veiculos(
        db, {"0.001"}, {"0.002": [_semob(prefixo="440001")]}, agora
    )

    assert len(resultado["0.001"]) == 1


def test_velocidade_media_acima_do_teto_e_cortada(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()
    agora = datetime.now(timezone.utc)
    # Semeadas DIRETO no armazenamento para testar só o teto: ~2,1 km em 30 s
    # seria recusado pelo registrar (RN-C4b) — aqui a regra é a da média.
    _semear_leituras(servico, viagem.id, [(-15.80, -48.07), NO_MEIO], agora)

    veiculo = servico.veiculos(db, {"0.001"}, {}, agora)["0.001"][0]

    assert veiculo.velocidade_media_kmh == 90.0


# ==========================================================================
# Revogação e LGPD (nem o log guarda coordenada)
# ==========================================================================


def test_apagar_limpa_leituras_e_o_limite_de_envio(db):
    viagem = _viagem_na_sessao(db)
    servico = _servico()

    assert _registrar(servico, viagem, NO_MEIO, db=db) == MOTIVO_ACEITA

    servico.apagar(viagem.id)

    assert servico._armazenamento.obter(viagem.id) == []
    assert viagem.id not in servico._ultimo_envio


def test_nenhuma_coordenada_aparece_em_log(db, caplog):
    viagem = _viagem_na_sessao(db)
    servico = _servico()

    with caplog.at_level(logging.DEBUG, logger="mobilidade.posicoes_colaborativas"):
        assert _registrar(servico, viagem, NO_MEIO, db=db) == MOTIVO_ACEITA
        _registrar(servico, viagem, FORA_DA_LINHA, db=db)
        assert servico.veiculos(db, {"0.001"}, {}, datetime.now(timezone.utc))

    texto = caplog.text
    for ponto in (NO_MEIO, LEVEMENTE_EM, FORA_DA_LINHA):
        assert str(ponto[0]) not in texto
        assert str(ponto[1]) not in texto
