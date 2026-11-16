"""Flask + blueprints; dados locais separados do código publicado."""
import hmac
import os
import secrets
from pathlib import Path
import click
from flask import Flask, jsonify, redirect, request, session
from sqlalchemy.engine import URL
from config import USE_MYSQL, MYSQL_CONFIG
from models import db, Usuario
from routes.pages import pages_bp
from routes.clientes import clientes_bp
from routes.ordens import ordens_bp
from routes.faturamento import faturamento_bp
from routes.financeiro import financeiro_bp
from routes.auth import auth_bp


def create_app(test_config=None):
    app = Flask(__name__)
    mysql = dict(MYSQL_CONFIG)
    mysql['username'] = mysql.pop('user')
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or (
            URL.create('mysql+pymysql', **mysql) if USE_MYSQL else 'sqlite:///oficina.db'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        MAX_CONTENT_LENGTH=1024 * 1024,
        PDF_DIR=str(Path(app.instance_path) / 'pdfs'),
        SECRET_KEY=os.environ.get('SECRET_KEY'),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config['SECRET_KEY']:
        secret_file = Path(app.instance_path) / 'session-secret'
        try:
            with secret_file.open('x', encoding='utf-8') as stream:
                stream.write(secrets.token_hex(48))
        except FileExistsError:
            pass
        app.config['SECRET_KEY'] = secret_file.read_text(encoding='utf-8').strip()
    db.init_app(app)
    for blueprint in (pages_bp, clientes_bp, ordens_bp, faturamento_bp, financeiro_bp, auth_bp):
        app.register_blueprint(blueprint)
    with app.app_context():
        db.create_all()

    def csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']
    app.jinja_env.globals['csrf_token'] = csrf_token

    @app.before_request
    def protect_routes():
        if request.endpoint in (None, 'static'):
            return None
        if request.endpoint != 'auth.login':
            user_id = session.get('usuario_id')
            if not user_id or not db.session.get(Usuario, user_id):
                if user_id:
                    session.clear()
                if request.path.startswith('/api/'):
                    return jsonify(erro='Autenticação necessária.'), 401
                return redirect('/login')
        if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
            expected = session.get('csrf_token', '')
            if not expected or not hmac.compare_digest(expected, supplied):
                return jsonify(erro='Sessão inválida. Atualize a página e tente novamente.'), 400

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify(erro='Registro não encontrado.'), 404
        return error

    @app.cli.command('create-user')
    @click.option('--name', prompt='Nome')
    @click.option('--username', prompt='Usuário')
    @click.password_option(confirmation_prompt=True)
    def create_user(name, username, password):
        """Cria o primeiro usuário local sem credenciais padrão."""
        name, username = name.strip(), username.strip()
        if not name or not username or len(password) < 8:
            raise click.ClickException('Informe nome, usuário e senha de pelo menos 8 caracteres.')
        if Usuario.query.filter_by(usuario=username).first():
            raise click.ClickException('Usuário já existe.')
        user = Usuario(nome=name, usuario=username)
        user.set_senha(password)
        db.session.add(user)
        db.session.commit()
        click.echo('Usuário criado.')
    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.environ.get('PORT', '5000')), debug=False)
