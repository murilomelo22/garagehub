"""Regressões de apresentação e comportamento compartilhado da V0.1."""

from datetime import datetime, timezone
import re
from app import presentation
from app.extensions import db
from app.models import Comment, Like, Post, User, Vehicle
from app.seed import seed_database
from test_workflows import login, logout, post, register, create_car


def test_brazilian_numbers_money_and_brasilia_time(monkeypatch):
    assert presentation.number_br(1234.5) == "1.234,5"
    assert presentation.money_br(2500) == "R$ 2.500,00"
    assert presentation.number_br(None) == "—"
    class FixedDate(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 14, 1, tzinfo=timezone.utc).astimezone(tz)
    monkeypatch.setattr(presentation, "datetime", FixedDate)
    assert presentation.relative_time(datetime(2026, 10, 13, 23)) == "há 2 h"
    assert presentation.relative_time(datetime(2026, 10, 13, 1)) == "ontem"


def test_demo_has_varied_coherent_measurements_and_interactions(app):
    with app.app_context():
        seed_database()
        for owner in db.session.scalars(db.select(User)):
            assert len(owner.vehicles) >= 3
            for car in owner.vehicles:
                a,b,c = car.stats
                assert a.power < b.power < c.power
                assert a.zero_to_hundred > b.zero_to_hundred > c.zero_to_hundred
                assert a.top_speed < b.top_speed < c.top_speed
                assert a.consumption > b.consumption > c.consumption
                assert b.power-a.power <= 4
                assert c.power-b.power > b.power-a.power
        posts = db.session.scalars(db.select(Post)).all()
        assert len({item.created_at for item in posts}) == len(posts)
        assert {len(item.comments) for item in posts} == {1,2,3}
        assert {len(item.likes) for item in posts} == {1,2,3}
        assert db.session.scalar(db.select(db.func.count()).select_from(Like)) > 0
        assert db.session.scalar(db.select(db.func.count()).select_from(Comment)) == 12


def test_feed_all_following_and_brand_filters(client, app):
    register(client)
    create_car(client, brand="Volkswagen")
    post(client,"/posts",{"text":"VW na garagem"})
    logout(client)
    register(client,"driver_two")
    create_car(client,brand="Honda",model="Civic")
    post(client,"/posts",{"text":"Projeto Honda"})
    logout(client);login(client)
    assert "Projeto Honda" not in client.get("/feed?filter=following").text
    assert "Projeto Honda" in client.get("/feed?filter=all").text
    assert "Projeto Honda" in client.get("/feed?filter=all&brand=Honda").text
    assert "VW na garagem" not in client.get("/feed?filter=all&brand=Honda").text


def test_friend_filters_and_stable_profile_destination(client, app):
    register(client);create_car(client)
    post(client,"/perfil/editar",{"city":"Curitiba","bio":""})
    logout(client);register(client,"driver_two")
    assert "driver_one" in client.get("/amigos?city=Curitiba&brand=Volkswagen").text
    assert "Nenhuma garagem encontrada" in client.get("/amigos?city=Recife&brand=Volkswagen").text
    assert client.get("/perfil").location == "/u/driver_two"
    for path in ["/feed","/garagem/","/amigos","/u/driver_one"]:
        source=client.get(path).text
        assert re.search(r'href="/perfil">.*?<span>Perfil</span>', source, re.S)
        assert "Sua paixão. Sua comunidade." not in source
        assert "V0.1" in source


def test_seo_unique_and_metric_selector_on_local_pages(client):
    register(client);car_id=create_car(client)
    sources=[client.get(path).text for path in ["/feed","/garagem/","/amigos",f"/garagem/{car_id}"]]
    descriptions=[re.search(r'<meta name="description" content="([^"]+)"',source).group(1) for source in sources]
    assert len(set(descriptions))==len(descriptions)
    for source in sources:
        assert 'property="og:image"' in source and 'name="twitter:card"' in source
    detail=sources[-1]
    assert 'id="chart-metric"' in detail and 'id="capture-viewer"' in detail
    assert 'id="reset-viewer"' in detail and 'id="viewer-defaults"' in detail


def test_seed_does_not_replace_custom_history_and_post_photo_is_independent(app, client):
    with app.app_context():
        seed_database()
        car=db.session.get(Vehicle,1)
        original=car.stats[0].power
        car.stats[0].power=original+1
        post=db.session.scalar(db.select(Post).where(Post.user_id==car.user_id))
        assert post.photo != car.photos[0].filename
        seed_database()
        assert car.stats[0].power==original+1
        assert len(car.stats)==3
