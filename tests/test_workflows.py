"""Integrações reais das rotas com CSRF, sessões, banco e imagens."""

from io import BytesIO
from pathlib import Path
import re
from PIL import Image
from app.extensions import db
from app.models import (
    CarStats,
    Comment,
    Friendship,
    Like,
    Modification,
    Post,
    User,
    Vehicle,
    VehiclePhoto,
)
from app.seed import seed_database


def token(client):
    response = client.get("/", follow_redirects=True)
    return re.search(r'name="csrf-token" content="([^"]+)"', response.text).group(1)


def post(client, path, data=None, follow=True, **kwargs):
    payload = dict(data or {})
    payload["csrf_token"] = token(client)
    return client.post(path, data=payload, follow_redirects=follow, **kwargs)


def register(client, username="driver_one"):
    response = post(
        client,
        "/auth/cadastro",
        {
            "username": username,
            "email": username + "@example.test",
            "password": "SenhaTeste123!",
        },
    )
    assert response.status_code == 200
    return response


def logout(client):
    return post(client, "/auth/logout")


def login(client, username="driver_one"):
    return post(
        client, "/auth/login", {"identity": username, "password": "SenhaTeste123!"}
    )


def car_data(**overrides):
    result = {
        "brand": "Volkswagen",
        "model": "Golf GTI",
        "year": "2018",
        "color": "Vermelho",
        "engine": "2.0 TSI",
        "transmission": "DSG",
        "description": "Meu projeto diário.",
    }
    result.update(overrides)
    return result


def create_car(client, **kwargs):
    response = post(client, "/garagem/novo", car_data(**kwargs))
    assert response.status_code == 200
    return int(re.search(r"/garagem/(\d+)/editar", response.text).group(1))


def image_file(name="foto.png"):
    stream = BytesIO()
    Image.new("RGB", (100, 100), "red").save(stream, "PNG")
    stream.seek(0)
    return stream, name


def test_signup_password_login_logout_and_duplicate(client, app):
    register(client)
    with app.app_context():
        user = db.session.scalar(db.select(User))
        assert user.password_hash != "SenhaTeste123!"
        assert user.check_password("SenhaTeste123!")
        assert not user.check_password("outra")
    logout(client)
    assert client.get("/feed").status_code == 302
    response = post(
        client, "/auth/login", {"identity": "driver_one", "password": "errada"}
    )
    assert "incorretos" in response.text
    response = post(
        client,
        "/auth/cadastro",
        {
            "username": "driver_one",
            "email": "other@example.test",
            "password": "SenhaTeste123!",
        },
    )
    assert "já está cadastrado" in response.text
    assert "Seu feed" in login(client).text


def test_signup_validations_and_csrf(client, app):
    assert client.post("/auth/cadastro", data={}).status_code == 400
    for data, message in [
        (
            {"username": "a", "email": "a@example.test", "password": "longpassword"},
            "3 a 30",
        ),
        (
            {
                "username": "valid_name",
                "email": "sem-email",
                "password": "longpassword",
            },
            "e-mail válido",
        ),
        (
            {"username": "valid_name", "email": "a@example.test", "password": "curta"},
            "8 e 128",
        ),
    ]:
        assert message in post(client, "/auth/cadastro", data).text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0


def test_login_rejects_external_redirect(client):
    register(client)
    logout(client)
    response = post(
        client,
        "/auth/login?next=https://evil.example",
        {"identity": "driver_one", "password": "SenhaTeste123!"},
        follow=False,
    )
    assert response.location == "/feed"


def test_profile_public_upload_and_escape(client, app):
    register(client)
    response = post(
        client,
        "/perfil/editar",
        {
            "city": "São Paulo",
            "bio": "<script>alert(1)</script>",
            "photo": image_file(),
        },
    )
    assert response.status_code == 200
    assert "&lt;script&gt;" in response.text
    with app.app_context():
        user = db.session.scalar(db.select(User))
        filename = user.photo
        assert filename.endswith(".jpg")
    logout(client)
    assert client.get("/u/driver_one").status_code == 200
    assert client.get("/uploads/" + filename).status_code == 200
    assert client.get("/uploads/../secret.key").status_code == 404
    assert client.get("/u/missing").status_code == 404


def test_vehicle_crud_images_stats_cascade(client, app):
    register(client)
    car_id = create_car(client, photos=image_file())
    response = post(
        client, f"/garagem/{car_id}/editar", car_data(model="Golf GTI Stage 1")
    )
    assert "Golf GTI Stage 1" in response.text
    with app.app_context():
        filename = db.session.get(Vehicle, car_id).photos[0].filename
        assert (Path(app.config["UPLOAD_FOLDER"]) / filename).exists()
    post(client, f"/estatisticas/{car_id}", {"date": "2025-01-01", "power": "250"})
    post(
        client,
        f"/estatisticas/{car_id}/modificacoes",
        {
            "name": "Remap",
            "category": "Motor",
            "date": "2025-01-02",
            "value": "1800,50",
        },
    )
    assert client.get(f"/garagem/{car_id}").status_code == 200
    assert "Veículo excluído" in post(client, f"/garagem/{car_id}/excluir").text
    with app.app_context():
        assert db.session.get(Vehicle, car_id) is None
        assert db.session.scalar(db.select(CarStats)) is None
        assert db.session.scalar(db.select(Modification)) is None
        assert not (Path(app.config["UPLOAD_FOLDER"]) / filename).exists()


def test_vehicle_required_fields_year_and_bad_image(client, app):
    register(client)
    assert "Preencha marca" in post(client, "/garagem/novo", car_data(brand="")).text
    assert "Ano: informe" in post(client, "/garagem/novo", car_data(year="1800")).text
    assert (
        "ler essa imagem"
        in post(
            client,
            "/garagem/novo",
            car_data(photos=(BytesIO(b"fake jpeg"), "fake.jpg")),
        ).text
    )
    assert (
        "Use uma imagem"
        in post(
            client, "/garagem/novo", car_data(photos=(BytesIO(b"<svg/>"), "bad.svg"))
        ).text
    )
    with app.app_context():
        assert db.session.scalar(db.select(Vehicle)) is None


def test_failed_multi_upload_removes_already_saved_photo(client, app):
    register(client)
    data = car_data(photos=[image_file(), (BytesIO(b"fake"), "bad.jpg")])
    assert "ler essa imagem" in post(client, "/garagem/novo", data).text
    assert list(Path(app.config["UPLOAD_FOLDER"]).iterdir()) == []


def test_car_owner_permissions_on_all_changes(client, app):
    register(client)
    car_id = create_car(client, photos=image_file())
    post(client, f"/estatisticas/{car_id}", {"date": "2025-01-01", "power": "200"})
    post(
        client,
        f"/estatisticas/{car_id}/modificacoes",
        {"name": "Remap", "category": "Motor", "date": "2025-01-02", "value": "1000"},
    )
    with app.app_context():
        photo_id = db.session.scalar(db.select(VehiclePhoto)).id
        stats_id = db.session.scalar(db.select(CarStats)).id
        mod_id = db.session.scalar(db.select(Modification)).id
    logout(client)
    register(client, "driver_two")
    assert client.get(f"/garagem/{car_id}").status_code == 200
    for path in [
        f"/garagem/{car_id}/editar",
        f"/garagem/{car_id}/excluir",
        f"/estatisticas/{car_id}",
        f"/estatisticas/{car_id}/modificacoes",
        f"/visualizador/{car_id}",
        f"/garagem/{car_id}/fotos/{photo_id}/excluir",
        f"/estatisticas/{car_id}/medicoes/{stats_id}/excluir",
        f"/estatisticas/{car_id}/modificacoes/{mod_id}/excluir",
    ]:
        assert post(client, path, {}).status_code == 403, path


def test_stat_history_orders_by_measurement_date(client, app):
    register(client)
    car_id = create_car(client)
    for day, power in [
        ("2025-03-01", "290"),
        ("2025-01-01", "230"),
        ("2025-02-01", "260"),
    ]:
        response = post(
            client,
            f"/estatisticas/{car_id}",
            {
                "date": day,
                "power": power,
                "torque": "350",
                "zero_to_hundred": "6.2",
                "top_speed": "240",
                "consumption": "10.5",
            },
        )
        assert response.status_code == 200
    with app.app_context():
        car = db.session.get(Vehicle, car_id)
        assert [item.power for item in car.stats] == [230, 260, 290]
        assert car.latest_stats.power == 290
    response = client.get(f"/garagem/{car_id}")
    assert '"power": [230.0, 260.0, 290.0]' in response.text


def test_stats_validation_rejects_nan_future_and_negative(client, app):
    register(client)
    car_id = create_car(client)
    assert (
        "informe um número"
        in post(
            client, f"/estatisticas/{car_id}", {"date": "2025-01-01", "power": "nan"}
        ).text
    )
    assert (
        "data válida"
        in post(
            client, f"/estatisticas/{car_id}", {"date": "2999-01-01", "power": "250"}
        ).text
    )
    assert (
        "valor válido"
        in post(
            client,
            f"/estatisticas/{car_id}/modificacoes",
            {
                "name": "Remap",
                "category": "Motor",
                "date": "2025-01-01",
                "value": "-10",
            },
        ).text
    )
    with app.app_context():
        assert db.session.scalar(db.select(CarStats)) is None
        assert db.session.scalar(db.select(Modification)) is None


def test_modification_money_and_remove_history(client, app):
    register(client)
    car_id = create_car(client)
    post(
        client,
        f"/estatisticas/{car_id}/modificacoes",
        {
            "name": "Rodas",
            "category": "Rodas e pneus",
            "date": "2025-01-01",
            "value": "1500.55",
        },
    )
    with app.app_context():
        item = db.session.scalar(db.select(Modification))
        assert str(item.value) == "1500.55"
        item_id = item.id
    assert (
        "Registro removido"
        in post(client, f"/estatisticas/{car_id}/modificacoes/{item_id}/excluir").text
    )
    with app.app_context():
        assert db.session.get(Modification, item_id) is None


def test_viewer_config_saved_validated_and_reloaded(client, app):
    register(client)
    car_id = create_car(client)
    config = {
        "paint_color": "#ff0000",
        "wheel_color": "#101010",
        "wheel_size": "1.2",
        "suspension": "lowered",
        "spoiler": "yes",
    }
    response = post(
        client,
        f"/visualizador/{car_id}",
        config,
        headers={"Accept": "application/json"},
    )
    assert response.json["config"]["spoiler"] is True
    assert 'value="#ff0000"' in client.get(f"/garagem/{car_id}").text
    for override in [
        {"paint_color": "javascript:bad"},
        {"wheel_size": "99"},
        {"wheel_size": "nan"},
        {"suspension": "invalid"},
        {"spoiler": "invalid"},
    ]:
        assert (
            post(
                client,
                f"/visualizador/{car_id}",
                config | override,
                headers={"Accept": "application/json"},
            ).status_code
            == 400
        )
    with app.app_context():
        assert db.session.get(Vehicle, car_id).viewer_config["wheel_size"] == 1.2


def test_feed_follow_unfollow_and_chronological_order(client, app):
    register(client)
    post(client, "/posts", {"text": "post do driver_one"})
    logout(client)
    register(client, "driver_two")
    post(client, "/posts", {"text": "post do driver_two primeiro"})
    post(client, "/posts", {"text": "post do driver_two segundo"})
    logout(client)
    login(client)
    assert "post do driver_two primeiro" not in client.get("/feed").text
    with app.app_context():
        other_id = db.session.scalar(
            db.select(User).filter_by(username="driver_two")
        ).id
    post(client, f"/usuarios/{other_id}/seguir")
    feed = client.get("/feed").text
    assert "post do driver_two primeiro" in feed
    assert (
        feed.index("post do driver_two segundo")
        < feed.index("post do driver_two primeiro")
        < feed.index("post do driver_one")
    )
    post(client, f"/usuarios/{other_id}/seguir")
    assert "post do driver_two primeiro" not in client.get("/feed").text


def test_posts_photo_like_unlike_comment_and_delete(client, app):
    register(client)
    assert "Escreva algo" in post(client, "/posts", {}).text
    response = post(client, "/posts", {"text": "Novo projeto", "photo": image_file()})
    assert "Novo projeto" in response.text
    with app.app_context():
        item = db.session.scalar(db.select(Post))
        post_id, filename = item.id, item.photo
    post(client, f"/posts/{post_id}/curtir")
    with app.app_context():
        assert db.session.scalar(db.select(Like)) is not None
    post(client, f"/posts/{post_id}/curtir")
    with app.app_context():
        assert db.session.scalar(db.select(Like)) is None
    assert (
        "Muito bom!"
        in post(client, f"/posts/{post_id}/comentar", {"text": "Muito bom!"}).text
    )
    assert (
        "Preencha comentário"
        in post(client, f"/posts/{post_id}/comentar", {"text": ""}).text
    )
    post(client, f"/posts/{post_id}/excluir")
    with app.app_context():
        assert db.session.get(Post, post_id) is None
        assert db.session.scalar(db.select(Comment)) is None
        assert not (Path(app.config["UPLOAD_FOLDER"]) / filename).exists()


def test_other_user_cannot_delete_post(client, app):
    register(client)
    post(client, "/posts", {"text": "Meu post"})
    with app.app_context():
        post_id = db.session.scalar(db.select(Post)).id
    logout(client)
    register(client, "driver_two")
    assert post(client, f"/posts/{post_id}/excluir").status_code == 403


def test_user_search_name_city_brand_and_model(client):
    register(client)
    create_car(client)
    post(client, "/perfil/editar", {"city": "Curitiba", "bio": ""})
    logout(client)
    register(client, "driver_two")
    for q in ["driver_one", "Curitiba", "Volkswagen", "Golf"]:
        assert "driver_one" in client.get("/amigos", query_string={"q": q}).text
    assert "Nenhuma garagem encontrada" in client.get("/amigos?q=sem-resultados").text
    assert "Nenhuma garagem encontrada" in client.get("/amigos?q=%25").text


def test_friendship_request_accept_authorization_and_remove(client, app):
    register(client)
    with app.app_context():
        first_id = db.session.scalar(db.select(User)).id
    logout(client)
    register(client, "driver_two")
    with app.app_context():
        second_id = db.session.scalar(
            db.select(User).filter_by(username="driver_two")
        ).id
    post(client, f"/usuarios/{first_id}/amizade/solicitar")
    assert post(client, f"/usuarios/{first_id}/amizade/aceitar").status_code == 403
    post(client, f"/usuarios/{first_id}/amizade/solicitar")
    with app.app_context():
        assert (
            db.session.scalar(db.select(db.func.count()).select_from(Friendship)) == 1
        )
    logout(client)
    login(client)
    assert "Aceitar amizade" in client.get("/amigos").text
    post(client, f"/usuarios/{second_id}/amizade/aceitar")
    with app.app_context():
        assert db.session.scalar(db.select(Friendship)).status == "accepted"
    post(client, f"/usuarios/{second_id}/amizade/remover")
    with app.app_context():
        assert db.session.scalar(db.select(Friendship)) is None


def test_friend_request_cancel_and_decline(client, app):
    register(client)
    logout(client)
    register(client, "driver_two")
    with app.app_context():
        first_id = db.session.scalar(
            db.select(User).filter_by(username="driver_one")
        ).id
        second_id = db.session.scalar(
            db.select(User).filter_by(username="driver_two")
        ).id
    post(client, f"/usuarios/{first_id}/amizade/solicitar")
    post(client, f"/usuarios/{first_id}/amizade/cancelar")
    with app.app_context():
        assert db.session.scalar(db.select(Friendship)) is None
    post(client, f"/usuarios/{first_id}/amizade/solicitar")
    logout(client)
    login(client)
    assert post(client, f"/usuarios/{second_id}/amizade/cancelar").status_code == 403
    post(client, f"/usuarios/{second_id}/amizade/recusar")
    with app.app_context():
        assert db.session.scalar(db.select(Friendship)) is None


def test_seed_is_repeatable_and_public_pages_render(app, client):
    with app.app_context():
        seed_database()
        seed_database()
        for model, count in [(User, 12), (Vehicle, 36), (Post, 24), (CarStats, 108)]:
            assert (
                db.session.scalar(db.select(db.func.count()).select_from(model))
                == count
            )
        cars = db.session.scalars(db.select(Vehicle)).all()
        car_ids = [car.id for car in cars]
    for car_id in car_ids:
        assert client.get(f"/garagem/{car_id}").status_code == 200
    assert client.get("/u/lucas_gti").status_code == 200


def test_csrf_required_for_authenticated_mutations(client):
    register(client)
    assert client.post("/posts", data={"text": "Sem CSRF"}).status_code == 400
    assert client.get("/auth/logout").status_code == 405
    assert client.get("/pagina-inexistente").status_code == 404


def test_feed_pagination(client, app):
    register(client)
    with app.app_context():
        user_id = db.session.scalar(db.select(User)).id
        db.session.add_all([Post(user_id=user_id, text=f"item-{i}") for i in range(12)])
        db.session.commit()
    assert client.get("/feed").text.count('<article class="panel post"') == 10
    assert client.get("/feed?page=2").text.count('<article class="panel post"') == 2
