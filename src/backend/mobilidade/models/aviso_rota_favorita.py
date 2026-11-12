from sqlalchemy import Boolean, Column, DateTime, Uuid, func
from models.base import Base


class AvisoRotaFavorita(Base):
    """
    Estado dos avisos de uma rota favorita na "corrida" atual — US #207
    (rotas preferidas da #22 levadas ao push).

    Uma corrida é a aproximação de um ônibus da linha até a parada de
    embarque da favorita. Cada corrida tem dois avisos, um de cada tipo:
    antecedência (ETA dentro da antecedência da #29) e proximidade (ônibus
    ao vivo a 5 min ou menos). Quando o ETA volta a subir, a corrida acabou
    e os dois voltam a False.

    Era um dicionário em memória no worker da #22 (colaboracao/deduplicador);
    no banco, o estado sobrevive a deploy e não duplica aviso quando mais de
    uma máquina roda o worker.

    Campos:
        favorita_id           → `rotas_favoritas.id`. Sem FK: a tabela é do
                                serviço de colaboração (mesmo motivo de
                                providers/destinatarios_banco.py); a linha
                                órfã de uma favorita apagada é removida pelo
                                próprio serviço no ciclo seguinte
        antecedencia_enviada  → aviso de antecedência já enviado nesta corrida
        proximidade_enviada   → aviso de ônibus próximo já enviado nesta corrida
        atualizado_em         → última mudança de estado, para diagnóstico
    """

    __tablename__ = "aviso_rota_favorita"

    favorita_id = Column(Uuid, primary_key=True, nullable=False)
    antecedencia_enviada = Column(Boolean, nullable=False, default=False)
    proximidade_enviada = Column(Boolean, nullable=False, default=False)
    atualizado_em = Column(DateTime, nullable=False, default=func.now())
