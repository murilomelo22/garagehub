"""Testa a prévia sob /garagehub/, com armazenamento real e dados descartáveis."""

from datetime import date, timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import os
import shutil
import sys
import tempfile
import threading
import urllib.request
from PIL import Image
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
KEY = "garagehub:preview:v0.2"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run():
    with tempfile.TemporaryDirectory(prefix="garagehub-pages-test-") as temporary:
        Path(temporary,"garagehub").symlink_to(ROOT / "docs",target_is_directory=True)
        server = ThreadingHTTPServer(("127.0.0.1",0),partial(QuietHandler,directory=temporary))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}/garagehub/"
        cache = {}
        def cdn(route):
            url = route.request.url
            if url not in cache:
                with urllib.request.urlopen(url,timeout=40) as response:
                    cache[url] = response.read()
            route.fulfill(status=200,body=cache[url],content_type="application/javascript",headers={"Access-Control-Allow-Origin":"*"})
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=os.getenv("BROWSER_PATH") or shutil.which("chromium") or shutil.which("google-chrome"),args=["--no-sandbox","--disable-dev-shm-usage","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
                context=browser.new_context(viewport={"width":1280,"height":900},locale="pt-BR",accept_downloads=True)
                context.route("https://cdn.jsdelivr.net/**",cdn)
                page=context.new_page(); page.set_default_timeout(15000)
                def visit(url):
                    response=page.goto(url)
                    page.evaluate("() => window.GaragePreviewReady")
                    return response
                errors=[]; requests=[]
                page.on("pageerror",lambda error: errors.append(str(error)))
                page.on("request",lambda request: requests.append(request.url) if request.method=="POST" else None)
                assert visit(base).status==200
                # Acesso explícito e fallback sem JavaScript não podem voltar à própria página.
                no_js=browser.new_context(java_script_enabled=False)
                fallback=no_js.new_page();fallback.goto(base+"acesso.html")
                link=fallback.locator("main [data-enter-visitor]");assert link.get_attribute("href")=="feed.html"
                link.click();assert fallback.url.endswith("feed.html");no_js.close()
                visit(base+"acesso.html");page.locator("main [data-enter-visitor]").click()
                page.wait_for_url("**/feed.html")
                expect(page.locator(".post")).to_have_count(24)
                assert "lucas_gti" in page.locator(".preview-banner").inner_text()
                # Publicação com imagem e comentário ficam preservados após recarregar.
                stream=BytesIO();Image.new("RGB",(180,120),"navy").save(stream,"PNG")
                page.locator("#post-text").fill("Meu projeto de teste <script>window.injetado=true</script>")
                page.locator(".composer [name=photo]").set_input_files({"name":"teste.png","mimeType":"image/png","buffer":stream.getvalue()})
                page.locator(".composer").get_by_role("button",name="Publicar").click()
                expect(page.locator(".post")).to_have_count(25)
                post=page.locator(".post").first
                assert post.locator(".post-photo").get_attribute("src").startswith("data:image/jpeg")
                post.locator("[data-like]").click()
                assert post.locator("[data-like]").get_attribute("aria-pressed")=="true"
                post.locator(".comment-form input").fill("Ficou ótimo! <img src=x onerror=window.injetado=true>")
                post.locator(".comment-form button").click()
                assert "1 comentários" in post.locator("[data-comment-focus]").inner_text()
                page.reload()
                expect(page.locator(".post")).to_have_count(25)
                assert page.locator(".post").first.locator("[data-like]").get_attribute("aria-pressed")=="true"
                assert page.evaluate("window.injetado === undefined")
                # Escape fecha o diálogo e devolve o foco ao acionador.
                opener=page.get_by_role("link",name="Novo projeto")
                opener.click();assert page.locator("dialog").is_visible()
                page.keyboard.press("Escape");expect(page.locator("dialog")).to_be_hidden()
                assert opener.evaluate("element => element === document.activeElement")
                opener.click()
                dialog=page.locator("dialog")
                dialog.get_by_role("button",name="Salvar veículo",exact=True).click()
                expect(dialog.locator(".form-error")).to_contain_text("preencha")
                assert dialog.locator('[aria-invalid="true"]').count()==1
                dialog.get_by_label("Marca *",exact=True).fill("Honda")
                dialog.get_by_label("Modelo *",exact=True).fill("Civic de teste")
                dialog.get_by_label("Ano *",exact=True).fill("2018")
                dialog.get_by_label("Descrição",exact=True).fill("Projeto local <script>window.injetado=true</script>")
                dialog.locator('[name="photo"]').set_input_files({"name":"grande.jpg","mimeType":"image/jpeg","buffer":b"x"*(7*1024*1024)})
                dialog.get_by_role("button",name="Salvar veículo",exact=True).click()
                expect(dialog.locator(".form-error")).to_contain_text("até 6 MB")
                dialog.locator('[name="photo"]').set_input_files([])
                dialog.get_by_role("button",name="Salvar veículo",exact=True).click()
                expect(page.locator("dialog")).to_be_hidden()
                visit(base+"garagem.html")
                assert page.locator(".car-card").count()==4
                page.reload();page.evaluate("() => window.GaragePreviewReady");assert page.locator(".car-card").count()==4
                page.locator(".car-card").filter(has_text="Civic de teste").click()
                page.wait_for_url("**/carro.html?id=local-*")
                page.locator("#activate-viewer").click()
                page.wait_for_selector('#car-viewer[data-ready="true"]',timeout=60000)
                assert page.locator("h1").inner_text()=="Civic de teste"
                assert page.evaluate("window.injetado === undefined")
                page.get_by_role("link",name="Editar carro").click()
                dialog.get_by_label("Modelo *",exact=True).fill("Civic projeto V0.2")
                dialog.get_by_role("button",name="Salvar veículo",exact=True).click()
                page.wait_for_load_state("networkidle");page.evaluate("() => window.GaragePreviewReady")
                assert page.locator("h1").inner_text()=="Civic projeto V0.2"
                brazil_today=date.fromisoformat(page.evaluate("GarageHub.day(new Date())"))
                for days,power in [(30,"180"),(0,"210")]:
                    page.get_by_role("link",name="Registrar evolução").click()
                    dialog.get_by_label("Data *",exact=True).fill((brazil_today-timedelta(days=days)).isoformat())
                    dialog.get_by_label("Potência (cv) *",exact=True).fill(power)
                    dialog.get_by_label("Torque (Nm)",exact=True).fill("260")
                    dialog.get_by_label("0–100 km/h (s)",exact=True).fill("7.2")
                    dialog.get_by_label("Consumo (km/l)",exact=True).fill("11.4")
                    dialog.get_by_role("button",name="Salvar medição",exact=True).click()
                    if dialog.is_visible() and not dialog.locator(".form-error").is_hidden(): print("Validação:",dialog.locator(".form-error").inner_text(),flush=True)
                    expect(dialog).to_be_hidden()
                assert "+30 cv" in page.locator("#metric-change").inner_text()
                page.get_by_label("Métrica",exact=True).select_option("consumption")
                assert "km/l" in page.locator("#metric-change").inner_text()
                page.get_by_role("link",name="Registrar evolução").click()
                dialog.get_by_role("button",name="Adicionar modificação",exact=True).click()
                dialog.get_by_label("Nome *",exact=True).fill("Pneus novos")
                dialog.get_by_label("Valor (R$) *",exact=True).fill("R$ 2.500,00")
                dialog.get_by_role("button",name="Salvar modificação",exact=True).click()
                assert "2.500,00" in page.locator("[data-modifications]").inner_text()
                page.locator('[name="paint_color"]').fill("#1255aa")
                page.locator('[name="wheel_size"]').fill("1.25")
                page.locator('[name="suspension"]').select_option("lowered")
                page.get_by_role("button",name="Salvar configuração").click()
                assert "navegador" in page.locator("#viewer-feedback").inner_text()
                page.reload();page.locator("#activate-viewer").click()
                page.wait_for_selector('#car-viewer[data-ready="true"]',timeout=60000)
                assert page.locator('[name="paint_color"]').input_value()=="#1255aa"
                assert page.locator('[name="wheel_size"]').input_value()=="1.25"
                page.get_by_role("button",name="Redefinir",exact=True).click()
                assert page.locator('[name="paint_color"]').input_value()=="#244f91"
                assert page.locator('[name="wheel_size"]').input_value()=="1"
                with page.expect_download() as pending:
                    page.get_by_role("button",name="Exportar imagem PNG",exact=True).click()
                download=pending.value
                image_path=Path(temporary)/"modelo.png";download.save_as(image_path)
                with Image.open(image_path) as image:
                    assert image.width>100 and image.height>100
                    assert len(image.getcolors(image.width*image.height))>100
                visit(base+"amigos.html?q=GT86")
                assert page.locator(".person-card").count()==1
                visit(base+"amigos.html?q=inexistente")
                assert page.get_by_role("heading",name="Nenhuma garagem encontrada.").is_visible()
                page.get_by_role("button",name="Limpar filtros").click()
                assert page.locator(".person-card").count()==11
                pedro=page.locator(".person-card").filter(has_text="pedro_rs")
                pedro.get_by_role("button",name="Seguir",exact=True).click()
                assert pedro.get_by_role("button",name="Seguindo",exact=True).is_visible()
                page.reload();page.evaluate("() => window.GaragePreviewReady");assert pedro.get_by_role("button",name="Seguindo",exact=True).is_visible()
                visit(base+"feed.html?filter=following&brand=Ford")
                assert page.locator(".post").count()==2
                # Quota indisponível não pode alterar o estado nem mostrar um falso sucesso.
                before=page.evaluate("key => localStorage.getItem(key)",KEY)
                page.evaluate("() => { window.originalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new DOMException('Quota','QuotaExceededError')}; }")
                page.locator("[data-like]").first.click()
                assert "não conseguiu salvar" in page.locator(".local-toast").inner_text()
                assert page.evaluate("key => localStorage.getItem(key)",KEY)==before
                page.evaluate("() => { Storage.prototype.setItem=window.originalSetItem; }")
                # Restauração remove apenas alterações da prévia, sem apagar outros dados da origem.
                page.evaluate("localStorage.setItem('outro-aplicativo','preservar')")
                page.once("dialog",lambda dialog:dialog.accept())
                page.locator("[data-restore-demo]").click();page.wait_for_load_state("networkidle");page.evaluate("() => window.GaragePreviewReady")
                stored=page.evaluate("key=>JSON.parse(localStorage.getItem(key))",KEY)
                assert len(stored["cars"])==36 and len(stored["posts"])==24
                assert page.evaluate("localStorage.getItem('outro-aplicativo')")=="preservar"
                expect(page.locator("[data-visitor-status]")).to_contain_text("Você está como visitante")
                # Toda página gerada é exercitada nos três tamanhos solicitados.
                for width,height in [(360,800),(768,1024),(1280,900)]:
                    page.set_viewport_size({"width":width,"height":height})
                    for path in sorted((ROOT/"docs").glob("*.html")):
                        visit(base+path.name)
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"),f"Rolagem horizontal: {path.name} ({width}px)"
                        profile=page.locator('.sidebar nav a').last
                        assert profile.get_attribute("href")=="perfil-lucas_gti.html"
                    print(f"Todas as páginas verificadas em {width}px.",flush=True)
                # Captura real da identidade visual para Open Graph e Twitter.
                page.set_viewport_size({"width":1200,"height":630})
                visit(base)
                page.screenshot(path=str(ROOT/"app/static/img/social-card.png"))
                page.set_viewport_size({"width":360,"height":800})
                visit(base+"feed.html")
                screenshots=Path(os.getenv("SCREENSHOT_DIR",str(Path(tempfile.gettempdir())/"garagehub-screenshots")))
                screenshots.mkdir(exist_ok=True,parents=True)
                page.screenshot(path=str(screenshots/"v02-preview-360.png"),full_page=True)
                assert not errors,errors
                assert not requests,requests
                browser.close()
                print("Prévia OK: modais, persistência, fotos, segurança de texto, interações, filtros, gráficos, 3D, PNG e três tamanhos.")
        finally:
            server.shutdown();server.server_close()


if __name__=="__main__":
    run()
