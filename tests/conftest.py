"""Cada teste recebe um banco descartável e uma pasta isolada de uploads."""

import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-apenas-para-testes",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
