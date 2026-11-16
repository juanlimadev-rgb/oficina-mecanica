from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, OrdemServico

faturamento_bp = Blueprint(
    "faturamento",
    __name__
)


@faturamento_bp.route("/api/faturamento", methods=["GET"])
def faturamento():
    # Pega o dia de hoje sem as horas locais interferirem
    hoje = datetime.utcnow().date()

    # Define início e fim do dia atual de forma estrita para evitar quebras de fuso
    inicio_hoje = datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
    fim_hoje = inicio_hoje + timedelta(days=1)

    inicio_mes = datetime(hoje.year, hoje.month, 1, 0, 0, 0)

    proximo_mes = datetime(hoje.year + (hoje.month == 12), 1 if hoje.month == 12 else hoje.month + 1, 1)

    # Base da query apenas com ordens finalizadas
    base_query = OrdemServico.query.filter(
        OrdemServico.status == "finalizada"
    )

    # Faturamento de Hoje
    faturamento_hoje = (
        base_query
        .filter(
            OrdemServico.data >= inicio_hoje,
            OrdemServico.data < fim_hoje
        )
        .with_entities(
            func.coalesce(
                func.sum(OrdemServico.valor_total),
                0
            )
        )
        .scalar()
    )

    # Quantidade de OS de Hoje
    qtd_hoje = (
        base_query
        .filter(
            OrdemServico.data >= inicio_hoje,
            OrdemServico.data < fim_hoje
        )
        .count()
    )

    # Faturamento do Mês
    faturamento_mes = (
        base_query
        .filter(
            OrdemServico.data >= inicio_mes,
            OrdemServico.data < proximo_mes
        )
        .with_entities(
            func.coalesce(
                func.sum(OrdemServico.valor_total),
                0
            )
        )
        .scalar()
    )

    # Quantidade de OS do Mês
    qtd_mes = (
        base_query
        .filter(
            OrdemServico.data >= inicio_mes,
            OrdemServico.data < proximo_mes
        )
        .count()
    )

    # Faturamento Total acumulado
    faturamento_total = (
        base_query
        .with_entities(
            func.coalesce(
                func.sum(OrdemServico.valor_total),
                0
            )
        )
        .scalar()
    )

    # Quantidade Total de OS
    qtd_total = base_query.count()

    # Monta o dicionário estrutural de resposta inicial
    resultado = {
        "faturamento_hoje": round(faturamento_hoje, 2),
        "faturamento_mes": round(faturamento_mes, 2),
        "faturamento_total": round(faturamento_total, 2),
        "quantidade_os_hoje": qtd_hoje,
        "quantidade_os_mes": qtd_mes,
        "quantidade_os_total": qtd_total,
    }

    # Verifica filtros customizados por período de datas (caso o dashboard envie)
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if data_inicio and data_fim:
        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)

            custom_query = base_query.filter(
                OrdemServico.data >= dt_inicio,
                OrdemServico.data < dt_fim
            )

            resultado["faturamento_periodo"] = round(
                custom_query.with_entities(
                    func.coalesce(
                        func.sum(OrdemServico.valor_total),
                        0
                    )
                ).scalar(),
                2
            )

            resultado["quantidade_os_periodo"] = custom_query.count()
        except ValueError:
            return jsonify(erro="Período inválido."), 400

    return jsonify(resultado)


@faturamento_bp.route("/api/faturamento/por-mes", methods=["GET"])
def faturamento_por_mes():
    # Agrupa faturamento total e quantidade de OS divididos por Ano-Mês para montar os gráficos
    resultados = (
        db.session.query(
            func.strftime("%Y-%m", OrdemServico.data).label("mes"),
            func.coalesce(
                func.sum(OrdemServico.valor_total),
                0
            ).label("total"),
            func.count(OrdemServico.id).label("quantidade"),
        )
        .filter(
            OrdemServico.status == "finalizada"
        )
        .group_by("mes")
        .order_by("mes")
        .all()
    )

    return jsonify([
        {
            "mes": r.mes,
            "total": round(r.total, 2),
            "quantidade": r.quantidade
        }
        for r in resultados
    ])
