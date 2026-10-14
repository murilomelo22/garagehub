"""Validação em desktop e celular com banco e uploads descartáveis.

Os arquivos CDN são obtidos por HTTPS com verificação TLS pela rede do Python.
"""

import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import urllib.request
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server, WSGIRequestHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.seed import seed_database


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def run():
    with tempfile.TemporaryDirectory(prefix="garagehub-browser-") as directory:
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "chave-do-teste-de-navegador",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "UPLOAD_FOLDER": str(Path(directory) / "uploads"),
            }
        )
        with app.app_context():
            seed_database()
        server = make_server("127.0.0.1", 0, app, request_handler=QuietHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}"
        cdn_cache = {}

        def cdn_route(route):
            url = route.request.url
            if url not in cdn_cache:
                with urllib.request.urlopen(url, timeout=40) as response:
                    cdn_cache[url] = response.read()
            route.fulfill(
                status=200,
                body=cdn_cache[url],
                content_type="application/javascript",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        try:
            with sync_playwright() as playwright:
                browser_path = (
                    os.getenv("BROWSER_PATH")
                    or shutil.which("chromium")
                    or shutil.which("google-chrome")
                )
                browser = playwright.chromium.launch(
                    executable_path=browser_path,
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--use-angle=swiftshader",
                        "--enable-unsafe-swiftshader",
                    ],
                )
                context = browser.new_context(
                    viewport={"width": 1440, "height": 1000}, locale="pt-BR"
                )
                context.route("https://cdn.jsdelivr.net/**", cdn_route)
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                assert page.goto(base).status == 200
                assert page.get_by_role(
                    "heading", name="Sua paixão merece uma garagem."
                ).is_visible()
                page.goto(base + "/auth/login")
                page.get_by_label("Usuário ou e-mail").fill("lucas_gti")
                page.get_by_label("Senha", exact=True).fill("GarageHub123!")
                page.get_by_role("button", name="Entrar na GarageHub").click()
                page.wait_for_url("**/feed")
                assert page.locator(".post").count() == 4
                page.locator("#post-text").fill(
                    "Post publicado pelo teste de navegador."
                )
                page.get_by_role("button", name="Publicar", exact=True).click()
                page.wait_for_url("**/feed")
                assert page.locator(".post").count() == 5
                page.locator(".post").first.get_by_role(
                    "button", name="Curtir post", exact=True
                ).click()
                assert (
                    page.locator(".post").first.locator(".reaction.liked").count() == 1
                )
                page.goto(base + "/garagem/")
                assert page.locator(".car-card").count() == 3
                page.locator(".car-card").last.click()
                page.wait_for_selector('#car-viewer[data-ready="true"]', timeout=60000)
                page.wait_for_function(
                    "typeof Chart !== 'undefined' && Chart.getChart(document.getElementById('power-chart')) !== undefined"
                )
                assert page.locator("#viewer-message").is_hidden()
                # A rotação deve mudar os pixels efetivamente desenhados.
                canvas = page.locator("#car-viewer canvas")
                before = canvas.screenshot()
                rect = canvas.bounding_box()
                page.mouse.move(
                    rect["x"] + rect["width"] * 0.5, rect["y"] + rect["height"] * 0.5
                )
                page.mouse.down()
                page.mouse.move(
                    rect["x"] + rect["width"] * 0.75,
                    rect["y"] + rect["height"] * 0.55,
                    steps=15,
                )
                page.mouse.up()
                assert (
                    before != canvas.screenshot()
                ), "OrbitControls deve alterar a cena."
                page.locator('input[name="paint_color"]').fill("#1255aa")
                page.locator('input[name="wheel_color"]').fill("#eeeeee")
                page.locator('input[name="wheel_size"]').fill("1.25")
                page.locator('select[name="suspension"]').select_option("lowered")
                page.locator('select[name="spoiler"]').select_option("yes")
                page.get_by_role("button", name="Salvar configuração").click()
                page.wait_for_function(
                    "document.getElementById('viewer-feedback').textContent.includes('Visual salvo')"
                )
                page.reload()
                page.wait_for_selector('#car-viewer[data-ready="true"]', timeout=60000)
                assert (
                    page.locator('input[name="paint_color"]').input_value() == "#1255aa"
                )
                assert page.locator('input[name="wheel_size"]').input_value() == "1.25"
                assert page.locator('select[name="spoiler"]').input_value() == "yes"
                assert (
                    page.locator('select[name="suspension"]').input_value() == "lowered"
                )
                assert not errors, errors
                screenshots = Path(
                    os.getenv(
                        "SCREENSHOT_DIR",
                        str(Path(tempfile.gettempdir()) / "garagehub-screenshots"),
                    )
                )
                screenshots.mkdir(parents=True, exist_ok=True)
                page.screenshot(
                    path=str(screenshots / "car-desktop.png"), full_page=True
                )
                page.goto(base + "/feed")
                page.screenshot(
                    path=str(screenshots / "feed-desktop.png"), full_page=True
                )
                page.goto(base + "/amigos?q=Curitiba")
                assert page.locator(".person-card").count() == 1
                assert page.locator(".person-card h3").inner_text() == "ana_silva"
                for width, height in [(360, 800), (768, 1024), (1280, 900)]:
                    page.set_viewport_size({"width": width, "height": height})
                    for path in [
                        "/feed",
                        "/garagem/",
                        "/garagem/1",
                        "/amigos",
                        "/u/lucas_gti",
                        "/garagem/novo",
                        "/estatisticas/1",
                    ]:
                        page.goto(base + path)
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= innerWidth"
                        ), f"Overflow em {path} ({width}px)"
                    page.goto(base + "/feed")
                    page.screenshot(
                        path=str(screenshots / f"feed-mobile-{width}.png"),
                        full_page=True,
                    )
                assert not errors, errors
                browser.close()
                print(
                    "Navegador OK: login, post, curtida, busca, Chart.js, Three.js, rotação, persistência 3D e 7 telas em 360/768/1280 px."
                )
                print(f"Capturas: {screenshots}")
                print(f"Arquivos CDN verificados por HTTPS: {len(cdn_cache)}")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    run()
