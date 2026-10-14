"""Smoke do artefato: páginas esperadas, links locais, metadados e versão de assets."""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit, parse_qs

VERSION = "V0.2"


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.references, self.ids, self.meta, self.title_parts = [], set(), {}, []
        self.in_title, self.in_footer, self.footer_parts = False, False, []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "base": return
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "title": self.in_title = True
        if tag == "footer": self.in_footer = True
        if tag == "meta": self.meta[attrs.get("name") or attrs.get("property")] = attrs.get("content", "")
        for key in ("href", "src", "data-viewer-src", "data-chart-src", "data-gallery-src"):
            if attrs.get(key): self.references.append((key, attrs[key]))
        if tag == "meta" and attrs.get("name") == "demo-data-url": self.references.append(("src",attrs["content"]))

    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag == "footer": self.in_footer = False

    def handle_data(self, value):
        if self.in_title: self.title_parts.append(value)
        if self.in_footer: self.footer_parts.append(value)

    @property
    def title(self): return "".join(self.title_parts).strip()


def verify(output, expected_pages=None):
    output = Path(output)
    paths = sorted(output.glob("*.html"))
    if not paths: raise RuntimeError("Exportação sem páginas HTML.")
    if expected_pages is None:
        expected_pages = json.loads((output/"build-manifest.json").read_text())["pages"]
    actual = {path.name for path in paths}
    if actual != set(expected_pages):
        raise RuntimeError(f"Páginas ausentes ou antigas: {actual ^ set(expected_pages)}")
    pages, titles, descriptions, errors = {}, set(), set(), []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        # A única ocorrência autorizada é o controle de restauração exigido na V0.2.
        inspected = re.sub(r'<button\b[^>]*data-restore-demo[^>]*>Restaurar dados de exemplo</button>', "", text)
        if re.search(r"V0\.0|dados de exemplo", inspected, re.I): errors.append(f"{path.name}: conteúdo antigo proibido")
        if re.search(r"V0\.1|R\$ 2500,00|Garagem de exemplo", text, re.I): errors.append(f"{path.name}: conteúdo desatualizado")
        page = Page(text);pages[path.name]=page
        if VERSION not in "".join(page.footer_parts): errors.append(f"{path.name}: rodapé sem {VERSION}")
        description=page.meta.get("description", "")
        if not page.title or page.title in titles: errors.append(f"{path.name}: título vazio ou repetido")
        if len(description)<45 or description in descriptions: errors.append(f"{path.name}: descrição vazia, curta ou repetida")
        titles.add(page.title);descriptions.add(description)
        for key in ("og:title","og:description","og:image","twitter:card","twitter:image","theme-color"):
            if not page.meta.get(key): errors.append(f"{path.name}: falta {key}")
        if re.fullmatch(r"carro-\d+\.html",path.name):
            schemas=re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)
            if not schemas or json.loads(schemas[0]).get("@type")!="Vehicle": errors.append(f"{path.name}: falta schema Vehicle")
    references=0
    for name,page in pages.items():
        for attribute,url in page.references:
            parsed=urlsplit(url)
            if parsed.scheme or parsed.netloc or url.startswith("data:"): continue
            local=unquote(parsed.path).lstrip("/")
            destination=output/local if local else output/name
            if local and not destination.is_file(): errors.append(f"{name}: arquivo ausente {url}")
            if not local and parsed.fragment and parsed.fragment not in page.ids: errors.append(f"{name}: âncora ausente {url}")
            if local in pages and parsed.fragment and parsed.fragment not in pages[local].ids: errors.append(f"{name}: âncora ausente {url}")
            if local.endswith((".css",".js")) and destination.is_file():
                expected=sha256(destination.read_bytes()).hexdigest()[:12]
                if parse_qs(parsed.query).get("v")!=[expected]: errors.append(f"{name}: asset sem hash correto {url}")
            references+=1
    if errors: raise RuntimeError("Falha na verificação:\n"+"\n".join(errors))
    return {"version":VERSION,"pages":len(pages),"local_references":references,"status":"ok"}


if __name__=="__main__":
    print(json.dumps(verify(Path(__file__).resolve().parents[1]/"docs"),ensure_ascii=False))
