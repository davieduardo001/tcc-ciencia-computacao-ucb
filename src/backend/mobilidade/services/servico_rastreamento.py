import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from mobilidade.models.linha_acompanhada import LinhaAcompanhada
from mobilidade.models.alerta import AlertaAtraso
from mobilidade.providers.gtfs_base import FornecedorGTFS
from mobilidade.services.servico_notificacoes import Notificador
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from mobilidade.providers.contratos_proximidade import PreferenciasProvider


class ServicoRastreamento:
    def __init__(
        self,
        fornecedor_gtfs: FornecedorGTFS,
        notificador: Notificador,
        preferencias: Optional[PreferenciasProvider] = None,
    ):
        """
        `preferencias` (US #207, Cenário 3): com as notificações desligadas
        na #29, o alerta continua sendo registrado (é o que aparece dentro
        do app), mas o notificador não é chamado. Sem provider, notifica
        sempre — o comportamento de antes.
        """
        self.fornecedor = fornecedor_gtfs
        self.notificador = notificador
        self.preferencias = preferencias

    def _pode_notificar(self, usuario_id: uuid.UUID, db: Session) -> bool:
        if self.preferencias is None:
            return True
        return self.preferencias.obter(usuario_id, db).notificacoes_ativas

    def listar_linhas_acompanhadas(self, usuario_id: uuid.UUID, db: Session) -> list[LinhaAcompanhada]:
        return (
            db.query(LinhaAcompanhada)
            .filter(LinhaAcompanhada.usuario_id == usuario_id)
            .all()
        )

    def listar_alertas(self, usuario_id: uuid.UUID, db: Session) -> list[AlertaAtraso]:
        return (
            db.query(AlertaAtraso)
            .filter(AlertaAtraso.usuario_id == usuario_id)
            .order_by(AlertaAtraso.criado_em.desc())
            .all()
        )

    def verificar_e_disparar_alertas(self, usuario_id: uuid.UUID, db: Session) -> list[str]:
        eventos = []
        linhas = self.listar_linhas_acompanhadas(usuario_id, db)

        for linha in linhas:
            atraso = self.fornecedor.obter_atraso(linha.linha_id)
            if atraso is None:
                continue

            eventos.extend(self._processar_linha(usuario_id, linha.linha_id, atraso, db))

        return eventos

    def _processar_linha(self, usuario_id: uuid.UUID, linha_id: str, atraso: float, db: Session) -> list[str]:
        eventos = []
        alerta = (
            db.query(AlertaAtraso)
            .filter(
                AlertaAtraso.usuario_id == usuario_id,
                AlertaAtraso.linha_id == linha_id,
                AlertaAtraso.status == "ativo",
            )
            .first()
        )

        if atraso > 10:
            if alerta is None:
                novo = AlertaAtraso(
                    usuario_id=usuario_id,
                    linha_id=linha_id,
                    atraso_inicio_minutos=atraso,
                    ultimo_atraso_notificado=atraso,
                    ultimo_alerta_enviado_em=datetime.utcnow(),
                )
                try:
                    db.add(novo)
                    db.commit()
                    db.refresh(novo)
                    if self._pode_notificar(usuario_id, db):
                        self.notificador.alerta_disparado(str(usuario_id), linha_id, atraso)
                    eventos.append("criado")
                except IntegrityError:
                    db.rollback()
                    alerta = (
                        db.query(AlertaAtraso)
                        .filter(
                            AlertaAtraso.usuario_id == usuario_id,
                            AlertaAtraso.linha_id == linha_id,
                            AlertaAtraso.status == "ativo",
                        )
                        .with_for_update()
                        .first()
                    )
                    if alerta:
                        eventos.extend(self._atualizar_alerta(alerta, atraso, db))
            else:
                eventos.extend(self._atualizar_alerta(alerta, atraso, db))

        elif atraso < 5:
            if alerta is not None:
                alerta.status = "cancelado"
                alerta.cancelado_em = datetime.utcnow()
                db.commit()
                if self._pode_notificar(usuario_id, db):
                    self.notificador.alerta_cancelado(str(usuario_id), linha_id)
                eventos.append("cancelado")

        return eventos

    def _atualizar_alerta(self, alerta: AlertaAtraso, atraso: float, db: Session) -> list[str]:
        if alerta.ultimo_atraso_notificado is None:
            eventos = []
        else:
            variacao = abs(atraso - alerta.ultimo_atraso_notificado)
            if variacao >= 5:
                # US #207, Cenário 2: o registro acompanha a variação nos
                # dois sentidos (regra da #27), mas só se avisa quando o
                # atraso AUMENTA — "diminuiu um pouco" não é motivo para
                # tirar o celular do bolso; o fim do atraso tem aviso próprio.
                aumentou = atraso > alerta.ultimo_atraso_notificado
                alerta.ultimo_atraso_notificado = atraso
                alerta.ultimo_alerta_enviado_em = datetime.utcnow()
                db.commit()
                if aumentou and self._pode_notificar(alerta.usuario_id, db):
                    self.notificador.alerta_atualizado(str(alerta.usuario_id), alerta.linha_id, atraso)
                return ["atualizado"]
        return []
