"""Perfil público e edição dos dados pessoais."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from ..extensions import db
from ..helpers import remove_image, save_image, text_field
from ..models import Follow, Friendship, User

bp = Blueprint("perfil", __name__)


@bp.get("/perfil")
@login_required
def me():
    return redirect(url_for("perfil.public", username=current_user.username))


@bp.get("/u/<username>")
def public(username):
    user = db.first_or_404(db.select(User).where(User.username == username.lower()))
    following = False
    friendship = None
    if current_user.is_authenticated and current_user.id != user.id:
        following = db.session.get(Follow, (current_user.id, user.id)) is not None
        low, high = sorted([current_user.id, user.id])
        friendship = db.session.scalar(
            db.select(Friendship).filter_by(user_low_id=low, user_high_id=high)
        )
    followers = db.session.scalar(
        db.select(db.func.count())
        .select_from(Follow)
        .where(Follow.followed_id == user.id)
    )
    return render_template(
        "perfil/public.html",
        title=f"Garagem de @{user.username}",
        user=user,
        following=following,
        friendship=friendship,
        followers=followers,
    )


@bp.route("/perfil/editar", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        image = None
        try:
            bio = text_field("bio", "bio", 500)
            city = text_field("city", "cidade", 80)
            image = save_image(request.files.get("photo"))
            old_image = current_user.photo
            current_user.bio, current_user.city = bio, city
            if image:
                current_user.photo = image
            db.session.commit()
            if image:
                remove_image(old_image)
            flash("Perfil atualizado!", "success")
            return redirect(url_for("perfil.public", username=current_user.username))
        except ValueError as error:
            remove_image(image)
            flash(str(error), "error")
    return render_template("perfil/edit.html", title="Editar perfil")
