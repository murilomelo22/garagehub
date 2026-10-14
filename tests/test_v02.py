"""Regressões da publicação completa, da comunidade e da demonstração da V0.2."""
from pathlib import Path
import re
import shutil
import sys
import pytest
from app.extensions import db
from app.models import User
from app.seed import seed_database
from test_workflows import post

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_pages import verify
import build_pages


def test_artifact_has_every_profile_and_car():
    result=verify(ROOT/"docs")
    assert result["pages"]==55
    assert len(list((ROOT/"docs").glob("carro-*.html")))==36
    assert len(list((ROOT/"docs").glob("perfil-*.html")))==12
    car=(ROOT/"docs/carro-1.html").read_text()
    assert "R$ 2.500,00" in car and "V0.2" in car
    assert "lucas_gti" in car and '"@type": "Vehicle"' in car


@pytest.mark.parametrize("change",["old_version","old_banner","broken_link","wrong_footer","stale_asset"])
def test_verifier_rejects_publication_regressions(tmp_path,change):
    output=tmp_path/"site";shutil.copytree(ROOT/"docs",output)
    path=output/"carro-1.html";source=path.read_text()
    if change=="old_version": source+='<!-- V0.0 -->'
    elif change=="old_banner": source+='<p>dados de exemplo</p>'
    elif change=="broken_link": source+='<a href="carro-inexistente.html">Projeto</a>'
    elif change=="wrong_footer": source=source.replace('class="orange">V0.2','class="orange">versão desconhecida')
    else: source=re.sub(r'(style\.css\?v=)[a-f0-9]+',r'\g<1>antigo',source)
    path.write_text(source)
    with pytest.raises(RuntimeError): verify(output)


def test_failed_export_keeps_previous_site(tmp_path,monkeypatch):
    destination=tmp_path/"docs";destination.mkdir();(destination/"index.html").write_text("última versão válida")
    def fail(): raise RuntimeError("falha durante a geração")
    monkeypatch.setattr(build_pages,"render_export",fail)
    with pytest.raises(RuntimeError): build_pages.build(destination)
    assert (destination/"index.html").read_text()=="última versão válida"


def test_home_has_shared_studio_and_gti_chart(client):
    source=client.get("/").text
    assert 'data-home-demo="true"' in source and 'id="activate-viewer"' in source
    assert 'id="chart-metric"' in source and '"power": [230, 233, 268]' in source
    assert 'class="topbar-slogan"' in source


def test_community_model_search_and_ordering(client,app):
    with app.app_context(): seed_database()
    post(client,"/auth/login",{"identity":"lucas_gti","password":"GarageHub123!"})
    source=client.get("/amigos?q=BRZ").text
    assert "marina_boxer" in source and "Nenhuma garagem encontrada" not in source
    for order,first in [("recent","nina_estrada"),("cars","caio_track")]:
        source=client.get(f"/amigos?order={order}").text
        names=re.findall(r'<h3>([a-z0-9_]+)</h3>',source)
        assert len(names)==11 and names[0]==first
    assert client.get("/amigos?order=likes").status_code==200
    assert "Nenhuma garagem encontrada" in client.get("/amigos?q=zzzzzz").text
    assert 'class="topbar-slogan"' not in client.get("/feed").text
