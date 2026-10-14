"""Seed opcional e repetível. Não substitui contas ou carros já cadastrados."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from flask import current_app
from PIL import Image, ImageDraw, ImageFont
from .extensions import db
from .models import (
    CarStats,
    Comment,
    Like,
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
    """Adiciona exemplos repetíveis; preserva carros e medições editados pelo usuário."""
    users = []
    for username, city, bio in [
        ("lucas_gti", "São Paulo, SP", "Projetos turbo para o dia a dia. Cada modificação tem uma história."),
        ("ana_silva", "Curitiba, PR", "Café, estrada e motores aspirados. Um detalhe de cada vez."),
        ("pedro_rs", "Belo Horizonte, MG", "Da revisão aos pneus: construindo uma garagem para dirigir."),
    ]:
        user = db.session.scalar(db.select(User).filter_by(username=username))
        if not user:
            user = User(username=username, email=f"{username}@example.test", city=city, bio=bio)
            user.set_password("GarageHub123!")
            db.session.add(user)
            db.session.flush()
        users.append(user)
    # Potência, torque, aceleração, máxima e consumo originais variam por projeto.
    examples = [
        (0,"Volkswagen","Golf GTI",2018,"Vermelho","2.0 TSI","DSG 6 marchas","#c94432",230,350,6.5,244,10.2,3,35),
        (0,"Volkswagen","Jetta GLI",2021,"Cinza","2.0 TSI","DSG 7 marchas","#767d89",230,350,6.7,250,10.5,4,35),
        (1,"Honda","Civic Si",2015,"Branco","2.4 i-VTEC","Manual 6 marchas","#c8c9c6",206,244,7.1,225,11.2,2,8),
        (1,"Mazda","MX-5",2016,"Vermelho","2.0 Skyactiv","Manual 6 marchas","#b93038",160,200,7.3,214,12.0,2,7),
        (2,"Ford","Focus RS",2017,"Azul","2.3 EcoBoost","Manual 6 marchas","#357fa4",350,440,4.7,266,8.2,4,48),
        (0,"Volkswagen","Polo GTS",2020,"Azul","1.4 TSI","Automático 6 marchas","#244f91",150,250,8.4,207,11.7,3,25),
        (1,"Toyota","GT86",2017,"Cinza","2.0 boxer","Manual 6 marchas","#888c97",200,205,7.6,226,12.4,3,9),
        (2,"Ford","Fiesta ST",2016,"Vermelho","1.6 EcoBoost","Manual 6 marchas","#bb3832",182,240,6.9,223,12.0,3,30),
        (2,"Renault","Sandero RS",2019,"Preto","2.0 16V","Manual 6 marchas","#24272d",150,205,8.0,202,10.8,2,8),
    ]
    first_cars = {}
    today = date.today()
    for index, example in enumerate(examples):
        owner,brand,model,year,color,engine,transmission,paint,power,torque,acceleration,speed,consumption,filter_gain,remap_gain = example
        user = users[owner]
        car = db.session.scalar(db.select(Vehicle).filter_by(user_id=user.id,brand=brand,model=model,year=year))
        fresh = car is None
        if fresh:
            car = Vehicle(owner=user,brand=brand,model=model,year=year,color=color,engine=engine,transmission=transmission,
                description=f"Projeto de uso diário, com manutenção em dia e evolução gradual. Filtro esportivo: aproximadamente +{filter_gain} cv. Remapeamento: aproximadamente +{remap_gain} cv. Medições e fotos ilustrativas da demonstração.",
                viewer_config={"paint_color":paint,"wheel_color":"#bfc4cc","wheel_size":1.0+(index%3)*0.05,"suspension":"lowered" if index%2==0 else "original","spoiler":owner==2})
            car.photos.append(VehiclePhoto(filename=demo_photo(paint,car.title)))
            db.session.add(car)
        # Reconhece apenas os números repetidos do seed V0.0, sem tocar em históricos reais.
        legacy = (len(car.stats)==3 and [s.power for s in car.stats]==[power,power+15,power+35]
                  and all(s.zero_to_hundred==6.5 and s.top_speed==240 and s.consumption==10.2 for s in car.stats))
        if fresh or legacy:
            if legacy:
                car.stats.clear()
                # Corrige somente as duas modificações originais da demonstração.
                for modification in car.modifications:
                    if modification.name=="Filtro esportivo": modification.date=today-timedelta(days=90)
                    if modification.name=="Remap stage 1": modification.date=today-timedelta(days=15)
            for days,gain in [(150,0),(90,filter_gain),(15,filter_gain+remap_gain)]:
                ratio=gain/power
                car.stats.append(CarStats(date=today-timedelta(days=days),power=power+gain,
                    torque=round(torque*(1+ratio*1.15),1),zero_to_hundred=round(acceleration/(1+ratio*0.7),2),
                    top_speed=round(speed*(1+ratio)**(1/3),1),consumption=round(consumption*(1-ratio*0.08),2)))
        if fresh:
            car.modifications.extend([
                Modification(name=f"Filtro esportivo (+{filter_gain} cv estimados)",category="Motor",date=today-timedelta(days=90),value=680),
                Modification(name=f"Remapeamento (+{remap_gain} cv estimados)",category="Motor",date=today-timedelta(days=15),value=2500),
            ])
        first_cars.setdefault(owner,(car,paint))
    db.session.flush()
    for follower,followed in [(0,1),(1,0),(2,0)]:
        if not db.session.get(Follow,(users[follower].id,users[followed].id)):
            db.session.add(Follow(follower_id=users[follower].id,followed_id=users[followed].id))
    low,high=sorted([users[0].id,users[1].id])
    if not db.session.scalar(db.select(Friendship).filter_by(user_low_id=low,user_high_id=high)):
        db.session.add(Friendship(user_low_id=low,user_high_id=high,requester_id=users[0].id,status="accepted"))
    now=datetime.now(timezone.utc).replace(tzinfo=None)
    examples_posts=[
        (0,2,"Fim de semana dedicado ao GTI. Filtro novo, revisão em dia e mais um capítulo desse projeto. Quem mais passou o sábado na garagem? 🔧"),
        (1,26,"O Civic ganhou atenção nos detalhes hoje. Nem toda evolução aparece no dinamômetro — às vezes está no cuidado. Qual é o próximo passo do seu projeto?"),
        (2,6,"350 cv de fábrica e uma lista de ideias que só cresce. Cheguei à GarageHub para trocar experiências e acompanhar as garagens de vocês!"),
        (0,50,"O Jetta ficou pronto para a estrada. Pneus revisados e uma rota de serra no roteiro."),
        (1,0.8,"Manhã de revisão no MX-5: óleo, alinhamento e um bom café. O próximo projeto é o GT86."),
        (2,74,"O Fiesta ST ganhou pneus novos. A diferença nas curvas vale mais que qualquer número."),
    ]
    for index,(owner,hours,content) in enumerate(examples_posts):
        post=db.session.scalar(db.select(Post).filter_by(user_id=users[owner].id,text=content))
        if not post:
            car,paint=first_cars[owner]
            post=Post(author=users[owner],text=content,photo=demo_photo(paint,car.title),created_at=now-timedelta(hours=hours))
            db.session.add(post)
            db.session.flush()
        for other in range(3):
            if (index+other)%3!=0 and not db.session.get(Like,(users[other].id,post.id)):
                db.session.add(Like(user_id=users[other].id,post_id=post.id))
        for offset in range(1+index%3):
            author=users[(owner+offset+1)%3]
            content_comment=["Que projeto bem cuidado! Como ficou o uso diário?","Gostei das escolhas. Qual foi a última medição?","Belo resultado! Vamos marcar um encontro de garagens."][(index+offset)%3]
            if not db.session.scalar(db.select(Comment).filter_by(post_id=post.id,user_id=author.id,text=content_comment)):
                db.session.add(Comment(post=post,author=author,text=content_comment,created_at=post.created_at+timedelta(minutes=8+offset*11)))
    db.session.commit()
