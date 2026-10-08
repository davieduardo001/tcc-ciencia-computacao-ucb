# Contratos da US #172 — Receber alerta de proximidade da parada
#
# Define as interfaces (typing.Protocol) que o ServicoProximidade consome,
# no mesmo padrão de colaboracao/providers/contratos.py (US #22). Todas as
# dependências entram por injeção: o serviço não instancia nenhuma
# implementação concreta, e a troca acontece em um único ponto (main.py).
#
# ---------------------------------------------------------------------------
# SUPosições PROVISÓRIAS — ajustar quando as dependências fecharem
# ---------------------------------------------------------------------------
#
# 1. VIAGEM ATIVA (depende da US #171, "Pegar o ônibus" — ABERTA)
#    A #172 só dispara dentro de uma viagem, mas a entidade "viagem" ainda
#    não existe no banco. Enquanto isso:
#      - `ViagemAtiva` é o formato mínimo que o alerta precisa (id da
#        viagem, usuário, linha e parada de destino com coordenadas);
#      - `ViagensAtivasProvisorias` devolve sempre `[]` — sem viagem, o
#        worker de proximidade não dispara nada (Cenário 4 levado ao
#        extremo: sem dado, sem alerta).
#    Quando a #171 fechar o formato real, trocar `ViagensAtivasProvisorias`
#    por `ViagensAtivasReais` em mobilidade/main.py. Se o formato real
#    divergir, adaptar só este arquivo — o ServicoProximidade consome os
#    campos da dataclass, não a fonte.
#
# 2. IDENTIDADE DA PARADA (depende da #173, "mapeamento entre paradas" —
#    PR #177 em aberto)
#    `parada_destino_codigo` é string estável SEM chave estrangeira: a #173
#    criará a tabela `parada` com um `codigo` estável (String(12)) e quem
#    consome deve usar o `codigo`, não o `id` (a tabela é reconstruída a
#    cada ingestão). Quando a #173 mergear, adicionar a FK para
#    `parada.codigo` numa migration aditiva — os dados já estarão no
#    formato certo.
#
# 3. ETA — o ServicoProximidade calcula o tempo com
#    `mobilidade.eta_service.eta_minutos_veiculo` em linha reta (sem
#    trajeto/sentido), porque o trajeto por parada vem da #173. Com a
#    identidade de parada pronta, passar a medir ao longo do traçado.
#
# 4. PREFERÊNCIAS (US #29 — PRONTA, tabela em colaboracao/)
#    lidas via SQL direto em preferencias_notificacao, sem importar o
#    pacote `colaboracao`: o container do mobilidade (Dockerfile) copia
#    só models/, shared/ e mobilidade/. Ver preferencias_banco.py.

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy.orm import Session

from mobilidade.posicao_service import PosicaoVeiculo


# ---------------------------------------------------------------------------
# Estruturas de dados transferidas entre o serviço e as fontes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ViagemAtiva:
    """
    Uma viagem em andamento (passageiro a bordo) com parada de destino.

    PROVISÓRIO — formato mínimo consumido pelo alerta de proximidade
    (ver observação 1 no cabeçalho do arquivo). Quando a US #171 existir,
    é a dataclass que o provider real terá que produzir.

    Campos:
        viagem_id             → identificador único da viagem; ancora o
                                "uma única vez por parada na mesma viagem"
                                (Cenário 2). String porque a entidade ainda
                                não existe — pode virar UUID na #171.
        usuario_id            → passageiro a bordo; cruza com as
                                preferências de notificação (Cenário 3)
        numero_linha          → número da linha em operação (ex: "0.110"),
                                usado para buscar a posição dos veículos
        parada_destino_codigo → código estável da parada de destino
                                (Cenário 1). Provisório: sem FK até a #173
                                entregar a tabela `parada`
        parada_destino_lat    → latitude do destino — alvo do cálculo de
                                ETA; presente mesmo sem a #173, porque é
                                coordenada, não identidade
        parada_destino_lng    → longitude do destino
        parada_destino_nome   → nome legível compõe a mensagem do alerta
    """

    viagem_id: str
    usuario_id: UUID
    numero_linha: str
    parada_destino_codigo: str
    parada_destino_lat: float
    parada_destino_lng: float
    parada_destino_nome: str = ""


@dataclass(frozen=True)
class PreferenciasDeNotificacao:
    """
    Recorte das preferências da US #29 que o alerta de proximidade usa.

    Campos:
        notificacoes_ativas   → interruptor geral (Cenário 3: "desativar
                                todas as notificações")
        alerta_chegada        → interruptor específico do alerta de chegada
                                (Cenário 3: "desativar tipo específico")
        antecedencia_minutos  → a partir de qual ETA (em minutos) o alerta
                                dispara (Cenário 1: "distância/tempo
                                configurado"). Permitidos: 5, 10, 30, 60;
                                30 é o padrão da US #29
    """

    notificacoes_ativas: bool = True
    alerta_chegada: bool = True
    antecedencia_minutos: int = 30


# ---------------------------------------------------------------------------
# Contratos (Protocol)
# ---------------------------------------------------------------------------


@runtime_checkable
class ViagensAtivasProvider(Protocol):
    """
    Contrato para listar as viagens em andamento que devem ser monitoradas.

    Implementação provisória: ViagensAtivasProvisorias (abaixo) — devolve [].
    Implementação real: fornecida pela US #171 assim que a entidade de
    viagem existir.
    """

    def listar_ativas(self) -> list[ViagemAtiva]:
        """
        Retorna todas as viagens ativas, de todos os usuários.

        Retorna lista vazia quando não há viagem — nunca lança exceção.
        """
        ...


@runtime_checkable
class PreferenciasProvider(Protocol):
    """
    Contrato para ler as preferências de notificação de um usuário (US #29).

    Implementação real: PreferenciasDoBanco (preferencias_banco.py) —
    lê a tabela `preferencias_notificacao` do banco compartilhado.
    """

    def obter(self, usuario_id: UUID, db: Session) -> PreferenciasDeNotificacao:
        """
        Retorna as preferências do usuário.

        Sem registro, devolve o padrão da US #29 (tudo ativo, 30 min) —
        mesmo comportamento de `_obter_ou_criar` em colaboracao/routes.py.
        Nunca lança exceção: sem confirmação do usuário, as preferências
        voltam com notificações desligadas (melhor não alertar a quem
        pediu silêncio do que incomodar).
        """
        ...


@runtime_checkable
class VeiculosProvider(Protocol):
    """
    Contrato para obter a posição atual dos veículos de uma ou mais linhas.

    Implementação real: VeiculosAoVivo (veiculos_ao_vivo.py) — envolve o
    PosicaoService (US #16), com o cache do feed do SEMOB.
    Implementação de teste: mapa fixo de veículos por linha.
    """

    def obter_das_linhas(self, numeros_linha: set[str]) -> dict[str, list[PosicaoVeiculo]]:
        """
        Posição dos veículos das linhas informadas, chaveada por número.

        Lista vazia para uma linha significa "nenhum veículo em operação"
        ou "fonte indisponível" — nas duas situações o alerta simplesmente
        não dispara (Cenário 4: sem posição, sem alerta).
        Nunca lança exceção.
        """
        ...


# ---------------------------------------------------------------------------
# Implementação provisória — remover quando a US #171 entregar a real
# ---------------------------------------------------------------------------


class ViagensAtivasProvisorias:
    """
    Provider provisório da US #171 — ainda não há viagens no sistema.

    Devolve sempre `[]`: com nenhuma viagem ativa, o ciclo de proximidade
    roda sem disparar nada. Isso mantém a US #172 integrada de ponta a
    ponta (modelo, worker, preferências) sem depender do formato final da
    #171 — e sem correr o risco de alerta indevido por dado inventado.

    TROCA: em mobilidade/main.py, substituir por `ViagensAtivasReais`
    (ou equivalente) quando a #171 mergear. Nada mais muda.
    """

    def listar_ativas(self) -> list[ViagemAtiva]:
        return []
