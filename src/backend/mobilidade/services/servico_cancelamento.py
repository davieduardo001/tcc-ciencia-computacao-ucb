# Alerta de cancelamento de viagem — US #28
#
# "Como passageiro que depende de uma linha específica, quero ser notificado
# quando uma viagem for cancelada, para buscar alternativa de transporte
# com antecedência."
#
# A cada ciclo o serviço varre as linhas acompanhadas (favoritos + linhas
# seguidas, Cenário 1) e, para cada uma:
#   1. lê a tabela teórica (`linha.horarios_previstos`) e acha as partidas
#      cujo horário previsto passou dentro da JANELA_DETECCAO (Cenário 3:
#      "não aparece em operação após 15 minutos do horário de partida");
#   2. confere se a linha TEM veículo no feed ao vivo — se tem, a partida
#      ocorreu e não há nada a registrar;
#   3. se a linha está sem veículo mas o feed dos DEMAIS está vivo (outra
#      linha reporta posição), a ausência é real: registra o alerta e
#      busca a linha alternativa (Cenário 2, sobreposição >= 70%);
#   4. notifica cada destinatário que tem `alerta_cancelamento` ativo
#      (Cenário 3 da US #29), sempre DEPOIS do commit.
#
# ---------------------------------------------------------------------------
# SUPosições PROVISÓRIAS (dependências abertas)
# ---------------------------------------------------------------------------
#
# * Cancelamento pelo operador (Cenário 1, "cancelada pelo operador") —
#   NÃO IMPLEMENTADO: não existe fonte no SEMOB nem tabela interna de
#   cancelamento operacional. O serviço cobre só a detecção por ausência
#   (Cenário 3), que é o "ônibus fantasma" do PRD. O campo
#   `AlertaCancelamento.status` já reserva "confirmado" para quando a
#   fonte existir — a detecção por operador entraria como um provider
#   novo alimentando a mesma tabela.
#
# * Horário da partida — vem de `linha.horarios_previstos` (tabela
#   teórica, cache local), comparado no FUSO DO SEMOB (Brasília), o mesmo
#   fuso em que o horário foi publicado. A janela de detecção tem teto
#   (JANELA_DETECCAO_MAX_MIN) para não registrar como cancelamento uma
#   partida da véspera quando o worker reinicia depois de horas fora.
#
# * Ausência vs. feed fora — o feed de posições do SEMOB não tem
#   histórico: só mostra quem está em operação AGORA. A ausência só vale
#   quando OUTRAS linhas reportam posição no mesmo ciclo (feed vivo);
#   com o feed inteiro vazio, a causa pode ser a fonte, não a linha — e
#   Cenário 4 da #172 já ensina: sem dado confiável, não notifica.
#
# * Preferências lidas do banco compartilhado (ver preferencias_banco.py)
#   sem importar o pacote `colaboracao`, por causa do Dockerfile do
#   mobilidade.

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mobilidade.linhas_alternativas import buscar_alternativas
from mobilidade.models.alerta_cancelamento import AlertaCancelamento
from mobilidade.models.linha import Linha
from mobilidade.posicao_service import FUSO_SEMOB
from mobilidade.providers.contratos_cancelamento import DestinatariosProvider
from mobilidade.providers.contratos_proximidade import (
    PreferenciasProvider,
    VeiculosProvider,
)
from mobilidade.services.servico_notificacoes import Notificador

logger = logging.getLogger(__name__)

# Eventos retornados por `verificar_ciclo` (para log e teste).
EVENTO_REGISTRADO = "cancelamento_registrado"
EVENTO_JA_REGISTRADO = "ja_registrado"
EVENTO_FEED_INDISPONIVEL = "feed_indisponivel"
EVENTO_ERRO = "erro"

# Janela em que a partida prevista ainda é considerada "recém-cancelada".
# Mínimo: 15 min, o prazo da SPEC ("após 15 minutos do horário de
# partida"). Máximo: evita acordar o usuário de madrugada com um
# cancelamento da véspera quando o serviço ficou fora (deploy, queda).
JANELA_DETECCAO_MIN_MIN = 15
JANELA_DETECCAO_MAX_MIN = 45


class ServicoCancelamento:
    """
    Serviço do alerta de cancelamento de viagem (US #28).

    Recebe tudo por injeção — nenhum mock nem implementação concreta é
    instanciado aqui (mesmo padrão do ServicoProximidade e do
    ServicoRastreamento). As interfaces estão em
    providers/contratos_cancelamento.py e contratos_proximidade.py.
    """

    def __init__(
        self,
        veiculos: VeiculosProvider,
        preferencias: PreferenciasProvider,
        notificador: Notificador,
        destinatarios: DestinatariosProvider,
    ) -> None:
        self.veiculos = veiculos
        self.preferencias = preferencias
        self.notificador = notificador
        self.destinatarios = destinatarios

    def verificar_ciclo(self, db: Session) -> list[str]:
        """
        Um ciclo completo: avalia todas as linhas acompanhadas uma única vez.

        Retorna um evento por LINHA avaliada (ver constantes EVENTO_*);
        uma linha sem partida na janela não gera evento. Falha em uma
        linha não interrompe as demais — o worker roda sozinho, ninguém
        está olhando exceção para repetir o ciclo.
        """
        por_linha = self.destinatarios.listar_por_linha(db)
        if not por_linha:
            return []

        # Uma leitura só no feed de posição para todas as linhas do ciclo,
        # igual ao ServicoProximidade: o cache do SEMOB dura 20 s, baixar
        # uma linha por vez desperdiça o feed.
        veiculos_por_linha = self._obter_veiculos(set(por_linha))

        # Sem NENHUM veículo no feed, a causa pode ser a fonte (rede,
        # SEMOB fora) e não a linha — Cenário 4 da #172: não notifica
        # com dado duvidoso.
        if not any(veiculos for veiculos in veiculos_por_linha.values()):
            return [EVENTO_FEED_INDISPONIVEL]

        agora = datetime.now(timezone.utc)
        eventos: list[str] = []
        for numero, usuarios in por_linha.items():
            try:
                linha_eventos = self._verificar_linha(
                    numero, usuarios, veiculos_por_linha.get(numero, []), agora, db
                )
            except IntegrityError:
                # Dois ciclos simultâneos: a outra transação registrou o
                # alerta primeiro. A deduplicação é do banco, não daqui.
                db.rollback()
                linha_eventos = [EVENTO_JA_REGISTRADO]
            except Exception:
                db.rollback()
                logger.exception(
                    "Erro ao verificar cancelamento | linha=%s", numero
                )
                linha_eventos = [EVENTO_ERRO]

            eventos.extend(linha_eventos)

        return eventos

    # ------------------------------------------------------------------
    # Verificação de uma linha — isolada para facilitar testes
    # ------------------------------------------------------------------

    def _verificar_linha(
        self,
        numero: str,
        usuarios: set,
        veiculos: list,
        agora: datetime,
        db: Session,
    ) -> list[str]:
        # Cenário 3 — a partida só é suspeita se a linha está SEM veículo
        # neste momento. Com ônibus na rua, a linha está operando.
        if veiculos:
            return []

        horarios = self._horarios_na_janela(numero, agora, db)
        if not horarios:
            return []

        eventos: list[str] = []
        for horario in horarios:
            evento = self._registrar_cancelamento(numero, horario, usuarios, db)
            if evento is not None:
                eventos.append(evento)
        return eventos

    def _horarios_na_janela(self, numero: str, agora: datetime, db: Session) -> list[str]:
        """
        Partidas previstas de HOJE cujo horário passou há 15–45 min.

        Comparação no fuso do SEMOB, o mesmo em que a tabela teórica foi
        publicada — o relógio do container é UTC e os horários não.
        """
        linha = db.query(Linha).filter(Linha.numero == numero).first()
        if linha is None or not linha.horarios_previstos:
            return []

        agora_local = agora.astimezone(FUSO_SEMOB)
        na_janela: list[str] = []
        for hhmm in linha.horarios_previstos:
            minutos = _minutos_desde(hhmm, agora_local)
            if minutos is None:
                continue
            if JANELA_DETECCAO_MIN_MIN <= minutos <= JANELA_DETECCAO_MAX_MIN:
                na_janela.append(hhmm)
        return na_janela

    def _registrar_cancelamento(
        self,
        numero: str,
        horario: str,
        usuarios: set,
        db: Session,
    ) -> str | None:
        """
        Persiste o alerta da partida e notifica os destinatários.

        Notifica DEPOIS do commit (mesmo padrão do ServicoProximidade):
        registrar que o alerta existe é a garantia de não repetir;
        notificar antes correria o risco de enviar duas vezes se o
        commit falhasse.
        """
        ja_existe = (
            db.query(AlertaCancelamento)
            .filter(
                AlertaCancelamento.numero_linha == numero,
                AlertaCancelamento.horario_partida == horario,
            )
            .first()
        )
        if ja_existe is not None:
            return EVENTO_JA_REGISTRADO

        alternativas = buscar_alternativas(db, numero)
        alerta = AlertaCancelamento(
            numero_linha=numero,
            horario_partida=horario,
            status="suspeito",
            alternativa_numero=alternativas[0].numero if alternativas else None,
            detectado_em=datetime.utcnow(),
        )
        db.add(alerta)
        db.commit()

        alternativa = alternativas[0].numero if alternativas else None
        notificados = 0
        for usuario_id in usuarios:
            pref = self.preferencias.obter(usuario_id, db)
            if not pref.notificacoes_ativas or not pref.alerta_cancelamento:
                continue
            self.notificador.alerta_cancelamento_viagem(
                str(usuario_id), numero, horario, alternativa
            )
            notificados += 1

        logger.info(
            "Cancelamento registrado | linha=%s | horario=%s | alternativa=%s | notificados=%d/%d",
            numero,
            horario,
            alternativa or "-",
            notificados,
            len(usuarios),
        )
        return EVENTO_REGISTRADO

    def _obter_veiculos(self, numeros_linha: set[str]) -> dict[str, list]:
        try:
            return self.veiculos.obter_das_linhas(numeros_linha)
        except Exception:
            # Contrato prevê "nunca lança"; se quebrar na prática, seguimos
            # com "sem veículo" — e o vazio geral vira feed indisponível.
            logger.warning("Falha inesperada ao obter veiculos", exc_info=True)
            return {}


def _minutos_desde(hhmm: str, agora_local: datetime) -> float | None:
    """
    Minutos decorridos desde o horário `hhmm` ("HH:MM") no fuso local.

    `None` quando o formato é inválido. Horário que ainda não chegou hoje
    é interpretado como a partida de ONTEM — a última passagem daquela
    linha, que é o caso real de "o ônibus das 23:50 nunca apareceu".
    """
    try:
        hora, minuto = str(hhmm).split(":")
        previsto = agora_local.replace(
            hour=int(hora), minute=int(minuto), second=0, microsecond=0
        )
    except (ValueError, TypeError):
        return None

    if previsto > agora_local:
        previsto -= timedelta(days=1)

    return (agora_local - previsto).total_seconds() / 60
