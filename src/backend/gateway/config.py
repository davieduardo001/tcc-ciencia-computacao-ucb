from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    """Configuração dos serviços backend para proxy."""

    # Usa as URLs públicas https dos serviços (não a rede interna
    # .internal do Fly.io): a rede privada é IPv6-only, e os serviços
    # também precisam aceitar IPv4 pra funcionar com o proxy público
    # do próprio Fly — bind dual-stack causou instabilidade em
    # produção. Os serviços já ficam expostos publicamente mesmo
    # (só têm /health e /hello sem dado sensível fora do que passa
    # pelo Gateway), então isso não aumenta a superfície de risco.
    AUTH_SERVICE_URL: str = "https://movecity-auth.fly.dev"
    MOBILIDADE_SERVICE_URL: str = "https://movecity-mobilidade.fly.dev"
    COLABORACAO_SERVICE_URL: str = "https://movecity-colaboracao.fly.dev"

    class Config:
        env_prefix = "GATEWAY_"
        env_file = ".env"


def get_gateway_settings() -> GatewaySettings:
    return GatewaySettings()
