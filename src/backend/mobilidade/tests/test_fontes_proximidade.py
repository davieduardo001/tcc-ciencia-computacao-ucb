from types import SimpleNamespace
from unittest.mock import MagicMock

from mobilidade.providers.contratos_proximidade import (
    PreferenciasDeNotificacao,
    ViagensAtivasProvisorias,
)
from mobilidade.providers.preferencias_banco import PreferenciasDoBanco
from mobilidade.providers.veiculos_ao_vivo import VeiculosAoVivo


# ---------------------------------------------------------------------------
# PreferenciasDoBanco — leitura das preferências da US #29
# ---------------------------------------------------------------------------


def test_preferencias_padrao_quando_usuario_sem_registro():
    db = MagicMock()
    db.execute.return_value.first.return_value = None

    pref = PreferenciasDoBanco().obter(MagicMock(), db)

    assert pref.notificacoes_ativas is True
    assert pref.alerta_chegada is True
    assert pref.antecedencia_minutos == 30


def test_preferencias_usa_valores_do_registro():
    db = MagicMock()
    db.execute.return_value.first.return_value = SimpleNamespace(
        notificacoes_ativas=False,
        alerta_chegada=True,
        antecedencia_minutos=10,
    )

    pref = PreferenciasDoBanco().obter(MagicMock(), db)

    assert pref.notificacoes_ativas is False
    assert pref.alerta_chegada is True
    assert pref.antecedencia_minutos == 10


def test_preferencias_falha_de_leitura_desliga_notificacoes():
    # Sem confirmar o que o usuário pediu, o caminho seguro é não
    # incomodar — e o worker tenta de novo no ciclo seguinte.
    db = MagicMock()
    db.execute.side_effect = RuntimeError("banco indisponivel")

    pref = PreferenciasDoBanco().obter(MagicMock(), db)

    assert pref.notificacoes_ativas is False
    assert pref.alerta_chegada is False


def test_preferencias_antecedencia_invalida_cai_no_padrao():
    db = MagicMock()
    db.execute.return_value.first.return_value = SimpleNamespace(
        notificacoes_ativas=True,
        alerta_chegada=True,
        antecedencia_minutos=0,
    )

    pref = PreferenciasDoBanco().obter(MagicMock(), db)

    assert pref.antecedencia_minutos == 30


# ---------------------------------------------------------------------------
# VeiculosAoVivo — feed do SEMOB (US #16) para o worker
# ---------------------------------------------------------------------------


class _PosicaoStub:
    def __init__(self, retorno=None, falhar=False):
        self._retorno = retorno or {}
        self._falhar = falhar
        self.chamadas = 0

    async def posicoes_das_linhas(self, numeros_linha):
        self.chamadas += 1
        if self._falhar:
            raise RuntimeError("timeout no SEMOB")
        return {n: self._retorno.get(n, []) for n in numeros_linha}


def test_veiculos_sem_linhas_nao_chama_a_fonte():
    stub = _PosicaoStub()

    resultado = VeiculosAoVivo(stub).obter_das_linhas(set())

    assert resultado == {}
    assert stub.chamadas == 0


def test_veiculos_devolve_o_que_a_fonte_trouxe():
    stub = _PosicaoStub(retorno={"0.110": ["veiculo-a"]})

    resultado = VeiculosAoVivo(stub).obter_das_linhas({"0.110"})

    assert resultado == {"0.110": ["veiculo-a"]}
    assert stub.chamadas == 1


def test_veiculos_falha_na_fonte_retorna_vazio():
    # Cenário 4: fonte indisponível não pode virar alerta impreciso —
    # e muito menos derrubar o job do APScheduler.
    stub = _PosicaoStub(falhar=True)

    resultado = VeiculosAoVivo(stub).obter_das_linhas({"0.110"})

    assert resultado == {}


# ---------------------------------------------------------------------------
# ViagensAtivasProvisorias — placeholder da US #171
# ---------------------------------------------------------------------------


def test_viagens_provisorias_retorna_vazio():
    # Enquanto a #171 não existir, não há viagem e não há alerta.
    assert ViagensAtivasProvisorias().listar_ativas() == []


def test_contrato_de_preferencias_padrao():
    padrao = PreferenciasDeNotificacao()
    assert padrao.notificacoes_ativas is True
    assert padrao.alerta_chegada is True
    assert padrao.antecedencia_minutos == 30
