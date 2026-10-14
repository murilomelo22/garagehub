"""Exporta a prévia interativa sem ler contas, sessões ou uploads reais."""

from hashlib import sha256
from html import escape, unescape
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import render_template_string
from app import create_app
from app.extensions import db
from app.models import Follow, Friendship, Post, User, Vehicle
from app.seed import seed_database

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
SITE_URL = os.getenv("GARAGEHUB_SITE_URL", "https://murilomelo22.github.io/garagehub").rstrip("/")
BANNER = ('<aside class="preview-banner" aria-label="Modo demonstração">'
          '<strong>PRÉVIA INTERATIVA</strong><span>Seus testes ficam apenas neste navegador.</span>'
          '<a href="acesso.html">Sobre a demonstração</a></aside>')


def export_html(source, routes, uploads, data, destination):
    """Reescreve caminhos e declara ações locais; mantém os formulários acessíveis."""
    def annotate_link(match):
        tag = match[0]
        href = re.search(r'href="([^"]+)"', tag)
        if not href:
            return tag
        path = urlsplit(unescape(href[1])).path
        kind, identity = None, ""
        if path in {"/garagem/novo", "/auth/cadastro"}:
            kind = "car"
        elif re.fullmatch(r"/garagem/\d+/editar", path):
            kind, identity = "edit", path.split("/")[2]
        elif re.fullmatch(r"/estatisticas/\d+", path):
            kind, identity = "evolution", path.split("/")[2]
        elif path == "/perfil/editar":
            kind = "profile"
        if kind:
            return tag[:-1] + f' data-preview-open="{kind}" data-preview-id="{identity}">'
        if path == "/auth/login":
            return tag[:-1] + ' data-enter-visitor>'
        return tag
    source = re.sub(r"<a\b[^>]*>", annotate_link, source)
    source = re.sub(r'<meta name="csrf-token"[^>]*>', "", source)
    source = re.sub(r'<input[^>]*name="csrf_token"[^>]*>', "", source)
    def annotate_form(match):
        tag = match[0]
        if not re.search(r'method="post"', tag, re.I):
            return tag
        action = re.search(r'action="([^"]+)"', tag)
        original = unescape(action[1]) if action else ""
        tag = re.sub(r'method="post"', 'method="get"', tag, flags=re.I)
        tag = re.sub(r'action="[^"]*"', 'action="#"', tag)
        return tag[:-1] + f' data-preview-action="{escape(original, quote=True)}">'
    source = re.sub(r"<form\b[^>]*>", annotate_form, source)
    def replace_url(match):
        attribute, quote, value = match.groups()
        decoded = unescape(value)
        parsed = urlsplit(decoded)
        path = parsed.path
        if path.startswith("/static/"):
            value = path[1:]
        elif path.startswith("/uploads/"):
            value = "uploads/" + uploads[Path(path).name]
        elif path in routes and (not parsed.scheme or parsed.hostname == "localhost"):
            value = routes[path] + ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")
        elif decoded.startswith("/") and not decoded.startswith("//"):
            if re.fullmatch(r"/garagem/\d+/editar", path):
                value = f"carro-{path.split('/')[2]}.html"
            elif re.fullmatch(r"/estatisticas/\d+", path):
                value = f"carro-{path.split('/')[2]}.html#metric-change"
            else:
                value = "garagem.html"
        return f"{attribute}={quote}{escape(value, quote=True)}{quote}"
    source = re.sub(r'''(?<![\w-])(href|src|action|data-gallery-src)\s*=\s*(["'])(.*?)\2''', replace_url, source, flags=re.DOTALL)
    source = re.sub(r'(<main\b[^>]*>)', r'\1' + BANNER, source, count=1)
    source = re.sub(r'(<a[^>]*data-enter-visitor[^>]*>).*?(</a>)', r'\1Entrar como visitante\2', source, flags=re.DOTALL)
    source = source.replace('aria-label="Sair"', 'aria-label="Sair da demonstração"')
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    source = source.replace("</head>", f'<script id="demo-data" type="application/json">{payload}</script><script src="static/js/preview.js" defer></script></head>')
    canonical = SITE_URL + "/" + ("" if destination == "index.html" else destination)
    source = re.sub(r'(<link rel="canonical" href=")[^"]*(")', lambda match: match[1] + canonical + match[2], source)
    source = re.sub(r'(<meta property="og:url" content=")[^"]*(")', lambda match: match[1] + canonical + match[2], source)
    source = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*(")', lambda match: match[1] + SITE_URL + "/static/img/social-card.png" + match[2], source)
    return source


def build():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    shutil.copytree(ROOT / "app" / "static", OUTPUT / "static")
    (OUTPUT / ".nojekyll").touch()
    with tempfile.TemporaryDirectory(prefix="garagehub-pages-") as temporary:
        upload_dir = Path(temporary) / "uploads"
        app = create_app({"TESTING": True, "PREVIEW_MODE": True,
            "SECRET_KEY": "chave-da-exportacao-apenas-dados-ficticios",
            "SQLALCHEMY_DATABASE_URI": "sqlite://", "UPLOAD_FOLDER": str(upload_dir)})
        with app.app_context():
            seed_database()
            users = list(db.session.scalars(db.select(User).order_by(User.id)))
            cars = list(db.session.scalars(db.select(Vehicle).order_by(Vehicle.id)))
            routes = {"/": "index.html", "/feed": "feed.html", "/amigos": "amigos.html",
                      "/garagem/": "garagem.html", "/garagem": "garagem.html",
                      "/perfil": "perfil-lucas_gti.html", "/perfil/editar": "perfil-lucas_gti.html",
                      "/auth/login": "acesso.html", "/auth/cadastro": "garagem.html", "/garagem/novo": "garagem.html"}
            routes.update({f"/u/{user.username}": f"perfil-{user.username}.html" for user in users})
            routes.update({f"/garagem/{car.id}": f"carro-{car.id}.html" for car in cars})
            uploads = {}
            (OUTPUT / "uploads").mkdir()
            for file in sorted(upload_dir.iterdir()):
                name = f"demo-{sha256(file.read_bytes()).hexdigest()[:12]}{file.suffix}"
                shutil.copyfile(file, OUTPUT / "uploads" / name)
                uploads[file.name] = name
            following = list(db.session.scalars(db.select(Follow.followed_id).where(Follow.follower_id == users[0].id)))
            friends = list(db.session.scalars(db.select(Friendship)))
            utc = lambda value: value.replace(tzinfo=timezone.utc).isoformat()
            data = {"version": 1, "exportedAt": datetime.now(timezone.utc).isoformat(), "demoUserId": users[0].id,
                "following": following, "friendships": {str(link.other_id(users[0].id)): link.status for link in friends if users[0].id in (link.user_low_id,link.user_high_id)},
                "users": [{"id":user.id,"username":user.username,"city":user.city,"bio":user.bio,
                           "followers":db.session.scalar(db.select(db.func.count()).select_from(Follow).where(Follow.followed_id==user.id,Follow.follower_id!=users[0].id))} for user in users],
                "cars": [{"id":car.id,"userId":car.user_id,"brand":car.brand,"model":car.model,"year":car.year,"color":car.color,
                    "engine":car.engine,"transmission":car.transmission,"description":car.description,"photo":"uploads/"+uploads[car.photos[0].filename],
                    "viewerConfig":car.viewer_config,"defaults":car.viewer_config,
                    "stats":[{"id":item.id,"date":item.date.isoformat(),**{metric:getattr(item,metric) for metric in ["power","torque","zero_to_hundred","top_speed","consumption"]}} for item in car.stats],
                    "modifications":[{"id":item.id,"name":item.name,"category":item.category,"date":item.date.isoformat(),"value":float(item.value)} for item in car.modifications]} for car in cars],
                "posts":[{"id":post.id,"userId":post.user_id,"text":post.text,"createdAt":utc(post.created_at),"photo":"uploads/"+uploads[post.photo] if post.photo else None,
                    "likes":[like.user_id for like in post.likes],"comments":[{"id":comment.id,"userId":comment.user_id,"text":comment.text,"createdAt":utc(comment.created_at)} for comment in post.comments]} for post in db.session.scalars(db.select(Post).order_by(Post.created_at.desc()))]}
            demo_id = str(users[0].id)
        client = app.test_client()
        homepage = client.get("/")
        assert homepage.status_code == 200
        (OUTPUT / "index.html").write_text(export_html(homepage.text,routes,uploads,data,"index.html"),encoding="utf-8")
        with client.session_transaction() as session:
            session["_user_id"] = demo_id
            session["_fresh"] = True
        exported = {"index.html"}
        for route,destination in routes.items():
            if destination in exported or route in {"/perfil","/perfil/editar","/auth/login","/auth/cadastro","/garagem/novo"}:
                continue
            response = client.get(route + ("?filter=all" if route=="/feed" else ""))
            if response.status_code != 200:
                raise RuntimeError(f"Falha na exportação: {route} HTTP {response.status_code}")
            (OUTPUT / destination).write_text(export_html(response.text,routes,uploads,data,destination),encoding="utf-8")
            exported.add(destination)
        with app.test_request_context("/"):
            about = render_template_string('''{% extends 'base.html' %}{% block content %}
            <section class="panel empty-state"><span class="eyebrow">CONHEÇA O GARAGEHUB</span><h1>Entre como visitante.</h1>
            <p>Explore o perfil de Lucas, nove carros e a comunidade. Você pode adicionar projetos, registrar medições, publicar fotos e experimentar o Garage Studio.</p>
            <p>Os dados de exemplo e suas alterações ficam apenas neste navegador. Esta demonstração não cria uma conta real.</p>
            <div class="actions"><a class="btn btn-primary" href="/auth/login">Entrar como visitante</a><a class="btn btn-secondary" href="/garagem/novo">Adicionar veículo</a></div></section>
            {% endblock %}''',title="Demonstração interativa",meta_description="Teste o GarageHub como visitante: garagem, evolução, publicações e visualização 3D com dados salvos apenas no seu navegador.")
        (OUTPUT / "acesso.html").write_text(export_html(about,routes,uploads,data,"acesso.html"),encoding="utf-8")
        prototype = client.get("/garagem/1").text
        prototype = prototype.replace("<title>Volkswagen Golf GTI · GarageHub</title>","<title>Projeto local · GarageHub</title>")
        prototype = prototype.replace("Conheça o projeto Volkswagen Golf GTI 2018 de lucas_gti: histórico de evolução, modificações e Garage Studio 3D.","Projeto de demonstração criado neste navegador: garagem, medições e configuração 3D local.")
        prototype = prototype.replace('content="Volkswagen Golf GTI · GarageHub"','content="Projeto local · GarageHub"')
        (OUTPUT / "carro.html").write_text(export_html(prototype,routes,uploads,data,"carro.html"),encoding="utf-8")
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
    pages = sorted(path.name for path in OUTPUT.glob("*.html") if path.name != "carro.html")
    (OUTPUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"".join(f"<url><loc>{SITE_URL}/{name if name!='index.html' else ''}</loc></url>" for name in pages)+"</urlset>",encoding="utf-8")
    (OUTPUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    print(f"V0.1 exportada: {len(list(OUTPUT.glob('*.html')))} páginas em {OUTPUT}")


if __name__ == "__main__":
    build()
