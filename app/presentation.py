"""Formatação de apresentação, mantendo datas armazenadas em UTC."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BRASILIA = ZoneInfo("America/Sao_Paulo")


def number_br(value):
    if value is None:
        return "—"
    formatted = f"{float(value):,.2f}".rstrip("0").rstrip(".")
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def money_br(value):
    return "R$ " + f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def brasilia(value):
    return value.replace(tzinfo=timezone.utc).astimezone(BRASILIA) if value.tzinfo is None else value.astimezone(BRASILIA)


def relative_time(value):
    local = brasilia(value)
    now = datetime.now(BRASILIA)
    seconds = max(0, (now - local).total_seconds())
    if seconds < 60:
        return "agora"
    if seconds < 3600:
        return f"há {int(seconds // 60)} min"
    if local.date() == now.date():
        return f"há {int(seconds // 3600)} h"
    if (now.date() - local.date()).days == 1:
        return "ontem"
    return local.strftime("%d/%m/%Y")
