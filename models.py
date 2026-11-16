from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(20), unique=True)
    endereco = db.Column(db.String(200))
    moto = db.Column(db.String(100))      # modelo da moto
    placa = db.Column(db.String(10), unique=True)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    ordens = db.relationship("OrdemServico", backref="cliente", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "telefone": self.telefone,
            "endereco": self.endereco,
            "moto": self.moto,
            "placa": self.placa,
            "observacoes": self.observacoes,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }


class OrdemServico(db.Model):
    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    descricao = db.Column(db.Text)         # descrição geral do serviço (ex: "Troca de óleo")
    status = db.Column(db.String(20), default="finalizada")  # finalizada / pendente / cancelada
    valor_total = db.Column(db.Float, default=0.0)
    forma_pagamento = db.Column(db.String(50))

    itens = db.relationship("ItemServico", backref="ordem", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, incluir_itens=True):
        d = {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cliente_nome": self.cliente.nome if self.cliente else None,
            "data": self.data.isoformat() if self.data else None,
            "descricao": self.descricao,
            "status": self.status,
            "valor_total": self.valor_total,
            "forma_pagamento": self.forma_pagamento,
        }
        if incluir_itens:
            d["itens"] = [i.to_dict() for i in self.itens]
        return d


class ItemServico(db.Model):
    __tablename__ = "itens_servico"

    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey("ordens_servico.id"), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)  # ex: "Óleo 10W30", "Mão de obra"
    quantidade = db.Column(db.Float, default=1)
    valor_unitario = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "descricao": self.descricao,
            "quantidade": self.quantidade,
            "valor_unitario": self.valor_unitario,
            "subtotal": round(self.quantidade * self.valor_unitario, 2),
        }

from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    usuario = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def set_senha(self, senha):
        self.senha = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(
            self.senha,
            senha
        )
