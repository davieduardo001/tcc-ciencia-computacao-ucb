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


class NotificadorNulo(Notificador):
    def alerta_disparado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        pass

    def alerta_atualizado(self, usuario_id: str, linha_id: str, atraso: float) -> None:
        pass

    def alerta_cancelado(self, usuario_id: str, linha_id: str) -> None:
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
