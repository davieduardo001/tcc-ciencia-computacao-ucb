import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, Uuid

from models.base import Base


class ConfirmacaoOcorrencia(Base):
    """
    Registro de confirmação de ocorrência por um passageiro (US #26).

    Cada linha representa uma confirmação válida: um usuário diferente do
    autor original confirmou que viu o mesmo problema.

    A constraint UNIQUE(ocorrencia_id, usuario_id) garante, no nível do
    banco, que o mesmo usuário não confirme duas vezes — mesmo sob
    requisições concorrentes, o banco rejeita a segunda inserção com
    IntegrityError antes de qualquer incremento duplicado no contador.

    O contador `ocorrencia.contador_confirmacoes` é atualizado atomicamente
    junto com a inserção (dentro da mesma transação). O status muda para
    "confirmada" quando o contador atinge Ocorrencia.LIMITE_CONFIRMACOES.

    Não há FK para `usuarios.id` declarada no ORM para não acoplar
    colaboracao ao schema auth — mesmo padrão de Ocorrencia.usuario_id.
    A FK real pode ser adicionada numa migration futura se a integridade
    referencial entre serviços for requerida.
    """

    __tablename__ = "confirmacoes_ocorrencia"
    __table_args__ = (
        UniqueConstraint(
            "ocorrencia_id",
            "usuario_id",
            name="uq_confirmacao_ocorrencia_usuario",
        ),
    )

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)

    # FK para ocorrencia.id — mesmo banco PostgreSQL.
    ocorrencia_id = Column(
        Uuid,
        ForeignKey("ocorrencia.id"),
        nullable=False,
        index=True,
    )

    # ID do usuário que confirmou — sem FK ORM (padrão do projeto).
    usuario_id = Column(Uuid, nullable=False, index=True)

    criado_em = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.utcnow(),
    )
