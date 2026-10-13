"""Garagem, fotos e proteção das alterações por propriedade do veículo."""

from datetime import date
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from ..extensions import db
from ..helpers import number_field, owned_vehicle, remove_image, save_image, text_field
from ..models import Vehicle, VehiclePhoto

bp = Blueprint("garagem", __name__, url_prefix="/garagem")


@bp.get("/")
@login_required
def index():
    return render_template(
        "garagem/index.html", title="Minha garagem", vehicles=current_user.vehicles
    )


def vehicle_fields():
    return dict(
        brand=text_field("brand", "marca", 50, True),
        model=text_field("model", "modelo", 80, True),
        year=number_field("year", "Ano", 1886, date.today().year + 1, True, True),
        color=text_field("color", "cor", 40, True),
        engine=text_field("engine", "motor", 80),
        transmission=text_field("transmission", "câmbio", 50),
        description=text_field("description", "descrição", 2000),
    )


def edit_vehicle(vehicle=None):
    if request.method == "POST":
        saved = []
        try:
            fields = vehicle_fields()
            uploads = [
                file for file in request.files.getlist("photos") if file.filename
            ]
            if (
                len(uploads) > 5
                or len(uploads) + (len(vehicle.photos) if vehicle else 0) > 15
            ):
                raise ValueError(
                    "Envie até 5 fotos por vez, com limite de 15 por carro."
                )
            for upload in uploads:
                saved.append(save_image(upload))
            car = vehicle or Vehicle(user_id=current_user.id)
            for key, value in fields.items():
                setattr(car, key, value)
            for filename in saved:
                car.photos.append(VehiclePhoto(filename=filename))
            db.session.add(car)
            db.session.commit()
            flash(
                "Veículo atualizado!" if vehicle else "Novo projeto na garagem!",
                "success",
            )
            return redirect(url_for("garagem.detail", vehicle_id=car.id))
        except ValueError as error:
            for filename in saved:
                remove_image(filename)
            flash(str(error), "error")
    return render_template(
        "garagem/form.html",
        title="Editar veículo" if vehicle else "Adicionar veículo",
        vehicle=vehicle,
        max_year=date.today().year + 1,
    )


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def create():
    return edit_vehicle()


@bp.route("/<int:vehicle_id>/editar", methods=["GET", "POST"])
@login_required
def edit(vehicle_id):
    return edit_vehicle(owned_vehicle(vehicle_id))


@bp.get("/<int:vehicle_id>")
def detail(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    from .visualizador import DEFAULT_CONFIG

    chart = {
        "labels": [item.date.isoformat() for item in vehicle.stats],
        "power": [item.power for item in vehicle.stats],
    }
    return render_template(
        "garagem/detail.html",
        title=vehicle.title,
        vehicle=vehicle,
        chart=chart,
        viewer_config=vehicle.viewer_config or DEFAULT_CONFIG,
    )


@bp.post("/<int:vehicle_id>/excluir")
@login_required
def delete(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    photos = [photo.filename for photo in vehicle.photos]
    db.session.delete(vehicle)
    db.session.commit()
    for filename in photos:
        remove_image(filename)
    flash("Veículo excluído da sua garagem.", "success")
    return redirect(url_for("garagem.index"))


@bp.post("/<int:vehicle_id>/fotos/<int:photo_id>/excluir")
@login_required
def delete_photo(vehicle_id, photo_id):
    owned_vehicle(vehicle_id)
    photo = db.get_or_404(VehiclePhoto, photo_id)
    if photo.vehicle_id != vehicle_id:
        abort(404)
    filename = photo.filename
    db.session.delete(photo)
    db.session.commit()
    remove_image(filename)
    flash("Foto removida.", "success")
    return redirect(url_for("garagem.edit", vehicle_id=vehicle_id))
