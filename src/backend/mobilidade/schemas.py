from pydantic import BaseModel


class ParadaResponse(BaseModel):
    nome: str
    lat: float
    lng: float


class LinhaResponse(BaseModel):
    numero: str
    nome: str
    sentido: str
    paradas: list[ParadaResponse]
    trajeto: list[tuple[float, float]]
    horarios_previstos: list[str]


class LinhaNaoEncontrada(BaseModel):
    detail: str = "Linha não encontrada."
