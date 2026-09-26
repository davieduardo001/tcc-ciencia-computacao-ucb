from abc import ABC, abstractmethod
from typing import Optional


class FornecedorGTFS(ABC):
    @abstractmethod
    def obter_atraso(self, linha_id: str) -> Optional[float]:
        """Retorna o atraso em minutos para a linha. None se indisponível."""
        ...
