from flask import Blueprint, request, jsonify, send_file

from datetime import datetime, timedelta
import os

from models import (
    db,
    Cliente,
    OrdemServico,
    ItemServico
)

from pdf_generator import gerar_pdf_ordem
from routes.validation import validate_order

ordens_bp = Blueprint("ordens", __name__)


@ordens_bp.route("/api/ordens", methods=["GET"])
def listar_ordens():
    """
    Filtros disponíveis (query params):
      - cliente_id: filtra por cliente
      - data_inicio, data_fim: formato YYYY-MM-DD, filtra pelo intervalo de datas
      - status: finalizada / pendente / cancelada
    """
    query = OrdemServico.query

    cliente_id = request.args.get("cliente_id")
    if cliente_id:
        try:
            cliente_id = int(cliente_id)
        except ValueError:
            return jsonify(erro="cliente_id inválido."), 400
        query = query.filter(OrdemServico.cliente_id == cliente_id)

    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(
                data_inicio,
                "%Y-%m-%d"
            )

            query = query.filter(
                OrdemServico.data >= dt_inicio
            )

        except ValueError:
            return jsonify({
                "erro": "Data inicial inválida."
            }), 400


    if data_fim:
        try:
            dt_fim = datetime.strptime(
                data_fim,
                "%Y-%m-%d"
            ) + timedelta(days=1)

            query = query.filter(
                OrdemServico.data < dt_fim
            )

        except ValueError:
            return jsonify({
                "erro": "Data final inválida."
            }), 400

    status = request.args.get("status")
    if status:
        query = query.filter(OrdemServico.status == status)

    ordens = query.order_by(OrdemServico.data.desc()).all()
    return jsonify([o.to_dict() for o in ordens])


@ordens_bp.route("/api/ordens/<int:ordem_id>", methods=["GET"])
def obter_ordem(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    return jsonify(ordem.to_dict())


@ordens_bp.route("/api/ordens", methods=["POST"])
def criar_ordem():
    """
    Espera um JSON no formato:
    {
        "cliente_id": 1,
        "descricao": "Troca de óleo e revisão geral",
        "status": "finalizada",
        "itens": [
            {"descricao": "Óleo 10W30", "quantidade": 1, "valor_unitario": 45.0},
            {"descricao": "Mão de obra", "quantidade": 1, "valor_unitario": 30.0}
        ]
    }
    """
    data = request.get_json()
    if not isinstance(data, dict) or not data.get("cliente_id"):
        return jsonify({"erro": "cliente_id é obrigatório"}), 400

    try:
        validate_order({**data, "itens": data.get("itens", [])})
        cliente_id = int(data["cliente_id"])
    except (ValueError, TypeError) as error:
        return jsonify(erro=str(error)), 400
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente:
        return jsonify({"erro": "Cliente não encontrado"}), 404

    itens_data = data.get("itens", [])
    valor_total = sum(
        float(i.get("quantidade", 1)) * float(i.get("valor_unitario", 0))
        for i in itens_data
    )

    ordem = OrdemServico(
        cliente_id=cliente.id,
        descricao=data.get("descricao", ""),
        status=data.get("status", "finalizada"),
        valor_total=round(valor_total, 2),
        forma_pagamento=data.get("forma_pagamento"),
    )

    # se foi passada uma data específica, usa ela; senão usa agora
    if data.get("data"):
        try:
            ordem.data = datetime.strptime(data["data"], "%Y-%m-%d")
        except ValueError:
            pass

    db.session.add(ordem)
    db.session.flush()  # garante ordem.id antes de criar os itens

    for item in itens_data:
        novo_item = ItemServico(
            ordem_id=ordem.id,
            descricao=item.get("descricao", ""),
            quantidade=float(item.get("quantidade", 1)),
            valor_unitario=float(item.get("valor_unitario", 0)),
        )
        db.session.add(novo_item)

    db.session.commit()
    return jsonify(ordem.to_dict()), 201


@ordens_bp.route("/api/ordens/<int:ordem_id>", methods=["PUT"])
def atualizar_ordem(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    data = request.get_json() or {}

    try:
        validate_order(data)
    except ValueError as error:
        return jsonify(erro=str(error)), 400

    ordem.descricao = data.get("descricao", ordem.descricao)
    ordem.status = data.get("status", ordem.status)
    ordem.forma_pagamento = data.get("forma_pagamento", ordem.forma_pagamento)

    if "itens" in data:
        # remove itens antigos e recria
        for item in list(ordem.itens):
            db.session.delete(item)
        db.session.flush()

        valor_total = 0
        for item in data["itens"]:
            qtd = float(item.get("quantidade", 1))
            valor_unit = float(item.get("valor_unitario", 0))
            valor_total += qtd * valor_unit
            novo_item = ItemServico(
                ordem_id=ordem.id,
                descricao=item.get("descricao", ""),
                quantidade=qtd,
                valor_unitario=valor_unit,
            )
            db.session.add(novo_item)
        ordem.valor_total = round(valor_total, 2)

    db.session.commit()
    return jsonify(ordem.to_dict())


@ordens_bp.route("/api/ordens/<int:ordem_id>", methods=["DELETE"])
def remover_ordem(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    db.session.delete(ordem)
    db.session.commit()
    return jsonify({"sucesso": True})

@ordens_bp.route("/api/ordens/<int:ordem_id>/pdf", methods=["GET"])
def gerar_pdf(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    cliente = ordem.cliente
    filepath = gerar_pdf_ordem(ordem, cliente)
    return send_file(filepath, as_attachment=False, download_name=os.path.basename(filepath))
