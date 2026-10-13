"""Configuração de produção: HTTPS e dados que sobrevivem a reinícios."""

import re
import pytest
from app import create_app
from app.extensions import db
from app.models import User


def production_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("GARAGEHUB_ENV", "production")
    monkeypatch.setenv("GARAGEHUB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SECRET_KEY", "chave-de-teste-com-mais-de-32-caracteres")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GARAGEHUB_TRUST_PROXY", raising=False)


@pytest.mark.parametrize("key", [None, "curta"])
def test_production_rejects_missing_or_weak_session_key(monkeypatch, tmp_path, key):
    production_environment(monkeypatch, tmp_path)
    if key is None:
        monkeypatch.delenv("SECRET_KEY")
    else:
        monkeypatch.setenv("SECRET_KEY", key)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()
    assert not (tmp_path / "data" / "secret.key").exists()


def test_https_proxy_sets_secure_cookie_and_health_is_public(monkeypatch, tmp_path):
    production_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("GARAGEHUB_TRUST_PROXY", "1")
    app = create_app({"TESTING": True})
    client = app.test_client()
    response = client.get("/", headers={"X-Forwarded-Proto": "https"})
    assert response.status_code == 200
    cookie = response.headers["Set-Cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
    health = client.get("/health")
    assert health.status_code == 200 and health.json == {"status": "ok"}
    assert "Set-Cookie" not in health.headers


def test_account_session_and_upload_survive_application_restart(monkeypatch, tmp_path):
    production_environment(monkeypatch, tmp_path)
    app = create_app({"TESTING": True})
    client = app.test_client()
    origin = "https://garagehub.test"
    response = client.get("/", base_url=origin)
    csrf_token = re.search(r'name="csrf-token" content="([^"]+)"', response.text).group(1)
    response = client.post(
        "/auth/cadastro",
        base_url=origin,
        headers={"Referer": origin + "/auth/cadastro"},
        data={
            "csrf_token": csrf_token,
            "username": "hosted_driver",
            "email": "hosted@example.test",
            "password": "SenhaDeTeste123!",
        },
    )
    assert response.status_code == 302
    cookie = client.get_cookie("session", domain="garagehub.test")
    upload = tmp_path / "data" / "uploads" / "persistent.svg"
    upload.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    with app.app_context():
        assert db.session.scalar(db.select(User)).username == "hosted_driver"
        db.session.remove()
        db.engine.dispose()

    restarted = create_app({"TESTING": True})
    after_restart = restarted.test_client()
    after_restart.set_cookie("session", cookie.value, domain="garagehub.test")
    assert after_restart.get("/garagem/", base_url=origin).status_code == 200
    assert after_restart.get("/uploads/persistent.svg", base_url=origin).data == upload.read_bytes()
