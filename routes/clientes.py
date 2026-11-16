from flask import Blueprint, request, jsonify

from models import db, Cliente

import re

clientes_bp = Blueprint("clientes", __name__)


def normalizar_placa(placa):
    if not placa:
        return None

    placa = str(placa).upper()
    placa = re.sub(r"[^A-Z0-9]", "", placa)

    return placa or None


def normalizar_telefone(telefone):
    if not telefone:
        return None

    return re.sub(r"\D", "", str(telefone)) or None

@clientes_bp.route("/api/clientes", methods=["GET"])
def listar_clientes():

    busca = request.args.get("busca", "").strip()

    query = Cliente.query

    if busca:
        query = query.filter(
            (Cliente.nome.ilike(f"%{busca}%")) |
            (Cliente.placa.ilike(f"%{busca}%")) |
            (Cliente.telefone.ilike(f"%{busca}%"))
        )

    clientes = query.order_by(Cliente.nome).all()

    return jsonify([c.to_dict() for c in clientes])


@clientes_bp.route("/api/clientes/<int:cliente_id>", methods=["GET"])
def obter_cliente(cliente_id):

    cliente = Cliente.query.get_or_404(cliente_id)

    return jsonify(cliente.to_dict())


@clientes_bp.route("/api/clientes", methods=["POST"])
def criar_cliente():

    data = request.get_json()

    if not isinstance(data, dict) or not isinstance(data.get("nome"), str) or not data["nome"].strip():
        return jsonify({
            "erro": "Nome é obrigatório"
        }), 400

    placa = normalizar_placa(
    data.get("placa", "")
    )
    telefone = normalizar_telefone(
    data.get("telefone", "")
    )

    # Verifica placa duplicada
    if placa:
        cliente_placa = Cliente.query.filter_by(
            placa=placa
        ).first()

        if cliente_placa:
            return jsonify({
                "erro": f"A placa {placa} já está cadastrada."
            }), 400

    # Verifica telefone duplicado
    if telefone:
        cliente_telefone = Cliente.query.filter_by(
            telefone=telefone
        ).first()

        if cliente_telefone:
            return jsonify({
                "erro": f"O telefone {telefone} já está cadastrado."
            }), 400

    cliente = Cliente(
        nome=data["nome"],
        telefone=telefone,
        endereco=data.get("endereco"),
        moto=data.get("moto"),
        placa=placa,
        observacoes=data.get("observacoes")
    )

    db.session.add(cliente)
    db.session.commit()

    return jsonify(cliente.to_dict()), 201


@clientes_bp.route("/api/clientes/<int:cliente_id>", methods=["PUT"])
def atualizar_cliente(cliente_id):

    cliente = Cliente.query.get_or_404(cliente_id)

    data = request.get_json() or {}

    if not isinstance(data, dict) or ("nome" in data and (not isinstance(data["nome"], str) or not data["nome"].strip())):
        return jsonify(erro="Nome é obrigatório."), 400

    nova_placa = normalizar_placa(
    data.get(
        "placa",
        cliente.placa
    )
    )

    novo_telefone = normalizar_telefone(
    data.get(
        "telefone",
        cliente.telefone
    )
    )

    # Verifica placa duplicada em outro cliente
    if nova_placa:
        existe = Cliente.query.filter(
            Cliente.placa == nova_placa,
            Cliente.id != cliente.id
        ).first()

        if existe:
            return jsonify({
                "erro": f"A placa {nova_placa} já pertence a outro cliente."
            }), 400

    # Verifica telefone duplicado em outro cliente
    if novo_telefone:
        existe = Cliente.query.filter(
            Cliente.telefone == novo_telefone,
            Cliente.id != cliente.id
        ).first()

        if existe:
            return jsonify({
                "erro": f"O telefone {novo_telefone} já pertence a outro cliente."
            }), 400

    cliente.nome = data.get("nome", cliente.nome)
    cliente.telefone = novo_telefone
    cliente.endereco = data.get("endereco", cliente.endereco)
    cliente.moto = data.get("moto", cliente.moto)
    cliente.placa = nova_placa
    cliente.observacoes = data.get("observacoes", cliente.observacoes)

    db.session.commit()

    return jsonify(cliente.to_dict())


@clientes_bp.route("/api/clientes/<int:cliente_id>", methods=["DELETE"])
def remover_cliente(cliente_id):

    cliente = Cliente.query.get_or_404(cliente_id)

    db.session.delete(cliente)
    db.session.commit()

    return jsonify({
        "sucesso": True
    })
