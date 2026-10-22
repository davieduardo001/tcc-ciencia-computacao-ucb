# Alerta de proximidade da parada de destino — US #172
#
# "Como passageiro em viagem, quero ser avisado quando o ônibus estiver
# se aproximando da minha parada, para me preparar para descer sem precisar
# ficar olhando o mapa."
#
# A cada ciclo o serviço varre as viagens ativas e, para cada uma:
#   1. lê as preferências do usuário (Cenário 3 — US #29);
#   2. acha, entre os veículos da linha, o ônibus DA VIAGEM (pelo prefixo
#      gravado no embarque) — Cenário 4: sem GPS dele, não dispara nada;
#   3. pede o ETA até a parada de destino, medido ao longo do trajeto, e
#      compara com a antecedência configurada (Cenário 1 — "distância/tempo
#      configurado"). Veículo parado, de sentido oposto, que já passou do
#      destino ou com posição velha não tem ETA, e portanto não alerta;
#   4. se nunca disparou para esta parada nesta viagem, persiste o alerta
#      e notifica (Cenário 2 — uma única vez; o índice único
#      (viagem_id, parada_destino_codigo) fecha a porta para dois ciclos
#      simultâneos).
#
# ---------------------------------------------------------------------------
# SUPosições PROVISÓRIAS (dependências abertas da Sprint 3)
# ---------------------------------------------------------------------------
#
# * Viagem ativa — vem da US #171 ("Pegar o ônibus"), via ViagensAtivasDoBanco
#   (já ligado em main.py). `ViagensAtivasProvisorias` (devolve []) ficou
#   só como dublê de teste.
#
# * Identidade da parada — `parada_destino_codigo` continua sem chave
#   estrangeira para `parada.codigo` (a tabela é reconstruída a cada
#   ingestão). O ETA, porém, já é medido ao longo do traçado até essa
#   parada (EtaDoDestinoProvider, providers/eta_destino_trajeto.py).
#
# * Entrega da notificação — o worker sobe com NotificadorNulo (no-op),
#   como o alerta de atraso (#27). Dentro do app, o alerta persistido
#   chega à tela pela consulta da viagem ativa (alerta_proximidade_entrega.py);
#   fora do app (push com a tela bloqueada) é integração futura, que
#   precisa de credencial e de decisão do time.
#
# * Preferências lidas do banco compartilhado (ver preferencias_banco.py)
#   sem importar o pacote `colaboracao`, por causa do Dockerfile do
#   mobilidade.

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mobilidade.models.alerta_proximidade import AlertaProximidade
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.providers.contratos_proximidade import (
    EtaDoDestinoProvider,
    PreferenciasProvider,
    VeiculosProvider,
    ViagemAtiva,
    ViagensAtivasProvider,
)
from mobilidade.services.servico_notificacoes import Notificador

logger = logging.getLogger(__name__)

# Eventos retornados por `verificar_proximidades` (para log e teste).
EVENTO_DISPARADO = "disparado"
EVENTO_JA_DISPARADO = "ja_disparado"
EVENTO_PREFERENCIAS = "preferencias_desativadas"
EVENTO_SEM_POSICAO = "sem_posicao_veiculo"
EVENTO_ERRO = "erro"


class ServicoProximidade:
    """
    Serviço do alerta de proximidade da parada (US #172).

    Recebe tudo por injeção — nenhum mock nem implementação concreta é
    instanciado aqui (mesmo padrão do ServicoRastreamento e do
    MonitoramentoWorker da US #22). As interfaces e as suposições
    provisórias estão em providers/contratos_proximidade.py.
    """

    def __init__(
        self,
        viagens: ViagensAtivasProvider,
        veiculos: VeiculosProvider,
        preferencias: PreferenciasProvider,
        notificador: Notificador,
        eta: EtaDoDestinoProvider,
    ) -> None:
        self.viagens = viagens
        self.veiculos = veiculos
        self.preferencias = preferencias
        self.notificador = notificador
        self.eta = eta

    def verificar_proximidades(self, db: Session) -> list[str]:
        """
        Um ciclo completo: avalia todas as viagens ativas uma única vez.

        Retorna um evento por viagem avaliada (ver constantes EVENTO_*);
        viagem fora do limiar não gera evento. Falha em uma viagem não
        interrompe as demais — o worker roda sozinho, ninguém está
        olhando exceção para repetir o ciclo.
        """
        viagens = self.viagens.listar_ativas()
        if not viagens:
            return []

        # Uma leitura só no feed de posição para todas as linhas do ciclo.
        veiculos_por_linha = self._obter_veiculos({v.numero_linha for v in viagens})
        agora = datetime.now(timezone.utc)

        eventos: list[str] = []
        for viagem in viagens:
            try:
                evento = self._verificar_viagem(
                    viagem, veiculos_por_linha.get(viagem.numero_linha, []), agora, db
                )
            except IntegrityError:
                # Dois ciclos simultâneos: a outra transação registrou o
                # alerta primeiro. A deduplicação é do banco, não daqui.
                db.rollback()
                evento = EVENTO_JA_DISPARADO
            except Exception:
                db.rollback()
                logger.exception(
                    "Erro ao verificar proximidade | viagem=%s | linha=%s",
                    viagem.viagem_id,
                    viagem.numero_linha,
                )
                evento = EVENTO_ERRO

            if evento:
                eventos.append(evento)

        return eventos

    # ------------------------------------------------------------------
    # Verificação de uma viagem — isolada para facilitar testes
    # ------------------------------------------------------------------

    def _verificar_viagem(
        self,
        viagem: ViagemAtiva,
        veiculos: list,
        agora: datetime,
        db: Session,
    ) -> str | None:
        # Cenário 3 — respeitar as preferências do usuário (US #29).
        pref = self.preferencias.obter(viagem.usuario_id, db)
        if not pref.notificacoes_ativas or not pref.alerta_chegada:
            return EVENTO_PREFERENCIAS

        # Cenário 4 — sem a posição do ônibus da viagem não há alerta
        # confiável. Outro ônibus da mesma linha não serve: ele pode estar
        # a minutos da parada enquanto o do passageiro ainda vai longe.
        veiculo = self._veiculo_da_viagem(viagem, veiculos)
        if veiculo is None:
            return EVENTO_SEM_POSICAO

        eta = self.eta.eta_minutos(viagem, veiculo, agora, db)
        if eta is None:
            return EVENTO_SEM_POSICAO

        # Cenário 1 — ETA dentro da antecedência configurada.
        if eta > pref.antecedencia_minutos:
            return None

        # Cenário 2 — uma única vez por parada nesta viagem.
        ja_existe = (
            db.query(AlertaProximidade)
            .filter(
                AlertaProximidade.viagem_id == viagem.viagem_id,
                AlertaProximidade.parada_destino_codigo == viagem.parada_destino_codigo,
            )
            .first()
        )
        if ja_existe is not None:
            return EVENTO_JA_DISPARADO

        alerta = AlertaProximidade(
            usuario_id=viagem.usuario_id,
            viagem_id=viagem.viagem_id,
            linha_id=viagem.numero_linha,
            parada_destino_codigo=viagem.parada_destino_codigo,
            parada_destino_nome=viagem.parada_destino_nome or None,
            status="disparado",
            eta_minutos=eta,
            disparado_em=datetime.utcnow(),
        )
        db.add(alerta)
        db.commit()

        # Notifica só depois do commit: registrar que o alerta existe é a
        # garantia de não repetir; notificar antes correria o risco de
        # enviar duas vezes se o commit falhasse.
        self.notificador.alerta_proximidade(
            str(viagem.usuario_id),
            viagem.numero_linha,
            viagem.parada_destino_nome or viagem.parada_destino_codigo,
            eta,
        )
        return EVENTO_DISPARADO

    @staticmethod
    def _veiculo_da_viagem(viagem: ViagemAtiva, veiculos: list[PosicaoVeiculo]) -> PosicaoVeiculo | None:
        """
        O ônibus em que o passageiro está, pelo prefixo gravado no embarque.

        `None` quando a viagem não tem prefixo ou o veículo não está no
        feed agora — o que vira "sem posição" em vez de um palpite.
        """
        if not viagem.veiculo_prefixo:
            return None
        return next((v for v in veiculos if v.prefixo == viagem.veiculo_prefixo), None)

    def _obter_veiculos(self, numeros_linha: set[str]) -> dict[str, list]:
        try:
            return self.veiculos.obter_das_linhas(numeros_linha)
        except Exception:
            # Contrato prevê "nunca lança"; se quebrar na prática, seguimos
            # com "sem veículo" — Cenário 4 manda não arriscar alerta errado.
            logger.warning("Falha inesperada ao obter veiculos", exc_info=True)
            return {}
