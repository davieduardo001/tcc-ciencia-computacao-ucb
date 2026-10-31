# Destinatários do alerta de cancelamento (US #28)
#
# As DUAS tabelas são criadas por SQL direto (mesmo desenho do
# destinatarios_banco.py): `rotas_favoritas` pertence ao pacote
# `colaboracao`, que o container do mobilidade não copia — o teste segue
# a mesma restrição do código de produção e não importa o modelo.

import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from mobilidade.providers.destinatarios_banco import DestinatariosDoBanco

_DDL = """
CREATE TABLE linhas_acompanhadas (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL,
    linha_id TEXT NOT NULL,
    ativo INTEGER DEFAULT 1
);
CREATE TABLE rotas_favoritas (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL,
    numero_linha TEXT NOT NULL
);
"""


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    with engine.begin() as conexao:
        for comando in _DDL.split(";"):
            if comando.strip():
                conexao.execute(text(comando))
    sessao = sessionmaker(bind=engine)()
    yield sessao
    sessao.close()


def _acompanhar(db, usuario, linha, ativo=1):
    db.execute(
        text(
            "INSERT INTO linhas_acompanhadas (id, usuario_id, linha_id, ativo) "
            "VALUES (:id, :usuario, :linha, :ativo)"
        ),
        {"id": str(uuid.uuid4()), "usuario": str(usuario), "linha": linha, "ativo": ativo},
    )
    db.commit()


def _favoritar(db, usuario, linha):
    db.execute(
        text(
            "INSERT INTO rotas_favoritas (id, usuario_id, numero_linha) "
            "VALUES (:id, :usuario, :linha)"
        ),
        {"id": str(uuid.uuid4()), "usuario": str(usuario), "linha": linha},
    )
    db.commit()


def test_agrupa_quem_acompanha_e_quem_favoritou_por_linha(db):
    u1, u2 = uuid.uuid4(), uuid.uuid4()
    _acompanhar(db, u1, "0.110")
    _favoritar(db, u2, "0.110")

    por_linha = DestinatariosDoBanco().listar_por_linha(db)

    # No SQLite o driver devolve texto; em produção (psycopg2) vem UUID.
    assert por_linha == {"0.110": {str(u1), str(u2)}}


def test_linha_desacompanhada_nao_recebe_alerta(db):
    u1 = uuid.uuid4()
    _acompanhar(db, u1, "0.110", ativo=0)

    assert DestinatariosDoBanco().listar_por_linha(db) == {}


def test_usuario_nas_duas_fontes_conta_uma_vez_só(db):
    u1 = uuid.uuid4()
    _acompanhar(db, u1, "0.110")
    _favoritar(db, u1, "0.110")

    por_linha = DestinatariosDoBanco().listar_por_linha(db)

    assert por_linha == {"0.110": {str(u1)}}


def test_sem_nada_registrado_devolve_vazio(db):
    assert DestinatariosDoBanco().listar_por_linha(db) == {}


def test_falha_na_leitura_devolve_vazio_sem_levantar(db):
    db.execute(text("DROP TABLE linhas_acompanhadas"))
    db.commit()

    # Tabela inexistente (banco separado pela #42, migração atrasada):
    # o worker tenta de novo no ciclo seguinte, sem derrubar o job.
    assert DestinatariosDoBanco().listar_por_linha(db) == {}
