"""Histórico de medições e modificações de cada projeto."""

from datetime import date
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from ..extensions import db
from ..helpers import date_field, money_field, number_field, owned_vehicle, text_field
from ..models import CarStats, Modification

bp = Blueprint("estatisticas", __name__, url_prefix="/estatisticas")


@bp.route("/<int:vehicle_id>", methods=["GET", "POST"])
@login_required
def edit(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    if request.method == "POST":
        try:
            stats = CarStats(
                vehicle_id=vehicle.id,
                date=date_field(),
                power=number_field("power", "Potência (cv)", 1, 10000, True),
                torque=number_field("torque", "Torque (Nm)", 1, 20000),
                zero_to_hundred=number_field("zero_to_hundred", "0–100 (s)", 0.1, 120),
                top_speed=number_field("top_speed", "Velocidade (km/h)", 1, 1000),
                consumption=number_field("consumption", "Consumo (km/l)", 0.1, 100),
            )
            db.session.add(stats)
            db.session.commit()
            flash("Medição registrada no histórico!", "success")
            return redirect(url_for("garagem.detail", vehicle_id=vehicle.id))
        except ValueError as error:
            flash(str(error), "error")
    return render_template(
        "estatisticas/edit.html",
        title="Performance & modificações",
        vehicle=vehicle,
        today=date.today().isoformat(),
    )


@bp.post("/<int:vehicle_id>/modificacoes")
@login_required
def add_modification(vehicle_id):
    owned_vehicle(vehicle_id)
    try:
        modification = Modification(
            vehicle_id=vehicle_id,
            name=text_field("name", "nome da modificação", 100, True),
            category=text_field("category", "categoria", 50, True),
            date=date_field(),
            value=money_field(),
        )
        db.session.add(modification)
        db.session.commit()
        flash("Modificação adicionada!", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("estatisticas.edit", vehicle_id=vehicle_id))


@bp.post("/<int:vehicle_id>/<kind>/<int:item_id>/excluir")
@login_required
def delete_item(vehicle_id, kind, item_id):
    owned_vehicle(vehicle_id)
    model = {"medicoes": CarStats, "modificacoes": Modification}.get(kind)
    if model is None:
        abort(404)
    item = db.get_or_404(model, item_id)
    if item.vehicle_id != vehicle_id:
        abort(404)
    db.session.delete(item)
    db.session.commit()
    flash("Registro removido.", "success")
    return redirect(url_for("estatisticas.edit", vehicle_id=vehicle_id))
