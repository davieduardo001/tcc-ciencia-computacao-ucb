from fastapi import APIRouter

from colaboracao.deduplicador import Deduplicador
from colaboracao.eta_service import ETAService
from colaboracao.monitoring_worker import MonitoramentoWorker
from colaboracao.providers.eta_mock import ETAMockProvider
from colaboracao.providers.favoritos_mock import FavoritosMockProvider
from colaboracao.push_service import PushService

router = APIRouter()

# ---------------------------------------------------------------------------
# Estado compartilhado da demonstração da US #22
#
# Instâncias mantidas em memória durante a vida do processo para que o
# Deduplicador e o PushService preservem estado entre chamadas à rota.
# Em produção, esses objetos serão substituídos pelas implementações reais
# (US #25, #29, #19) sem alterar esta rota.
# ---------------------------------------------------------------------------
_demo_push      = PushService()
_demo_dedup     = Deduplicador()
_demo_eta       = ETAService(ETAMockProvider())
_demo_favoritos = FavoritosMockProvider()

_demo_worker = MonitoramentoWorker(
    favoritos_provider=_demo_favoritos,
    eta_service=_demo_eta,
    push_sender=_demo_push,
    deduplicador=_demo_dedup,
)


@router.get("/hello")
def hello():
    return {"service": "colaboracao", "status": "ok"}


@router.get("/teste-vitoria")
def teste_vitoria():
    return {"service": "colaboracao", "autor": "Vitoria-Albuquerque", "mensagem": "hello world"}


@router.get("/teste-gualberto")
def teste_gualberto():
    return {"service": "colaboracao", "autor": "gualbertonathalia", "mensagem": "hello world"}


# ---------------------------------------------------------------------------
# US #22 — Rota de demonstração / teste do Worker de monitoramento
# ---------------------------------------------------------------------------

@router.post("/notificacoes/processar")
def processar_ciclo_notificacoes():
    """
    Executa exatamente UM ciclo do MonitoramentoWorker.

    Utiliza mocks de favoritos e ETA enquanto as US #25, #29 e #19
    não estiverem implementadas. Não cria loop infinito, não agenda
    tarefas em background.

    Retorna um resumo do ciclo: quantos favoritos foram processados,
    quantas notificações foram enviadas e o detalhe de cada item.
    """
    resultados = _demo_worker.executar_ciclo()

    itens = [
        {
            "usuario_id":   r.usuario_id,
            "numero_linha": r.numero_linha,
            "eta_minutos":  r.eta_minutos,
            "tipo_disparo": r.tipo_disparo.value if r.tipo_disparo else None,
            "enviado":      r.enviado,
            "motivo_skip":  r.motivo_skip,
        }
        for r in resultados
    ]

    return {
        "status":       "ciclo_processado",
        "processados":  len(itens),
        "enviados":     sum(1 for i in itens if i["enviado"]),
        "itens":        itens,
    }
