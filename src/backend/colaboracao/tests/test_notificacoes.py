# Testes de integração — US #22: Receber Notificações de Rotas Preferidas
#
# Cobre todos os critérios de aceite da US #22 e os cenários da
# acceptance criteria usando os mocks de favoritos e ETA já existentes.
# Não acessa banco de dados, não usa Firebase, não cria scheduler.

import ast
import pathlib

import pytest
from fastapi.testclient import TestClient

from colaboracao.deduplicador import Deduplicador, TipoDisparo
from colaboracao.eta_service import ETAService
from colaboracao.monitoring_worker import MonitoramentoWorker
from colaboracao.providers.contratos import (
    ETAResultado,
    FavoritoMonitorado,
    FavoritosProvider,
)
from colaboracao.providers.eta_mock import ETAMockProvider
from colaboracao.providers.favoritos_mock import FavoritosMockProvider
from colaboracao.push_service import PushService

# ---------------------------------------------------------------------------
# Helpers reutilizáveis
# ---------------------------------------------------------------------------


def _fav(
    usuario_id: str,
    numero_linha: str,
    notif_ativas: bool = True,
    antecedencia_min: int = 30,
    fcm_token: str = "tok-teste",
    nome_linha: str = "Linha Teste",
) -> FavoritoMonitorado:
    return FavoritoMonitorado(
        usuario_id=usuario_id,
        fcm_token=fcm_token,
        numero_linha=numero_linha,
        nome_linha=nome_linha,
        notif_ativas=notif_ativas,
        antecedencia_min=antecedencia_min,
    )


class FakeFavoritos:
    """FavoritosProvider de teste com lista configurável."""

    def __init__(self, lista: list[FavoritoMonitorado]) -> None:
        self._lista = lista

    def listar_favoritos_com_preferencias(self) -> list[FavoritoMonitorado]:
        return self._lista


class FakeETA:
    """ETAProvider de teste com mapa {numero_linha: int|None}."""

    def __init__(self, eta_map: dict[str, int | None]) -> None:
        self._map = eta_map

    def obter_eta(self, numero_linha: str) -> ETAResultado:
        val = self._map.get(numero_linha)
        if val is None:
            return ETAResultado(numero_linha=numero_linha, eta_minutos=0, disponivel=False)
        return ETAResultado(numero_linha=numero_linha, eta_minutos=val, disponivel=True)


class FakePushFalhante:
    """PushSender que sempre retorna False."""

    def __init__(self) -> None:
        self.chamadas: list[str] = []

    def enviar_push(
        self, fcm_token: str, numero_linha: str, nome_linha: str, eta_minutos: int
    ) -> bool:
        self.chamadas.append(numero_linha)
        return False


def _worker(
    favoritos: list[FavoritoMonitorado],
    eta_map: dict[str, int | None],
    push: PushService | None = None,
    dedup: Deduplicador | None = None,
) -> tuple[MonitoramentoWorker, PushService, Deduplicador]:
    p = push or PushService()
    d = dedup or Deduplicador()
    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos(favoritos),
        eta_service=ETAService(FakeETA(eta_map)),
        push_sender=p,
        deduplicador=d,
    )
    return w, p, d


# ---------------------------------------------------------------------------
# CRITÉRIO DE ACEITE 1 — Notificação de ônibus próximo (ETA ≤ 5 min)
# ---------------------------------------------------------------------------


def test_ac1_notificacao_onibus_proximo_envia_push():
    """ETA=5 deve disparar PROXIMIDADE e enviar exatamente 1 push."""
    w, push, _ = _worker([_fav("u1", "0.110")], {"0.110": 5})
    resultados = w.executar_ciclo()

    assert len(resultados) == 1
    assert resultados[0].enviado is True
    assert resultados[0].tipo_disparo == TipoDisparo.PROXIMIDADE
    assert push.total_enviadas() == 1


def test_ac1_payload_contem_dados_da_linha():
    """Payload da notificação deve conter numero_linha, nome_linha e eta_minutos."""
    w, push, _ = _worker(
        [_fav("u1", "0.110", nome_linha="0.110 — Taguatinga")], {"0.110": 5}
    )
    w.executar_ciclo()

    notif = push.ultima()
    assert notif is not None
    assert notif.data["numero_linha"] == "0.110"
    assert notif.data["nome_linha"] == "0.110 — Taguatinga"
    assert notif.data["eta_minutos"] == "5"


def test_ac1_sem_duplicata_no_segundo_ciclo():
    """Segundo ciclo com ETA ainda ≤ 5 não deve gerar novo push."""
    w, push, _ = _worker([_fav("u1", "0.110")], {"0.110": 5})
    w.executar_ciclo()  # envia
    w.executar_ciclo()  # deve ser bloqueado pelo deduplicador
    assert push.total_enviadas() == 1


# ---------------------------------------------------------------------------
# CRITÉRIO DE ACEITE 2 — Notificação com antecedência configurada (30 min)
# ---------------------------------------------------------------------------


def test_ac2_notificacao_antecedencia_30min():
    """ETA=30 com antecedencia_min=30 deve disparar ANTECEDENCIA."""
    w, push, _ = _worker(
        [_fav("u1", "0.110", antecedencia_min=30)], {"0.110": 30}
    )
    resultados = w.executar_ciclo()

    assert resultados[0].tipo_disparo == TipoDisparo.ANTECEDENCIA
    assert push.total_enviadas() == 1


def test_ac2_sem_repeticao_enquanto_eta_elegivel():
    """Ciclos consecutivos com ETA=30 não devem repetir a notificação."""
    w, push, _ = _worker(
        [_fav("u1", "0.110", antecedencia_min=30)], {"0.110": 30}
    )
    w.executar_ciclo()
    w.executar_ciclo()
    w.executar_ciclo()
    assert push.total_enviadas() == 1


def test_ac2_eta_acima_da_antecedencia_nao_envia():
    """ETA=35 com antecedencia_min=30 não deve enviar (acima do limiar)."""
    w, push, _ = _worker(
        [_fav("u1", "0.110", antecedencia_min=30)], {"0.110": 35}
    )
    w.executar_ciclo()
    assert push.total_enviadas() == 0


# ---------------------------------------------------------------------------
# CRITÉRIO DE ACEITE 3 — Respeitar notificações desabilitadas
# ---------------------------------------------------------------------------


def test_ac3_notificacoes_desabilitadas_sem_push():
    """notif_ativas=False deve ignorar completamente o favorito."""
    w, push, dedup = _worker(
        [_fav("u1", "0.110", notif_ativas=False)], {"0.110": 5}
    )
    resultados = w.executar_ciclo()

    assert resultados[0].enviado is False
    assert resultados[0].motivo_skip == "notificacoes_desativadas"
    assert push.total_enviadas() == 0
    assert dedup.total_corridas_ativas() == 0


def test_ac3_eta_nao_consultado_quando_desabilitado():
    """Favorito desabilitado não deve consultar o ETAProvider."""

    class ETASpy:
        def __init__(self) -> None:
            self.chamadas = 0

        def obter_eta(self, numero_linha: str) -> ETAResultado:
            self.chamadas += 1
            return ETAResultado(numero_linha=numero_linha, eta_minutos=5, disponivel=True)

    spy = ETASpy()
    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos([_fav("u1", "0.110", notif_ativas=False)]),
        eta_service=ETAService(spy),
        push_sender=PushService(),
        deduplicador=Deduplicador(),
    )
    w.executar_ciclo()
    assert spy.chamadas == 0


# ---------------------------------------------------------------------------
# CENÁRIO 4 — Fluxo completo: ETA>30 → ETA=30 → ETA=5 → 2 notificações
# ---------------------------------------------------------------------------


def test_fluxo_completo_dois_disparos_exatos():
    """Corrida completa deve gerar exatamente ANTECEDENCIA + PROXIMIDADE."""
    push = PushService()
    dedup = Deduplicador()
    fav = _fav("u1", "0.110", antecedencia_min=30)

    # Fase 1: ETA acima do limiar → nenhum envio
    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos([fav]),
        eta_service=ETAService(FakeETA({"0.110": 35})),
        push_sender=push,
        deduplicador=dedup,
    )
    w.executar_ciclo()
    assert push.total_enviadas() == 0

    # Fase 2: ETA cruza antecedência → ANTECEDENCIA
    w._eta = ETAService(FakeETA({"0.110": 30}))
    w.executar_ciclo()
    assert push.total_enviadas() == 1
    assert push.notificacoes_enviadas[0].data["eta_minutos"] == "30"

    # Fase 3: ciclos intermediários → sem novo envio
    w._eta = ETAService(FakeETA({"0.110": 20}))
    w.executar_ciclo()
    w.executar_ciclo()
    assert push.total_enviadas() == 1

    # Fase 4: ETA ≤ 5 → PROXIMIDADE
    w._eta = ETAService(FakeETA({"0.110": 5}))
    w.executar_ciclo()
    assert push.total_enviadas() == 2
    assert push.notificacoes_enviadas[1].data["eta_minutos"] == "5"

    # Fase 5: segundo ciclo com ETA=5 → sem spam
    w.executar_ciclo()
    assert push.total_enviadas() == 2


# ---------------------------------------------------------------------------
# CENÁRIO 5 — Usuários independentes
# ---------------------------------------------------------------------------


def test_usuarios_independentes():
    """Estado de deduplicação de u1 não deve afetar u2."""
    push = PushService()
    dedup = Deduplicador()
    favs = [
        _fav("u1", "0.110", fcm_token="tok-u1"),
        _fav("u2", "0.110", fcm_token="tok-u2"),
    ]

    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos(favs),
        eta_service=ETAService(FakeETA({"0.110": 30})),
        push_sender=push,
        deduplicador=dedup,
    )
    w.executar_ciclo()

    assert push.total_enviadas() == 2
    # Cada usuário recebeu exatamente um push com seu próprio token
    tokens = [n.fcm_token for n in push.notificacoes_enviadas]
    assert "tok-u1" in tokens
    assert "tok-u2" in tokens


def test_usuarios_dedup_independente_no_segundo_ciclo():
    """u1 bloqueado não bloqueia u2 no segundo ciclo."""
    push = PushService()
    dedup = Deduplicador()
    favs = [_fav("u1", "0.110", fcm_token="tok-u1"), _fav("u2", "0.110", fcm_token="tok-u2")]

    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos(favs),
        eta_service=ETAService(FakeETA({"0.110": 30})),
        push_sender=push,
        deduplicador=dedup,
    )
    w.executar_ciclo()  # 2 pushs: u1 e u2
    assert push.total_enviadas() == 2

    w.executar_ciclo()  # ambos bloqueados
    assert push.total_enviadas() == 2

    # Reseta só u1 — apenas u1 deve enviar de novo
    dedup.resetar_corrida("u1", "0.110")
    w.executar_ciclo()
    assert push.total_enviadas() == 3
    assert push.ultima().fcm_token == "tok-u1"


# ---------------------------------------------------------------------------
# CENÁRIO 6 — Linhas independentes
# ---------------------------------------------------------------------------


def test_linhas_independentes():
    """Estado de 0.110 não deve afetar 0.108."""
    push = PushService()
    favs = [_fav("u1", "0.110"), _fav("u1", "0.108")]

    w, push, _ = _worker(favs, {"0.110": 30, "0.108": 30}, push=push)
    w.executar_ciclo()
    assert push.total_enviadas() == 2
    linhas = [n.data["numero_linha"] for n in push.notificacoes_enviadas]
    assert "0.110" in linhas
    assert "0.108" in linhas


# ---------------------------------------------------------------------------
# CENÁRIO 7 — Falha no PushSender
# ---------------------------------------------------------------------------


def test_falha_push_nao_registra_no_dedup():
    """Quando PushSender retorna False, Deduplicador não deve registrar."""
    push_falho = FakePushFalhante()
    dedup = Deduplicador()
    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos([_fav("u1", "0.110")]),
        eta_service=ETAService(FakeETA({"0.110": 30})),
        push_sender=push_falho,
        deduplicador=dedup,
    )
    r = w.executar_ciclo()

    assert r[0].enviado is False
    est = dedup.estado("u1", "0.110")
    assert est.antecedencia_enviada is False


def test_falha_push_permite_tentativa_posterior():
    """Após falha, o próximo ciclo deve tentar novamente."""
    push_falho = FakePushFalhante()
    dedup = Deduplicador()
    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos([_fav("u1", "0.110")]),
        eta_service=ETAService(FakeETA({"0.110": 30})),
        push_sender=push_falho,
        deduplicador=dedup,
    )
    w.executar_ciclo()  # falha → não registra
    w.executar_ciclo()  # deve tentar de novo

    assert len(push_falho.chamadas) == 2, (
        f"Esperado 2 tentativas, recebido {len(push_falho.chamadas)}"
    )


def test_falha_em_favorito_nao_interrompe_proximos():
    """Falha no push do favorito A não deve impedir processamento do favorito B."""
    push_falho = FakePushFalhante()
    favs = [_fav("u1", "0.110"), _fav("u2", "0.108")]
    w = MonitoramentoWorker(
        favoritos_provider=FakeFavoritos(favs),
        eta_service=ETAService(FakeETA({"0.110": 30, "0.108": 30})),
        push_sender=push_falho,
        deduplicador=Deduplicador(),
    )
    resultados = w.executar_ciclo()

    assert len(resultados) == 2
    assert len(push_falho.chamadas) == 2  # ambos foram tentados


# ---------------------------------------------------------------------------
# CENÁRIO 8 — ETA indisponível
# ---------------------------------------------------------------------------


def test_eta_indisponivel_sem_push():
    """ETA indisponível não deve gerar push nem registrar no Deduplicador."""
    w, push, dedup = _worker([_fav("u1", "0.110")], {"0.110": None})
    r = w.executar_ciclo()

    assert push.total_enviadas() == 0
    assert r[0].motivo_skip == "eta_indisponivel"
    assert dedup.total_corridas_ativas() == 0


# ---------------------------------------------------------------------------
# CENÁRIO 9 — Validação do payload
# ---------------------------------------------------------------------------


def test_payload_titulo_proximidade():
    """ETA ≤ 5 deve gerar title 'Ônibus próximo'."""
    w, push, _ = _worker(
        [_fav("u1", "0.110", nome_linha="0.110 — Taguatinga")], {"0.110": 4}
    )
    w.executar_ciclo()
    assert push.ultima().title == "Ônibus próximo"


def test_payload_titulo_antecedencia():
    """ETA > 5 (dentro da antecedência) deve gerar title 'Lembrete de rota'."""
    w, push, _ = _worker(
        [_fav("u1", "0.110", antecedencia_min=30)], {"0.110": 30}
    )
    w.executar_ciclo()
    assert push.ultima().title == "Lembrete de rota"


def test_payload_campos_obrigatorios():
    """Payload deve conter numero_linha, nome_linha e eta_minutos como string."""
    w, push, _ = _worker(
        [_fav("u1", "0.110", nome_linha="Linha Centro", antecedencia_min=30)],
        {"0.110": 30},
    )
    w.executar_ciclo()
    data = push.ultima().data
    assert "numero_linha" in data
    assert "nome_linha" in data
    assert "eta_minutos" in data
    assert data["numero_linha"] == "0.110"
    assert data["nome_linha"] == "Linha Centro"
    assert isinstance(data["eta_minutos"], str)  # FCM exige string


# ---------------------------------------------------------------------------
# CENÁRIO 10 — Testes da rota HTTP POST /colaboracao/notificacoes/processar
# ---------------------------------------------------------------------------

from colaboracao.main import app  # noqa: E402

_client = TestClient(app)


def test_rota_existe():
    """Rota POST /colaboracao/notificacoes/processar deve existir."""
    response = _client.post("/colaboracao/notificacoes/processar")
    assert response.status_code != 404, "Rota não encontrada (404)"


def test_rota_aceita_post():
    """Método POST deve ser aceito (não 405)."""
    response = _client.post("/colaboracao/notificacoes/processar")
    assert response.status_code != 405, "Método POST não permitido (405)"


def test_rota_retorna_200():
    """Rota deve retornar HTTP 200."""
    response = _client.post("/colaboracao/notificacoes/processar")
    assert response.status_code == 200


def test_rota_retorna_json_com_status():
    """Resposta deve conter o campo 'status' com valor 'ciclo_processado'."""
    response = _client.post("/colaboracao/notificacoes/processar")
    data = response.json()
    assert "status" in data
    assert data["status"] == "ciclo_processado"


def test_rota_retorna_campos_de_resumo():
    """Resposta deve conter 'processados', 'enviados' e 'itens'."""
    response = _client.post("/colaboracao/notificacoes/processar")
    data = response.json()
    assert "processados" in data
    assert "enviados" in data
    assert "itens" in data
    assert isinstance(data["itens"], list)


def test_rota_ciclo_executado_processa_favoritos():
    """Resposta deve indicar que ao menos um favorito foi processado."""
    response = _client.post("/colaboracao/notificacoes/processar")
    data = response.json()
    assert data["processados"] >= 1, "Nenhum favorito foi processado"


def test_rota_itens_possuem_campos_esperados():
    """Cada item do resultado deve ter os campos definidos em ResultadoCicloItem."""
    response = _client.post("/colaboracao/notificacoes/processar")
    itens = response.json()["itens"]
    assert len(itens) >= 1
    for item in itens:
        assert "usuario_id" in item
        assert "numero_linha" in item
        assert "enviado" in item


def test_rota_nao_importa_firebase_celery():
    """routes.py não deve importar firebase_admin, celery ou apscheduler."""
    routes_path = pathlib.Path(__file__).resolve().parents[1] / "routes.py"
    fonte = routes_path.read_text()
    tree = ast.parse(fonte)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    proibidos = ["firebase_admin", "celery", "apscheduler"]
    for p in proibidos:
        assert not any(p in i.lower() for i in imports), f"routes.py importa {p!r}"


def test_rota_get_nao_aceita():
    """GET em /processar deve retornar 405 (somente POST aceito)."""
    response = _client.get("/colaboracao/notificacoes/processar")
    assert response.status_code == 405
