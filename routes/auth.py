from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash
)

from models import db, Usuario

auth_bp = Blueprint(
    "auth",
    __name__
)

# LOGIN
@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        usuario = request.form.get(
            "usuario"
        )

        senha = request.form.get(
            "senha"
        )

        user = Usuario.query.filter_by(
            usuario=usuario
        ).first()

        if not user or not senha or not user.verificar_senha(senha):

            flash(
                "Login e/ou senha inválido(s). Tente novamente.",
                "error"
            )

            return redirect("/login")

        session.clear()
        session["usuario_id"] = user.id
        session["usuario_nome"] = user.nome

        return redirect("/dashboard")

    return render_template(
        "login.html"
    )


# CADASTRO
@auth_bp.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def cadastro():
    # TRAVA DE SEGURANÇA: Se não estiver logado, chuta para a tela de login
    if not session.get("usuario_id"):
        return redirect("/login")

    if request.method == "POST":
        nome = request.form.get("nome")
        usuario = request.form.get("usuario")
        senha = request.form.get("senha", "")
        if not nome or not nome.strip() or not usuario or not usuario.strip() or len(senha) < 8:
            flash("Informe nome, usuário e senha de pelo menos 8 caracteres.", "error")
            return redirect("/cadastro")

        existe = Usuario.query.filter_by(usuario=usuario).first()
        if existe:
            flash("Usuário já existe", "error")
            return redirect("/cadastro")

        novo = Usuario(
            nome=nome,
            usuario=usuario
        )
        novo.set_senha(senha)

        db.session.add(novo)
        db.session.commit()

        flash("Usuário criado com sucesso", "success")

        # Redireciona para a dashboard (ou histórico), já que você já está logado mexendo no sistema
        return redirect("/dashboard")

    return render_template("cadastro.html")


# LOGOUT
@auth_bp.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return redirect("/")
