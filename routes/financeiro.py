from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    redirect
)

from datetime import datetime, timedelta

from models import OrdemServico

financeiro_bp = Blueprint(
    "financeiro",
    __name__
)


@financeiro_bp.route(
    "/api/financeiro",
    methods=["GET"]
)
def financeiro():

    # Verifica login
    if not session.get("usuario_id"):
        return redirect("/login")

    query = OrdemServico.query.filter(
        OrdemServico.status == "finalizada"
    )

    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if data_inicio:
        try:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        except ValueError:
            return jsonify(erro="Data inicial inválida."), 400

        query = query.filter(
            OrdemServico.data >= inicio
        )

    if data_fim:
        try:
            fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            return jsonify(erro="Data final inválida."), 400

        query = query.filter(
            OrdemServico.data < fim
        )

    ordens = query.order_by(
        OrdemServico.data.desc()
    ).all()

    resultado = []

    for o in ordens:

        resultado.append({

            "id": o.id,

            "data": o.data.strftime(
                "%d/%m/%Y"
            ),

            "cliente": (
                o.cliente.nome
                if o.cliente
                else "-"
            ),

            "descricao": (
                o.descricao
                or "-"
            ),

            "valor": float(
                o.valor_total or 0
            ),

            "pagamento": (
                o.forma_pagamento
                or "-"
            ),

            "itens": [
                item.descricao
                for item in o.itens
            ]

        })

    return jsonify(resultado)
