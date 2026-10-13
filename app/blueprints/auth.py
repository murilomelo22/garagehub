"""Cadastro e sessões com senha hash e validação no servidor."""

import re
from urllib.parse import urlsplit
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..helpers import text_field
from ..models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("social.feed"))
    if request.method == "POST":
        try:
            username = text_field("username", "nome de usuário", 30, True).lower()
            email = text_field("email", "e-mail", 254, True).lower()
            password = request.form.get("password", "")
            if not re.fullmatch(r"[a-z0-9_]{3,30}", username):
                raise ValueError(
                    "O usuário deve ter de 3 a 30 letras, números ou underscores."
                )
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                raise ValueError("Informe um e-mail válido.")
            if not 8 <= len(password) <= 128:
                raise ValueError("A senha deve ter entre 8 e 128 caracteres.")
            if db.session.scalar(
                db.select(User).where(
                    or_(User.username == username, User.email == email)
                )
            ):
                raise ValueError("Este usuário ou e-mail já está cadastrado.")
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Bem-vindo à GarageHub! Sua garagem começa aqui.", "success")
            return redirect(url_for("garagem.index"))
        except (ValueError, IntegrityError) as error:
            db.session.rollback()
            flash(
                (
                    str(error)
                    if isinstance(error, ValueError)
                    else "Este usuário ou e-mail já está cadastrado."
                ),
                "error",
            )
    return render_template("auth/form.html", title="Crie sua conta", mode="register")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("social.feed"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(
            db.select(User).where(
                or_(User.username == identity, User.email == identity)
            )
        )
        if user and len(password) <= 128 and user.check_password(password):
            login_user(user)
            target = request.args.get("next", "")
            # Redirecionamentos aceitam somente caminhos locais para evitar phishing.
            parsed = urlsplit(target)
            if (
                not target.startswith("/")
                or target.startswith("//")
                or "\\" in target
                or parsed.netloc
                or parsed.scheme
            ):
                target = url_for("social.feed")
            return redirect(target)
        flash("Usuário/e-mail ou senha incorretos.", "error")
    return render_template("auth/form.html", title="Bom te ver de novo", mode="login")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))
