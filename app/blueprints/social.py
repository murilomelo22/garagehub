"""Feed cronológico, seguidores, amizades e interações da comunidade."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..helpers import remove_image, save_image, text_field
from ..models import Comment, Follow, Friendship, Like, Post, User, Vehicle

bp = Blueprint("social", __name__)


@bp.get("/feed")
@login_required
def feed():
    feed_filter = request.args.get("filter", "following")
    if feed_filter not in {"all", "following"}:
        feed_filter = "following"
    brand = request.args.get("brand", "").strip()[:50]
    followed = db.select(Follow.followed_id).where(
        Follow.follower_id == current_user.id
    )
    query = db.select(Post).order_by(Post.created_at.desc(), Post.id.desc())
    if feed_filter == "following":
        query = query.where(or_(Post.user_id == current_user.id, Post.user_id.in_(followed)))
    if brand:
        query = query.where(Post.author.has(User.vehicles.any(Vehicle.brand == brand)))
    brands = db.session.scalars(db.select(Vehicle.brand).distinct().order_by(Vehicle.brand)).all()
    page = db.paginate(query, per_page=10, max_per_page=10, error_out=False)
    suggestions = db.session.scalars(
        db.select(User)
        .where(User.id != current_user.id, ~User.id.in_(followed))
        .order_by(User.id)
        .limit(3)
    ).all()
    liked_ids = set(
        db.session.scalars(
            db.select(Like.post_id).where(Like.user_id == current_user.id)
        )
    )
    following_count = db.session.scalar(
        db.select(db.func.count())
        .select_from(Follow)
        .where(Follow.follower_id == current_user.id)
    )
    return render_template(
        "social/feed.html",
        title="Seu feed",
        page=page,
        suggestions=suggestions,
        liked_ids=liked_ids,
        following_count=following_count,
        feed_filter=feed_filter,
        brand=brand,
        brands=brands,
    )


@bp.post("/posts")
@login_required
def create_post():
    image = None
    try:
        text = text_field("text", "post", 2000)
        file = request.files.get("photo")
        if not text and not (file and file.filename):
            raise ValueError("Escreva algo ou escolha uma foto para publicar.")
        image = save_image(file)
        db.session.add(Post(user_id=current_user.id, text=text, photo=image))
        db.session.commit()
        flash("Post publicado!", "success")
    except ValueError as error:
        remove_image(image)
        flash(str(error), "error")
    return redirect(url_for("social.feed"))


@bp.post("/posts/<int:post_id>/curtir")
@login_required
def like(post_id):
    db.get_or_404(Post, post_id)
    item = db.session.get(Like, (current_user.id, post_id))
    if item:
        db.session.delete(item)
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post_id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
    return redirect(url_for("social.feed") + f"#post-{post_id}")


@bp.post("/posts/<int:post_id>/comentar")
@login_required
def comment(post_id):
    db.get_or_404(Post, post_id)
    try:
        text = text_field("text", "comentário", 500, True)
        db.session.add(Comment(user_id=current_user.id, post_id=post_id, text=text))
        db.session.commit()
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("social.feed") + f"#post-{post_id}")


@bp.post("/posts/<int:post_id>/excluir")
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != current_user.id:
        abort(403)
    photo = post.photo
    db.session.delete(post)
    db.session.commit()
    remove_image(photo)
    flash("Post excluído.", "success")
    return redirect(url_for("social.feed"))


@bp.get("/amigos")
@login_required
def friends():
    q = request.args.get("q", "").strip()[:100]
    city = request.args.get("city", "").strip()[:80]
    brand = request.args.get("brand", "").strip()[:50]
    query = db.select(User).where(User.id != current_user.id)
    if q:
        # O EXISTS evita duplicar usuários com vários carros encontrados.
        query = query.where(
            or_(
                User.username.contains(q, autoescape=True),
                User.city.contains(q, autoescape=True),
                User.vehicles.any(
                    or_(
                        Vehicle.brand.contains(q, autoescape=True),
                        Vehicle.model.contains(q, autoescape=True),
                    )
                ),
            )
        )
    if city:
        query = query.where(User.city == city)
    if brand:
        query = query.where(User.vehicles.any(Vehicle.brand == brand))
    page = db.paginate(
        query.order_by(User.username), per_page=12, max_per_page=12, error_out=False
    )
    links = db.session.scalars(
        db.select(Friendship).where(
            or_(
                Friendship.user_low_id == current_user.id,
                Friendship.user_high_id == current_user.id,
            )
        )
    ).all()
    friendships = {link.other_id(current_user.id): link for link in links}
    users_by_id = {
        user.id: user
        for user in db.session.scalars(db.select(User).where(User.id.in_(friendships)))
    }
    following_ids = set(
        db.session.scalars(
            db.select(Follow.followed_id).where(Follow.follower_id == current_user.id)
        )
    )
    return render_template(
        "social/friends.html",
        title="Amigos & comunidade",
        q=q,
        page=page,
        friendships=friendships,
        users_by_id=users_by_id,
        following_ids=following_ids,
        city=city, brand=brand,
        cities=db.session.scalars(db.select(User.city).where(User.city != "").distinct().order_by(User.city)).all(),
        brands=db.session.scalars(db.select(Vehicle.brand).distinct().order_by(Vehicle.brand)).all(),
    )


@bp.post("/usuarios/<int:user_id>/seguir")
@login_required
def follow(user_id):
    db.get_or_404(User, user_id)
    if user_id == current_user.id:
        abort(400)
    item = db.session.get(Follow, (current_user.id, user_id))
    if item:
        db.session.delete(item)
        message = "Você deixou de seguir este usuário."
    else:
        db.session.add(Follow(follower_id=current_user.id, followed_id=user_id))
        message = "Agora você acompanha os posts deste usuário."
    try:
        db.session.commit()
        flash(message, "success")
    except IntegrityError:
        db.session.rollback()
        flash("Você já segue este usuário.", "info")
    return redirect(
        url_for("perfil.public", username=db.session.get(User, user_id).username)
    )


@bp.post("/usuarios/<int:user_id>/amizade/<action>")
@login_required
def friendship(user_id, action):
    db.get_or_404(User, user_id)
    if user_id == current_user.id:
        abort(400)
    low, high = sorted([user_id, current_user.id])
    item = db.session.scalar(
        db.select(Friendship).filter_by(user_low_id=low, user_high_id=high)
    )
    if action == "solicitar":
        if item:
            flash("Já existe uma amizade ou solicitação entre vocês.", "info")
        else:
            db.session.add(
                Friendship(
                    user_low_id=low, user_high_id=high, requester_id=current_user.id
                )
            )
            flash("Pedido de amizade enviado!", "success")
    elif action == "aceitar":
        if not item or item.status != "pending" or item.requester_id == current_user.id:
            abort(403)
        item.status = "accepted"
        flash("Amizade aceita!", "success")
    elif action in {"recusar", "cancelar", "remover"}:
        if not item:
            abort(404)
        if action == "recusar" and (
            item.status != "pending" or item.requester_id == current_user.id
        ):
            abort(403)
        if action == "cancelar" and (
            item.status != "pending" or item.requester_id != current_user.id
        ):
            abort(403)
        if action == "remover" and item.status != "accepted":
            abort(403)
        db.session.delete(item)
        flash("Amizade ou pedido removido.", "info")
    else:
        abort(404)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("O pedido já foi registrado. Atualize a página.", "info")
    return redirect(url_for("social.friends"))
