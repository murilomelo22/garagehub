"""Validações reutilizáveis e armazenamento seguro de imagens locais."""

import math
import re
import warnings
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4
from flask import abort, current_app, request
from flask_login import current_user
from PIL import Image, UnidentifiedImageError
from .extensions import db
from .models import Vehicle


def text_field(name, label, maximum, required=False):
    value = request.form.get(name, "").strip()
    if required and not value:
        raise ValueError(f"Preencha {label}.")
    if len(value) > maximum:
        raise ValueError(f"{label} deve ter até {maximum} caracteres.")
    return value


def number_field(name, label, minimum, maximum, required=False, integer=False):
    raw = request.form.get(name, "").strip().replace(",", ".")
    if not raw and not required:
        return None
    try:
        value = int(raw) if integer else float(raw)
        if not math.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError
    except (ValueError, OverflowError):
        raise ValueError(
            f"{label}: informe um número entre {minimum} e {maximum}."
        ) from None
    return value


def date_field():
    try:
        value = datetime.strptime(request.form.get("date", ""), "%Y-%m-%d").date()
        if not date(1900, 1, 1) <= value <= date.today():
            raise ValueError
        return value
    except ValueError:
        raise ValueError("Informe uma data válida, entre 1900 e hoje.") from None


def money_field():
    try:
        value = Decimal(request.form.get("value", "").strip().replace(",", "."))
        if not value.is_finite() or not Decimal("0") <= value <= Decimal(
            "9999999999.99"
        ):
            raise InvalidOperation
        return value.quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValueError(
            "Informe um valor válido e positivo para a modificação."
        ) from None


def owned_vehicle(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    if vehicle.user_id != current_user.id:
        abort(403)
    return vehicle


def save_image(file):
    if not file or not file.filename:
        return None
    # Não confiamos na extensão nem no MIME enviados pelo navegador.
    if Path(file.filename).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError("Use uma imagem JPG, PNG ou WebP.")
    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > 6 * 1024 * 1024:
        raise ValueError("Cada foto deve ter no máximo 6 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(file.stream) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Formato de imagem não suportado.")
                from PIL import ImageOps

                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((1920, 1920))
                filename = f"{uuid4().hex}.jpg"
                image.save(
                    Path(current_app.config["UPLOAD_FOLDER"]) / filename,
                    "JPEG",
                    quality=88,
                )
                return filename
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValueError(
            "Não foi possível ler essa imagem. Escolha outra foto."
        ) from None


def remove_image(filename):
    if filename and re.fullmatch(r"[a-zA-Z0-9_-]+\.jpg", filename):
        (Path(current_app.config["UPLOAD_FOLDER"]) / filename).unlink(missing_ok=True)
