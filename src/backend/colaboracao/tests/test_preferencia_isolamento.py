"""
Regressão da #213: em produção cada serviço sobe isolado, então o metadata do
processo de Colaboração não contém a tabela `usuarios` (modelo do Auth). Uma
FK do ORM para `usuarios.id` não resolvia e o flush levantava
NoReferencedTableError (500). Estes testes carregam só os modelos de
Colaboração, sem importar nada do Auth.
"""
import os
import subprocess
import sys

from colaboracao.models.preferencia_notificacao import PreferenciaNotificacao

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCRIPT = """
import sys
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
import colaboracao.models  # noqa: F401  (só modelos de Colaboração)
from colaboracao.models import PreferenciaNotificacao

assert not [m for m in sys.modules if m == "auth" or m.startswith("auth.")], "Auth carregado"
assert "usuarios" not in Base.metadata.tables, "tabela usuarios no metadata"

# Resolve todas as FKs do metadata (levantaria NoReferencedTableError).
for tabela in Base.metadata.sorted_tables:
    for fk in tabela.foreign_keys:
        fk.column

engine = create_engine("sqlite://")
Base.metadata.create_all(engine, tables=[PreferenciaNotificacao.__table__])
Sessao = sessionmaker(bind=engine)

usuario_id = uuid.uuid4()
with Sessao() as db:
    db.add(PreferenciaNotificacao(id=uuid.uuid4(), usuario_id=usuario_id))
    db.commit()

with Sessao() as db:
    lida = db.query(PreferenciaNotificacao).filter(
        PreferenciaNotificacao.usuario_id == usuario_id
    ).first()
    assert lida is not None
    assert lida.antecedencia_minutos == 30
    assert lida.notificacoes_ativas is True
print("ok")
"""


def test_orm_de_preferencia_nao_declara_fk_para_usuarios():
    assert not PreferenciaNotificacao.__table__.foreign_keys


def test_preferencia_grava_e_le_com_somente_modelos_de_colaboracao():
    resultado = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        cwd=BACKEND_DIR,
        env={**os.environ, "PYTHONPATH": BACKEND_DIR},
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "ok"
