"""Seed opcional e repetível. Não substitui contas ou carros já cadastrados."""

from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4
from flask import current_app
from PIL import Image, ImageDraw, ImageFont
from .extensions import db
from .models import (
    CarStats,
    Follow,
    Friendship,
    Modification,
    Post,
    User,
    Vehicle,
    VehiclePhoto,
)


def demo_photo(color, title):
    """Desenha uma foto ilustrativa local, sem depender de bancos de imagens."""
    image = Image.new("RGB", (1100, 620))
    draw = ImageDraw.Draw(image)
    for y in range(620):
        shade = int(23 + y / 620 * 22)
        draw.line((0, y, 1100, y), fill=(shade, shade, shade + 5))
    for x in range(0, 1100, 130):
        draw.line((x, 0, x - 250, 620), fill=(51, 49, 53), width=2)
    draw.rectangle((0, 455, 1100, 620), fill=(21, 22, 27))
    draw.ellipse((140, 427, 965, 520), fill=(12, 13, 16))
    draw.polygon(
        [
            (150, 340),
            (220, 295),
            (350, 280),
            (430, 205),
            (645, 205),
            (775, 286),
            (900, 313),
            (938, 361),
            (910, 440),
            (184, 440),
            (145, 393),
        ],
        fill=color,
    )
    draw.polygon([(371, 283), (445, 220), (635, 220), (744, 283)], fill=(48, 62, 75))
    draw.line((558, 218, 558, 284), fill=color, width=12)
    draw.line((163, 347, 906, 347), fill=(212, 182, 163), width=2)
    draw.rectangle((395, 304, 422, 310), fill=(177, 174, 170))
    draw.rectangle((585, 304, 612, 310), fill=(177, 174, 170))
    draw.line((366, 288, 356, 417), fill=(55, 38, 38), width=2)
    draw.line((643, 288, 649, 417), fill=(55, 38, 38), width=2)
    draw.rectangle((844, 331, 918, 352), fill=(251, 235, 208))
    draw.rectangle((149, 335, 176, 364), fill=(200, 32, 29))
    draw.rectangle((180, 423, 908, 442), fill=(25, 26, 31))
    for x in (294, 767):
        draw.ellipse(
            (x - 70, 365, x + 70, 505), fill=(9, 10, 13), outline=(35, 36, 42), width=5
        )
        draw.ellipse(
            (x - 46, 389, x + 46, 481),
            fill=(49, 51, 57),
            outline=(146, 149, 157),
            width=5,
        )
        for dx, dy in ((0, 42), (40, 15), (26, -32), (-26, -32), (-40, 15)):
            draw.line((x, 435, x + dx, 435 + dy), fill=(155, 158, 166), width=8)
        draw.ellipse((x - 10, 425, x + 10, 445), fill=(193, 196, 203))
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = (
        ImageFont.truetype(str(font_path), 18)
        if font_path.exists()
        else ImageFont.load_default()
    )
    draw.text((46, 39), "GARAGEHUB / " + title.upper(), fill=(156, 151, 151), font=font)
    draw.text(
        (46, 562),
        "PROJETO DEMO  /  ILUSTRACAO CONCEITUAL",
        fill=(99, 100, 112),
        font=font,
    )
    filename = f"{uuid4().hex}.jpg"
    image.save(Path(current_app.config["UPLOAD_FOLDER"]) / filename, quality=90)
    return filename


def seed_database():
    users = []
    for username, city, bio in [
        (
            "lucas_gti",
            "São Paulo, SP",
            "Apaixonado por hot hatches. Cada modificação, uma nova história. #VW",
        ),
        (
            "ana_silva",
            "Curitiba, PR",
            "JDM na garagem, café na mão. Construindo meus projetos um detalhe por vez.",
        ),
        (
            "pedro_rs",
            "Belo Horizonte, MG",
            "A vida é curta para dirigir carros sem graça. Fã de turbo e rodas bem escolhidas.",
        ),
    ]:
        user = db.session.scalar(db.select(User).filter_by(username=username))
        if not user:
            user = User(
                username=username, email=f"{username}@example.test", city=city, bio=bio
            )
            user.set_password("GarageHub123!")
            db.session.add(user)
            db.session.flush()
        users.append(user)
    examples = [
        (
            0,
            "Volkswagen",
            "Golf GTI",
            2018,
            "Vermelho",
            "2.0 TSI",
            "DSG 6 marchas",
            "#c94432",
            230,
        ),
        (
            0,
            "Volkswagen",
            "Jetta GLI",
            2021,
            "Cinza",
            "2.0 TSI",
            "DSG 7 marchas",
            "#767d89",
            230,
        ),
        (
            1,
            "Honda",
            "Civic Si",
            2015,
            "Branco",
            "2.4 i-VTEC",
            "Manual 6 marchas",
            "#c8c9c6",
            206,
        ),
        (
            1,
            "Mazda",
            "MX-5",
            2016,
            "Vermelho",
            "2.0 Skyactiv",
            "Manual 6 marchas",
            "#b93038",
            160,
        ),
        (
            2,
            "Ford",
            "Focus RS",
            2017,
            "Azul",
            "2.3 EcoBoost",
            "Manual 6 marchas",
            "#357fa4",
            350,
        ),
    ]
    first_cars = {}
    today = date.today()
    for (
        owner,
        brand,
        model,
        year,
        color,
        engine,
        transmission,
        paint,
        power,
    ) in examples:
        user = users[owner]
        car = db.session.scalar(
            db.select(Vehicle).filter_by(
                user_id=user.id, brand=brand, model=model, year=year
            )
        )
        if not car:
            car = Vehicle(
                owner=user,
                brand=brand,
                model=model,
                year=year,
                color=color,
                engine=engine,
                transmission=transmission,
                description="Um projeto que nasceu da vontade de fazer diferente. Do uso diário aos detalhes de performance, cada escolha tem um motivo. Fotos ilustrativas para demonstrar a GarageHub.",
                viewer_config={
                    "paint_color": paint,
                    "wheel_color": "#bfc4cc",
                    "wheel_size": 1.05,
                    "suspension": "lowered",
                    "spoiler": owner == 2,
                },
            )
            car.photos.append(VehiclePhoto(filename=demo_photo(paint, car.title)))
            for days, extra in [(150, 0), (90, 15), (15, 35)]:
                car.stats.append(
                    CarStats(
                        date=today - timedelta(days=days),
                        power=power + extra,
                        torque=power * 1.5 + extra,
                        zero_to_hundred=6.5,
                        top_speed=240,
                        consumption=10.2,
                    )
                )
            car.modifications.append(
                Modification(
                    name="Remap stage 1",
                    category="Motor",
                    date=today - timedelta(days=90),
                    value=2500,
                )
            )
            car.modifications.append(
                Modification(
                    name="Filtro esportivo",
                    category="Motor",
                    date=today - timedelta(days=15),
                    value=680,
                )
            )
            db.session.add(car)
        first_cars.setdefault(owner, (car, paint))
    for follower, followed in [(0, 1), (0, 2), (1, 0), (2, 0)]:
        if not db.session.get(Follow, (users[follower].id, users[followed].id)):
            db.session.add(
                Follow(follower_id=users[follower].id, followed_id=users[followed].id)
            )
    low, high = sorted([users[0].id, users[1].id])
    if not db.session.scalar(
        db.select(Friendship).filter_by(user_low_id=low, user_high_id=high)
    ):
        db.session.add(
            Friendship(
                user_low_id=low,
                user_high_id=high,
                requester_id=users[0].id,
                status="accepted",
            )
        )
    for index, text in enumerate(
        [
            "Fim de semana dedicado ao GTI. Filtro novo, revisão em dia e mais um capítulo desse projeto. Quem mais passou o sábado na garagem? 🔧",
            "O Civic ganhou atenção nos detalhes hoje. Nem toda evolução aparece no dinamômetro — às vezes está no cuidado. Qual é o próximo passo do seu projeto?",
            "350 cv de fábrica e uma lista de ideias que só cresce. Cheguei à GarageHub para trocar experiências e acompanhar as garagens de vocês!",
        ]
    ):
        if not db.session.scalar(
            db.select(Post).filter_by(user_id=users[index].id, text=text)
        ):
            car, paint = first_cars[index]
            db.session.add(
                Post(author=users[index], text=text, photo=demo_photo(paint, car.title))
            )
    db.session.commit()
