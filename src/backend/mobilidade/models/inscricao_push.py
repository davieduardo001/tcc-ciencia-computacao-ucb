import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, UniqueConstraint, Uuid

from models.base import Base


class InscricaoPush(Base):
    """
    Inscrição de um dispositivo para receber Web Push — alerta de
    proximidade com a tela bloqueada (US #172, continuação).

    Uma linha é "este navegador, neste aparelho, aceitou receber avisos do
    Movecity". O `endpoint` é a URL que o serviço de push do navegador (FCM,
    Mozilla, Apple, Windows) criou para ELE; `p256dh` e `auth` são as chaves
    com que o servidor cifra a mensagem para ele. Quem tem os três consegue
    mandar um push àquele aparelho (e ainda precisa da chave VAPID), então
    tratar como dado de identificação do dispositivo:

      - nunca vai para log (só o `id` desta linha);
      - sai daqui quando a pessoa desativa, quando sai da conta e quando o
        serviço de push responde 404/410 (inscrição expirada);
      - não carrega localização, nome nem user agent.

    Campos:
        usuario_id       → dono; vem do X-User-Id do Gateway, nunca do corpo
        endpoint         → único: um aparelho tem uma inscrição, e se outra
                           conta entrar no mesmo aparelho a linha muda de
                           dono em vez de duplicar
        p256dh, auth     → chaves públicas da inscrição, em base64url
        criado_em        → UTC, sem fuso (como as demais tabelas)
        ultima_falha_em  → último envio que falhou por motivo que NÃO é
                           inscrição expirada (rede, 5xx); diagnóstico
    """

    __tablename__ = "inscricao_push"
    __table_args__ = (UniqueConstraint("endpoint", name="uq_inscricao_push_endpoint"),)

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    usuario_id = Column(Uuid, nullable=False, index=True)
    endpoint = Column(String(1024), nullable=False)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(64), nullable=False)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    ultima_falha_em = Column(DateTime, nullable=True)
