from flask import Blueprint, render_template, request, redirect, session, flash

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    return render_template("index.html", active_page="inicio")


@pages_bp.route("/clientes")
def pagina_clientes():
    return render_template("clientes.html", active_page="clientes")


@pages_bp.route("/historico")
def pagina_historico():
    return render_template("historico.html", active_page="historico")


@pages_bp.route("/nova-os")
def pagina_nova_os():
    return render_template("nova_os.html", active_page="nova_os")


@pages_bp.route("/editar-os/<int:ordem_id>")
def pagina_editar_os(ordem_id):
    return render_template(
        "editar_os.html",
        active_page="historico",
        ordem_id=ordem_id
    )


@pages_bp.route("/dashboard")
def dashboard():

    if not session.get("usuario_id"):
        return redirect("/login")

    return render_template(
        "dashboard.html",
        active_page="faturamento"
    )

@pages_bp.route("/financeiro")
def pagina_financeiro():

    if not session.get("usuario_id"):
        return redirect("/login")

    return render_template(
        "financeiro.html",
        active_page="financeiro"
    )
