"""Verifica contraste de texto visível, rótulos e foco nas páginas estáticas.

A verificação de contraste usa as cores sólidas computadas e a composição de alfa;
textos sobre imagens/gradientes também precisam de inspeção visual.
"""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


def run():
    with tempfile.TemporaryDirectory(prefix="garagehub-a11y-") as temporary:
        Path(temporary,"garagehub").symlink_to(ROOT/"docs",target_is_directory=True)
        server=ThreadingHTTPServer(("127.0.0.1",0),partial(QuietHandler,directory=temporary))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=shutil.which("chromium") or shutil.which("google-chrome"),args=["--no-sandbox","--disable-dev-shm-usage"])
                page=browser.new_page(viewport={"width":1280,"height":900})
                page.route("https://cdn.jsdelivr.net/**",lambda route:route.abort())
                issues=[];checked=0
                for file in sorted((ROOT/"docs").glob("*.html")):
                    page.goto(f"http://127.0.0.1:{server.server_port}/garagehub/{file.name}")
                    result=page.evaluate("""() => {
                      const parse=value=>{const values=value.match(/[\\d.]+/g)?.map(Number)||[0,0,0,0];return [...values.slice(0,3),values[3]??1];};
                      const mix=(top,bottom)=>top.slice(0,3).map((v,i)=>v*top[3]+bottom[i]*(1-top[3]));
                      const light=rgb=>rgb.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
                      const bg=element=>{const parents=[];for(let current=element;current;current=current.parentElement)parents.unshift(current);return parents.reduce((color,parent)=>mix(parse(getComputedStyle(parent).backgroundColor),color),[255,255,255]);};
                      const problems=[];let count=0;
                      const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
                      while(walker.nextNode()){
                        const node=walker.currentNode,element=node.parentElement;
                        if(!node.textContent.trim()||element.closest('script,style,option,[hidden],[aria-hidden=true],button:disabled')||!element.getClientRects().length)continue;
                        const style=getComputedStyle(element);if(style.visibility==='hidden'||Number(style.opacity)===0)continue;
                        const background=bg(element),foreground=mix(parse(style.color),background);
                        const a=light(background),b=light(foreground),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
                        const minimum=parseFloat(style.fontSize)>=24||(parseFloat(style.fontSize)>=18.66&&Number(style.fontWeight)>=700)?3:4.5;
                        count++;
                        if(ratio+.01<minimum)problems.push({text:node.textContent.trim().slice(0,70),ratio:Number(ratio.toFixed(2)),minimum,tag:element.tagName});
                      }
                      document.querySelectorAll('img').forEach(img=>{if(!img.hasAttribute('alt'))problems.push({image:img.src,missing:'alt'});});
                      document.querySelectorAll('input:not([type=hidden]),textarea,select').forEach(input=>{
                        if(!input.labels?.length&&!input.hasAttribute('aria-label')&&!input.hasAttribute('aria-labelledby'))problems.push({input:input.name,missing:'rótulo'});
                      });
                      return {problems,count};
                    }""")
                    checked+=result["count"]
                    issues.extend({"page":file.name,**issue} for issue in result["problems"])
                assert not issues,issues
                page.goto(f"http://127.0.0.1:{server.server_port}/garagehub/garagem.html")
                page.get_by_role("link",name="Adicionar veículo",exact=True).focus()
                assert page.evaluate("parseFloat(getComputedStyle(document.activeElement).outlineWidth)>=2")
                browser.close()
                print(f"Acessibilidade OK: {checked} trechos de texto com contraste AA, imagens com alt, campos rotulados e foco visível.")
        finally:
            server.shutdown();server.server_close()


if __name__=="__main__":run()
