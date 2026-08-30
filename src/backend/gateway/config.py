from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    """Configuração dos serviços backend para proxy."""

    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    MOBILIDADE_SERVICE_URL: str = "http://mobilidade-service:8000"
    COLABORACAO_SERVICE_URL: str = "http://colaboracao-service:8000"

    class Config:
        env_prefix = "GATEWAY_"
        env_file = ".env"


def get_gateway_settings() -> GatewaySettings:
    return GatewaySettings()
