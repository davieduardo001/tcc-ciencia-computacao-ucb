from abc import ABC, abstractmethod


class Notificador(ABC):
    @abstractmethod
    def alerta_disparado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        ...

    @abstractmethod
    def alerta_atualizado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        ...

    @abstractmethod
    def alerta_cancelado(self, usuario_id: str, linha_id: str) -> None:
        ...

    @abstractmethod
    def alerta_proximidade(
        self,
        usuario_id: str,
        numero_linha: str,
        parada_destino: str,
        eta_minutos: float,
    ) -> None:
        """US #172 — passageiro a bordo se aproximando da parada de destino."""
        ...


class NotificadorNulo(Notificador):
    def alerta_disparado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        pass

    def alerta_atualizado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        pass

    def alerta_cancelado(self, usuario_id: str, linha_id: str) -> None:
        pass

    def alerta_proximidade(
        self,
        usuario_id: str,
        numero_linha: str,
        parada_destino: str,
        eta_minutos: float,
    ) -> None:
        pass


class NotificadorMock(Notificador):
    def __init__(self):
        self.chamadas = []

    def alerta_disparado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        self.chamadas.append(("disparado", usuario_id, linha_id, atraso))

    def alerta_atualizado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        self.chamadas.append(("atualizado", usuario_id, linha_id, atraso))

    def alerta_cancelado(self, usuario_id: str, linha_id: str) -> None:
        self.chamadas.append(("cancelado", usuario_id, linha_id))

    def alerta_proximidade(
        self,
        usuario_id: str,
        numero_linha: str,
        parada_destino: str,
        eta_minutos: float,
    ) -> None:
        self.chamadas.append(
            ("proximidade", usuario_id, numero_linha, parada_destino, eta_minutos)
        )
