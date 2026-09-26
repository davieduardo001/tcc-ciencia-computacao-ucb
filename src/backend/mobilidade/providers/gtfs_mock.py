from typing import Optional

from mobilidade.providers.gtfs_base import FornecedorGTFS


class FornecedorGTFSMock(FornecedorGTFS):
    def __init__(self, atrasos: dict[str, float] | None = None):
        self._atrasos = atrasos or {}

    def obter_atraso(self, linha_id: str) -> Optional[float]:
        return self._atrasos.get(linha_id)
