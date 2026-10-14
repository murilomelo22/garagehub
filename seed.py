"""Execute python seed.py para popular o banco local de demonstração."""

from app import create_app
from app.seed import seed_database

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_database()
    print(
        "Seed concluído: 12 perfis e 36 carros. Usuário principal: lucas_gti. Senha de demonstração: GarageHub123!"
    )
