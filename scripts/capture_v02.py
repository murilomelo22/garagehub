"""Captura home e Studio nas três larguras e valida controles, PNG e proporções."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import shutil
import threading
import urllib.request
from playwright.sync_api import expect, sync_playwright

ROOT=Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


def run():
    output=ROOT/"reports/screenshots";output.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(QuietHandler,directory=ROOT/"docs"))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f"http://127.0.0.1:{server.server_port}/"
    cache={};checks=[]
    def cdn(route):
        if route.request.url not in cache:
            with urllib.request.urlopen(route.request.url,timeout=40) as response: cache[route.request.url]=response.read()
        route.fulfill(body=cache[route.request.url],content_type="application/javascript",headers={"Access-Control-Allow-Origin":"*"})
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which("chromium"),args=["--no-sandbox","--disable-dev-shm-usage","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
            for width,height in [(360,800),(768,1024),(1280,900)]:
                context=browser.new_context(viewport={"width":width,"height":height},locale="pt-BR",accept_downloads=True)
                context.route("https://cdn.jsdelivr.net/**",cdn);page=context.new_page();errors=[]
                page.on("pageerror",lambda error:errors.append(str(error)))
                page.goto(base);page.evaluate("() => window.GaragePreviewReady")
                expect(page.locator('#power-chart[data-ready="true"]')).to_be_visible()
                assert page.locator("[data-enter-visitor]").count()==2
                assert page.locator(".hero-copy [data-enter-visitor]").inner_text().strip().startswith("Começar minha garagem")
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                image=page.locator(".studio-poster").bounding_box();assert abs(image['width']/image['height']-1000/420)<.01
                page.screenshot(path=str(output/f"home-{width}.png"),full_page=True)
                page.get_by_label("Métrica",exact=True).select_option("torque");expect(page.locator("#metric-change")).to_contain_text("Nm")
                page.locator(".chart-point").last.focus();expect(page.locator(".chart-tooltip")).to_be_visible()
                page.locator("#activate-viewer").click();page.wait_for_selector('#car-viewer[data-ready="true"]',timeout=60000)
                assert page.locator('[name="paint_color"]').input_value()=="#c94432"
                # Verifica o intervalo de rodas e suspensões sem esticar o contêiner.
                page.locator('[name="wheel_size"]').fill("1.3");page.locator('[name="suspension"]').select_option("lowered")
                page.locator('[name="spoiler"]').select_option("yes")
                page.get_by_role("button",name="Girar carro para a direita").click()
                page.locator("#visualizador").screenshot(path=str(output/f"studio-{width}.png"))
                page.get_by_role("button",name="Redefinir",exact=True).click()
                page.locator('[name="paint_color"]').fill("#1255aa");page.get_by_role("button",name="Salvar configuração").click()
                expect(page.locator("#viewer-feedback")).to_contain_text("navegador")
                page.reload();page.evaluate("() => window.GaragePreviewReady")
                expect(page.locator('[name="paint_color"]')).to_have_value("#1255aa")
                # Excluir o Golf na garagem não pode retirar o produto da home.
                page.evaluate("""() => {const key='garagehub:preview:v0.2',state=JSON.parse(localStorage.getItem(key));state.cars=state.cars.filter(car=>car.id!==1);localStorage.setItem(key,JSON.stringify(state));}""")
                page.reload();page.evaluate("() => window.GaragePreviewReady")
                expect(page.locator("h1")).to_contain_text("Seu projeto merece")
                expect(page.locator('#power-chart[data-ready="true"]')).to_be_visible()
                expect(page.locator('[name="paint_color"]')).to_have_value("#1255aa")
                assert not errors,errors
                checks.append({"width":width,"horizontal_scroll":False,"svg_aspect_ratio":round(image['width']/image['height'],4),"studio_rendered":True,"home_chart":True,"saved_config":True,"home_survives_deleted_golf":True})
                context.close()
            browser.close()
    finally: server.shutdown();server.server_close()
    (ROOT/"reports/visual-checks.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2))
    print("Capturas geradas: home e Studio em 360, 768 e 1280 px; SVG, controles, gráfico e persistência verificados.")


if __name__=="__main__":run()
