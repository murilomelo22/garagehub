"""Exporta uma prévia pública para GitHub Pages usando apenas dados fictícios.

Não abre o banco real nem publica contas, sessões ou fotos de usuários.
"""

from html import escape, unescape
from hashlib import sha256
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import render_template_string
from app import create_app
from app.extensions import db
from app.models import User, Vehicle
from app.seed import seed_database

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
BANNER = (
    '<aside class="preview-banner" aria-label="Sobre esta prévia">'
    '<strong>PRÉVIA · DADOS DE EXEMPLO</strong>'
    '<span>Explore a comunidade e os carros. Contas e alterações não estão disponíveis aqui.</span>'
    '<a href="acesso.html">Saiba mais</a></aside>'
)


def export_html(source, routes, uploads, search_index):
    def replace_url(match):
        attribute, quote, value = match.groups()
        decoded = unescape(value)
        path = urlsplit(decoded).path
        if path.startswith("/static/"):
            value = path[1:]
        elif path.startswith("/uploads/"):
            value = "uploads/" + uploads[Path(path).name]
        elif decoded.startswith("/"):
            value = routes.get(path, "acesso.html")
        return f"{attribute}={quote}{escape(value, quote=True)}{quote}"

    source = re.sub(
        r'''(href|src|action|data-gallery-src)\s*=\s*(["'])(.*?)\2''',
        replace_url,
        source,
        flags=re.DOTALL,
    )
    source = re.sub(r'<meta name="csrf-token"[^>]*>', "", source)
    source = re.sub(r'<input[^>]*name="csrf_token"[^>]*>', "", source)

    def read_only_form(match):
        opening, body = match.groups()
        if 'id="viewer-form"' in opening:
            opening = re.sub(r'method="post"', 'method="get"', opening)
            opening = re.sub(r'action="[^"]*"', 'action="#"', opening)
            body = re.sub(
                r'<button[^>]*id="save-viewer"[^>]*>.*?</button>',
                '<button id="save-viewer" class="btn btn-secondary full" disabled>Prévia sem salvamento</button>',
                body,
                flags=re.DOTALL,
            )
            return opening[:-1] + ' data-preview onsubmit="return false">' + body + "</form>"
        if 'method="post"' in opening.lower():
            return ""
        return opening + body + "</form>"

    source = re.sub(r'(<form\b[^>]*>)(.*?)</form>', read_only_form, source, flags=re.DOTALL)
    source = re.sub(r'(<main\b[^>]*>)', r'\1' + BANNER, source, count=1)
    source = source.replace(
        "</head>", '<link rel="stylesheet" href="static/css/preview.css"></head>'
    ).replace(
        "</body>", '<script src="static/js/preview.js" defer></script></body>'
    )
    source = source.replace("Começar minha garagem", "Explorar garagem")
    source = source.replace("Já tenho conta", "Ver comunidade")
    source = source.replace("Minha garagem", "Garagem de exemplo")
    source = source.replace('href="acesso.html">Explorar garagem', 'href="garagem.html">Explorar garagem')
    source = source.replace('href="acesso.html">Ver comunidade', 'href="feed.html">Ver comunidade')
    for username, searchable in search_index.items():
        pattern = r'(<article class="panel person-card")(>.*?<h3>' + re.escape(username) + r'</h3>)'
        source = re.sub(
            pattern,
            lambda m: m[1] + ' data-search="' + escape(searchable, quote=True) + '"' + m[2],
            source,
            flags=re.DOTALL,
        )
    return source


def build():
    # Limpa somente a pasta de saída dedicada. A aplicação real fica intacta.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    shutil.copytree(ROOT / "app" / "static", OUTPUT / "static")
    (OUTPUT / ".nojekyll").touch()
    with tempfile.TemporaryDirectory(prefix="garagehub-pages-") as temporary:
        upload_dir = Path(temporary) / "uploads"
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "chave-da-exportacao-apenas-dados-ficticios",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "UPLOAD_FOLDER": str(upload_dir),
            }
        )
        with app.app_context():
            seed_database()
            users = list(db.session.scalars(db.select(User).order_by(User.id)))
            cars = list(db.session.scalars(db.select(Vehicle).order_by(Vehicle.id)))
            demo_user = users[0]
            routes = {
                "/": "index.html", "/feed": "feed.html", "/amigos": "amigos.html",
                "/garagem/": "garagem.html", "/garagem": "garagem.html",
            }
            routes.update({f"/u/{user.username}": f"perfil-{user.username}.html" for user in users})
            routes.update({f"/garagem/{car.id}": f"carro-{car.id}.html" for car in cars})
            search_index = {
                user.username: " ".join([user.username, user.city or "", user.bio or ""] + [
                    f"{car.brand} {car.model}" for car in user.vehicles
                ]) for user in users
            }
            demo_id = str(demo_user.id)
            uploads = {}
            (OUTPUT / "uploads").mkdir()
            for file in sorted(upload_dir.iterdir()):
                name = f"demo-{sha256(file.read_bytes()).hexdigest()[:12]}{file.suffix}"
                shutil.copyfile(file, OUTPUT / "uploads" / name)
                uploads[file.name] = name

        client = app.test_client()
        homepage = client.get("/")
        assert homepage.status_code == 200
        (OUTPUT / "index.html").write_text(export_html(homepage.text, routes, uploads, search_index))
        with client.session_transaction() as session:
            session["_user_id"] = demo_id
            session["_fresh"] = True
        for route, destination in routes.items():
            if destination == "index.html" or route == "/garagem":
                continue
            response = client.get(route)
            if response.status_code != 200:
                raise RuntimeError(f"Falha na exportação: {route} HTTP {response.status_code}")
            (OUTPUT / destination).write_text(export_html(response.text, routes, uploads, search_index))
        with app.test_request_context("/"):
            about = render_template_string(
                """{% extends 'base.html' %}{% block content %}
                <section class="panel empty-state"><span class="eyebrow">CONHEÇA O GARAGEHUB</span>
                <h1>Você está na prévia.</h1>
                <p>Os perfis, carros e publicações são exemplos. Você pode navegar pela comunidade,
                ver os projetos e experimentar o visualizador 3D.</p>
                <p>Cadastro, login, publicações e salvamento de alterações estarão disponíveis
                na versão completa. Nenhum dado pessoal é solicitado nesta prévia.</p>
                <div class="actions"><a class="btn btn-primary" href="/garagem/">Explorar garagem</a>
                <a class="btn btn-secondary" href="/feed">Ver comunidade</a></div></section>
                {% endblock %}""", title="Conheça a prévia"
            )
        (OUTPUT / "acesso.html").write_text(export_html(about, routes, uploads, search_index))
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

    (OUTPUT / "static" / "css" / "preview.css").write_text(
        ".preview-banner{display:flex;gap:12px;align-items:center;flex-wrap:wrap;"
        "padding:14px 18px;margin-bottom:24px;border:1px solid #493126;border-radius:12px;"
        "background:#211b18;color:#cfc5bf;font-size:13px}"
        ".preview-banner strong{color:#ff7049;font-size:11px;letter-spacing:.08em}"
        ".preview-banner a{color:#ff7049;margin-left:auto}"
        "[hidden]{display:none!important}.preview-empty{margin-top:20px;color:#aca5a2}"
    )
    (OUTPUT / "static" / "js" / "preview.js").write_text(
        """document.addEventListener('submit', event => {
          const form = event.target;
          if (form.matches('[data-preview]')) {
            event.preventDefault(); event.stopImmediatePropagation(); return;
          }
          if (form.querySelector('[name="q"]')) {
            event.preventDefault();
            const query = form.querySelector('[name="q"]').value;
            location.href = 'amigos.html?q=' + encodeURIComponent(query);
          }
        }, true);
        const query = new URLSearchParams(location.search).get('q') || '';
        const normalize = value => value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
        document.querySelectorAll('[name="q"]').forEach(input => { input.value = query; });
        const cards = [...document.querySelectorAll('.person-card')];
        if (cards.length && query) {
          cards.forEach(card => { card.hidden = !normalize(card.dataset.search || card.textContent).includes(normalize(query)); });
          if (cards.every(card => card.hidden)) {
            const empty = document.createElement('p'); empty.className = 'preview-empty';
            empty.textContent = 'Nenhuma garagem de exemplo encontrada. Tente outro nome, cidade ou carro.';
            document.querySelector('.people-grid').append(empty);
          }
        }
        """
    )
    print(f"Prévia exportada: {len(list(OUTPUT.glob('*.html')))} páginas em {OUTPUT}")


if __name__ == "__main__":
    build()
