"""Configuração persistente do carro genérico 3D, independente do modelo real."""

import re
from flask import Blueprint, flash, jsonify, redirect, request, url_for
from flask_login import login_required
from ..extensions import db
from ..helpers import number_field, owned_vehicle

bp = Blueprint("visualizador", __name__, url_prefix="/visualizador")
DEFAULT_CONFIG = {
    "paint_color": "#ef492f",
    "wheel_color": "#cbd0d7",
    "wheel_size": 1.0,
    "suspension": "original",
    "spoiler": False,
}


@bp.post("/<int:vehicle_id>")
@login_required
def save(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    try:
        config = {}
        for key in ("paint_color", "wheel_color"):
            value = request.form.get(key, "")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError("Escolha cores válidas para a pintura e as rodas.")
            config[key] = value
        config["wheel_size"] = number_field(
            "wheel_size", "Tamanho das rodas", 0.8, 1.3, True
        )
        config["suspension"] = request.form.get("suspension", "")
        if config["suspension"] not in {"original", "lowered"}:
            raise ValueError("Escolha uma altura de suspensão válida.")
        if request.form.get("spoiler") not in {"yes", "no"}:
            raise ValueError("Escolha se deseja spoiler.")
        config["spoiler"] = request.form["spoiler"] == "yes"
        vehicle.viewer_config = config
        db.session.commit()
        if request.headers.get("Accept") == "application/json":
            return jsonify(message="Visual salvo na sua garagem!", config=config)
        flash("Visual 3D salvo!", "success")
    except ValueError as error:
        if request.headers.get("Accept") == "application/json":
            return jsonify(message=str(error)), 400
        flash(str(error), "error")
    return redirect(url_for("garagem.detail", vehicle_id=vehicle_id) + "#visualizador")
