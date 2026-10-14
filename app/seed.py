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
    image.save(Path(current_app.config["UPLOAD_FOLDER"]) / filename, quality=82, optimize=True)
    return filename


def seed_database():
    """Adiciona exemplos repetíveis; preserva carros e medições editados pelo usuário."""
    users = []
    for user_index, (username, city, bio) in enumerate([
        ("lucas_gti", "São Paulo, SP", "Projetos turbo para o dia a dia. Cada modificação tem uma história."),
        ("ana_silva", "Curitiba, PR", "Café, estrada e motores aspirados. Um detalhe de cada vez."),
        ("pedro_rs", "Belo Horizonte, MG", "Da revisão aos pneus: construindo uma garagem para dirigir."),
        ("bia_abarth", "Porto Alegre, RS", "Pequenos esportivos, grandes viagens. Cuidando da manutenção antes de buscar potência."),
        ("rafa_turbo", "Rio de Janeiro, RJ", "Da oficina à estrada: torque para o uso diário, sem abrir mão da confiabilidade."),
        ("marina_boxer", "Florianópolis, SC", "Motores boxer, curvas de serra e fotografias dos caminhos que cada carro abre."),
        ("caio_track", "Campinas, SP", "Freios, pneus e medições. Minha garagem mistura projetos de rua e dias de pista."),
        ("julia_classicos", "Recife, PE", "Restaurando memórias com peças bem escolhidas. Originalidade e cuidado em cada detalhe."),
        ("diego_jdm", "Brasília, DF", "Engenharia japonesa e projetos aspirados. Primeiro revisão, depois a próxima melhoria."),
        ("luiza_hatch", "Salvador, BA", "Hatches leves para a cidade e a estrada. A melhor modificação é dirigir mais."),
        ("thiago_sedan", "Goiânia, GO", "Sedãs discretos, conforto e resposta. Guardando os números de cada etapa do projeto."),
        ("nina_estrada", "Fortaleza, CE", "Garagem para viajar: consumo medido, revisões em dia e histórias pelo litoral."),
    ]):
        user = db.session.scalar(db.select(User).filter_by(username=username))
        if not user:
            user = User(username=username, email=f"{username}@example.test", city=city, bio=bio, created_at=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(days=240-user_index*17))
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
    catalogue = [
        ("Fiat","500 Abarth",2015,160,230,7.4,211,11.5,"1.4 turbo",2,22),
        ("Mini","Cooper S",2019,192,280,6.8,235,12.1,"2.0 turbo",3,28),
        ("Audi","A3",2018,220,350,6.8,245,12.0,"2.0 TFSI",3,32),
        ("Chevrolet","Cruze",2020,153,240,9.0,214,12.5,"1.4 turbo",2,20),
        ("Peugeot","208 GT",2017,173,240,7.6,222,12.0,"1.6 THP",3,24),
        ("Subaru","WRX",2016,270,350,5.8,240,9.0,"2.0 boxer turbo",3,32),
        ("Subaru","BRZ",2018,200,205,7.6,226,12.2,"2.0 boxer",2,8),
        ("BMW","320i",2018,184,270,7.3,235,12.0,"2.0 turbo",3,35),
        ("Renault","Clio RS",2014,200,240,6.7,230,11.0,"1.6 turbo",3,25),
        ("Volkswagen","Up TSI",2018,105,165,9.3,182,14.5,"1.0 TSI",1,16),
        ("Honda","Fit",2015,116,150,11.2,175,13.7,"1.5 i-VTEC",1,4),
        ("Volkswagen","Gol GTI",1994,120,183,9.9,185,10.5,"2.0 8V",1,4),
        ("Chevrolet","Opala",1992,121,280,12.0,170,6.8,"4.1 seis cilindros",2,5),
        ("Nissan","Sentra",2019,140,196,10.1,190,12.5,"2.0 16V",1,5),
        ("Mitsubishi","Lancer",2015,160,197,10.2,200,11.8,"2.0 16V",2,6),
        ("Suzuki","Swift Sport",2015,142,167,8.7,195,13.0,"1.6 16V",2,5),
        ("Hyundai","HB20",2022,120,172,10.0,190,14.0,"1.0 turbo",1,12),
        ("Ford","Ka",2019,136,158,9.6,187,13.2,"1.5 12V",1,4),
        ("Toyota","Corolla",2021,177,210,9.2,199,13.0,"2.0 16V",2,6),
        ("Nissan","Versa",2021,114,156,11.7,185,14.1,"1.6 16V",1,4),
        ("Honda","City",2022,126,155,10.5,190,14.5,"1.5 i-VTEC",1,4),
        ("Hyundai","i30",2012,145,186,10.6,205,11.0,"2.0 16V",2,5),
        ("Kia","Cerato",2018,128,157,11.0,190,12.2,"1.6 16V",1,4),
        ("Renault","Megane RS",2014,265,360,6.0,254,10.0,"2.0 turbo",3,30),
        ("Fiat","Punto T-Jet",2015,152,207,8.3,203,10.9,"1.4 turbo",2,22),
        ("Peugeot","308",2018,165,240,8.5,215,12.4,"1.6 THP",2,24),
        ("Citroën","C4 Lounge",2019,165,240,8.6,215,12.0,"1.6 THP",2,24),
    ]
    cursor = 0
    palette = [("Vermelho","#c94432"),("Cinza","#767d89"),("Azul","#244f91"),("Branco","#c8c9c6"),("Preto","#24272d")]
    for owner, count in zip(range(3,12), [2,3,4,5,2,3,4,2,2]):
        for _ in range(count):
            brand,model,year,power,torque,acceleration,speed,consumption,engine,small_gain,big_gain = catalogue[cursor]
            color,paint=palette[cursor%len(palette)]
            examples.append((owner,brand,model,year,color,engine,"Manual 6 marchas" if cursor%2 else "Automático",paint,power,torque,acceleration,speed,consumption,small_gain,big_gain))
            cursor += 1
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
    for owner in range(3,12):
        car,_ = first_cars[owner]
        examples_posts.extend([
            (owner, 3+owner*5, f"Revisão concluída no {car.model}: alinhamento, pneus e fluidos conferidos. A próxima medição vem depois de alguns dias de uso."),
            (owner, 30+owner*9, f"Primeira saída de estrada com o {car.model}. Registrei consumo e resposta do motor para comparar com a próxima etapa. Como vocês acompanham a evolução?"),
        ])
    for index,(owner,hours,content) in enumerate(examples_posts):
        post=db.session.scalar(db.select(Post).filter_by(user_id=users[owner].id,text=content))
        if not post:
            car,paint=first_cars[owner]
            post=Post(author=users[owner],text=content,photo=demo_photo(paint,car.title),created_at=now-timedelta(hours=hours))
            db.session.add(post)
            db.session.flush()
        for offset in range(1+index%3 if index<6 else 2+index%7):
            other = (owner+offset+1)%(3 if index<6 else len(users))
            if not db.session.get(Like,(users[other].id,post.id)):
                db.session.add(Like(user_id=users[other].id,post_id=post.id))
        for offset in range(1+index%3):
            author=users[(owner+offset+1)%(3 if index<6 else len(users))]
            content_comment=["Que projeto bem cuidado! Como ficou o uso diário?","Gostei das escolhas. Qual foi a última medição?","Belo resultado! Vamos marcar um encontro de garagens."][(index+offset)%3]
            if not db.session.scalar(db.select(Comment).filter_by(post_id=post.id,user_id=author.id,text=content_comment)):
                db.session.add(Comment(post=post,author=author,text=content_comment,created_at=post.created_at+timedelta(minutes=8+offset*11)))
    db.session.commit()
