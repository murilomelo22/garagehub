"""Fábrica Flask: configuração local, blueprints e respostas de erro."""

import os
import secrets
from pathlib import Path
import click
from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix
from .extensions import csrf, db, login_manager


def create_app(test_config=None):
    production = os.getenv("GARAGEHUB_ENV", "development").lower() == "production"
    data_dir = os.getenv("GARAGEHUB_DATA_DIR")
    instance_options = {"instance_path": str(Path(data_dir).resolve())} if data_dir else {}
    app = Flask(__name__, instance_relative_config=True, **instance_options)
    configured_key = (test_config or {}).get("SECRET_KEY") or os.getenv("SECRET_KEY")
    if production and (not configured_key or len(configured_key) < 32):
        raise RuntimeError("Em produção, defina SECRET_KEY com pelo menos 32 caracteres.")
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    # A chave local persiste entre reinícios. Em produção, use SECRET_KEY no ambiente.
    key_path = Path(app.instance_path) / "secret.key"
    if not configured_key:
        try:
            with key_path.open("x") as key_file:
                key_file.write(secrets.token_hex(32))
            key_path.chmod(0o600)
        except FileExistsError:
            pass
    app.config.from_mapping(
        SECRET_KEY=configured_key or (key_path.read_text() if key_path.exists() else None),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///garagehub.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(Path(app.instance_path) / "uploads"),
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SECURE=production,
    )
    if test_config:
        app.config.update(test_config)
    # Ative apenas atrás de um proxy confiável que substitua os cabeçalhos.
    if os.getenv("GARAGEHUB_TRUST_PROXY") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    from .presentation import brasilia, money_br, number_br, relative_time
    app.jinja_env.filters.update(number_br=number_br, money_br=money_br, brasilia=brasilia, relative_time=relative_time)
    app.config.setdefault("PREVIEW_MODE", False)

    @app.context_processor
    def presentation_context():
        return {"preview_mode": app.config["PREVIEW_MODE"]}
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre na sua conta para continuar."
    login_manager.login_message_category = "info"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id)) if user_id.isdigit() else None

    from .blueprints import auth, perfil, garagem, social, estatisticas, visualizador

    for module in (auth, perfil, garagem, social, estatisticas, visualizador):
        app.register_blueprint(module.bp)

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Banco indisponível na verificação de saúde")
            return {"status": "unavailable"}, 503
        return {"status": "ok"}

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if production and request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("social.feed"))
        from datetime import date, timedelta
        from .blueprints.visualizador import DEFAULT_CONFIG
        today = date.today()
        chart = {"labels": [(today-timedelta(days=days)).isoformat() for days in (150,90,15)],
                 "power": [230,233,268], "torque": [350,355.2,416.5], "zero_to_hundred": [6.5,6.44,5.83], "consumption": [10.2,10.19,10.07]}
        config = DEFAULT_CONFIG | {"paint_color":"#c94432", "wheel_size":1.0, "suspension":"lowered"}
        return render_template("landing.html", home_demo=True, chart=chart, viewer_config=config, viewer_defaults=config, title="Projetos, histórias e comunidade", meta_description="GarageHub: sua garagem digital para acompanhar projetos, compartilhar evolução e conhecer a comunidade automotiva.")

    @app.get("/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, max_age=86400)

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return (
            render_template(
                "error.html",
                title="Formulário expirado",
                message="Atualize a página e envie o formulário novamente.",
            ),
            400,
        )

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def friendly_error(error):
        messages = {
            400: "Não foi possível processar essa solicitação.",
            403: "Você não tem permissão para alterar este conteúdo.",
            404: "Esta página não foi encontrada.",
            413: "O envio passou de 32 MB. Escolha fotos menores (até 6 MB por foto).",
        }
        return (
            render_template(
                "error.html",
                title=f"Ops, erro {error.code}",
                message=messages[error.code],
            ),
            error.code,
        )

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.exception("Falha de persistência")
        return (
            render_template(
                "error.html",
                title="Tente novamente",
                message="Não foi possível salvar agora. Tente novamente em instantes.",
            ),
            500,
        )

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return (
            render_template(
                "error.html",
                title="Tente novamente",
                message="Algo deu errado. Tente novamente em instantes.",
            ),
            500,
        )

    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas ausentes sem apagar dados existentes."""
        db.create_all()
        click.echo("Banco da GarageHub inicializado.")

    @app.cli.command("seed")
    def seed_command():
        from .seed import seed_database

        seed_database()
        click.echo(
            "Seed concluído: 12 perfis e 36 carros de demonstração. Senha: GarageHub123!"
        )

    with app.app_context():
        db.create_all()
    return app
