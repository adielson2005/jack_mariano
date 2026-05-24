from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")

    db.init_app(app)
    CORS(app)

    from app.routes.api import api_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(api_bp,   url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    from app.models import Category, Product

    if Category.query.count() > 0:
        return

    categories = [
        {
            "slug": "bolo",
            "name": "Bolo Personalizado",
            "description": "Bolos personalizados com massa, recheio e decoração à sua escolha.",
            "icon": "🎂",
            "options": {
                "massa": [
                    "Chocolate",
                    "Branca",
                    "Cenoura",
                    "Red Velvet",
                    "Limão",
                    "Baunilha",
                ],
                "recheio": [
                    "Brigadeiro",
                    "Brigadeiro Branco",
                    "Morango com Creme",
                    "Limão",
                    "Maracujá",
                    "Ninho com Nutella",
                    "Prestígio",
                    "Romeu e Julieta",
                ],
                "decoracao": [
                    "Simples (chantilly liso)",
                    "Semínaked",
                    "Naked cake",
                    "Temático (personagem/tema)",
                    "Floral",
                    "Drip cake",
                ],
                "tamanho": [
                    "Pequeno (até 10 pessoas)",
                    "Médio (até 20 pessoas)",
                    "Grande (até 40 pessoas)",
                    "Extra Grande (mais de 40 pessoas)",
                ],
            },
        },
        {
            "slug": "doces",
            "name": "Doces",
            "description": "Doces finos artesanais, simples ou sofisticados.",
            "icon": "🍬",
            "options": {
                "tipo": ["Simples", "Sofisticado / Gourmet"],
                "sabor": [
                    "Brigadeiro Tradicional",
                    "Brigadeiro Branco",
                    "Beijinho",
                    "Cajuzinho",
                    "Bicho de Pé",
                    "Maracujá",
                    "Limão",
                    "Pistache",
                    "Ninho com Nutella",
                    "Churros",
                ],
            },
        },
        {
            "slug": "salgados",
            "name": "Salgados",
            "description": "Salgados artesanais fritos ou assados.",
            "icon": "🥟",
            "options": {
                "tipo": ["Frito", "Assado"],
                "sabor": [
                    "Carne",
                    "Frango",
                    "Queijo",
                    "Palmito",
                    "Camarão",
                    "Atum",
                    "Calabresa",
                    "Pizza",
                ],
            },
        },
        {
            "slug": "kit-festa",
            "name": "Kit Festa",
            "description": "Combo completo: bolo + doces + salgados para sua festa.",
            "icon": "🎉",
            "options": {
                "pessoas": [
                    "Até 20 pessoas",
                    "Até 40 pessoas",
                    "Até 60 pessoas",
                    "Mais de 60 pessoas",
                ],
                "inclui": [
                    "Bolo + Doces + Salgados",
                    "Bolo + Doces",
                    "Bolo + Salgados",
                    "Somente Doces + Salgados",
                ],
            },
        },
    ]

    for cat_data in categories:
        options = cat_data.pop("options")
        category = Category(**cat_data)
        db.session.add(category)
        db.session.flush()

        for option_name, choices in options.items():
            for choice in choices:
                product = Product(
                    category_id=category.id,
                    option_group=option_name,
                    name=choice,
                )
                db.session.add(product)

    db.session.commit()
