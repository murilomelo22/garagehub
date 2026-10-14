"""Consolida auditorias móveis reais; Lighthouse é um utilitário externo de desenvolvimento."""
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PAGES={"home":"index.html","feed":"feed.html","garagem":"garagem.html","amigos":"amigos.html","perfil":"perfil-lucas_gti.html","carro":"carro-1.html","acesso":"acesso.html"}


def run():
    executable=os.getenv("LIGHTHOUSE_BIN") or shutil.which("lighthouse")
    if not executable: raise SystemExit("Instale Lighthouse como utilitário e indique LIGHTHOUSE_BIN; consulte o README.")
    output=ROOT/"reports/lighthouse";output.mkdir(parents=True,exist_ok=True)
    base=os.getenv("AUDIT_BASE_URL","http://127.0.0.1:8765/").rstrip("/")+"/"
    entries=[]
    for name,route in PAGES.items():
        prefix=output/f"{name}-mobile"
        subprocess.run([executable,base+route,"--quiet","--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage","--only-categories=performance,accessibility,best-practices,seo","--output=json","--output=html",f"--output-path={prefix}"],check=True,env={**os.environ,"CHROME_PATH":os.getenv("CHROME_PATH",shutil.which("chromium") or shutil.which("google-chrome") or "")})
        report=json.loads(Path(str(prefix)+".report.json").read_text())
        scores={key:round(category["score"]*100) for key,category in report["categories"].items()}
        entry={"page":name,"route":route,"version":"V0.2","lighthouse_version":report["lighthouseVersion"],"fetch_time":report["fetchTime"],"form_factor":report["configSettings"]["formFactor"],"throttling_method":report["configSettings"]["throttlingMethod"],"scores":scores,"runtime_error":report.get("runtimeError"),"warnings":report.get("runWarnings",[])}
        entries.append(entry);print(name,scores,flush=True)
    (ROOT/"reports/lighthouse-summary.json").write_text(json.dumps(entries,ensure_ascii=False,indent=2))
    if any(entry["runtime_error"] or min(entry["scores"].values())<90 for entry in entries):
        raise SystemExit("Uma ou mais páginas ficaram abaixo da meta. Consulte os relatórios reais antes de publicar.")
    print("Meta 90+ atingida nas quatro categorias das sete páginas representativas.")


if __name__=="__main__":run()
