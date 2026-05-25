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

    app.register_blueprint(api_bp, url_prefix="/api")
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
            "name": "Bolos",
            "description": "Bolos personalizados com massa, recheio e decoração à sua escolha.",
            "icon": "🎂",
            "price_from": None,
            "options": {
                "Massa": [
                    "Branca (Baunilha)",
                    "Chocolate",
                ],
                "Recheio Tradicional": [
                    "4 Leites",
                    "Leite Ninho Trufado",
                    "Creme com Abacaxi",
                    "Mousse de Maracujá",
                    "Mousse de Limão",
                    "Creme de Cupuaçu",
                    "Doce de Leite com Abacaxi",
                    "Brigadeiro com Ovomaltine",
                    "Ninho com Ovomaltine",
                    "Ganache ao Leite",
                    "Ganache Meio Amargo",
                    "Ganache Branco",
                    "Amendoim",
                    "Cappuccino",
                    "Doce de Leite com Canela",
                    "Beijinho",
                    "Doce de Leite",
                    "Ninho Oreo",
                    "Brigadeiro e Oreo",
                    "Brigadeiro",
                    "Ganache de Café",
                    "Alpino",
                ],
                "Recheio Especial": [
                    "Creme com Nozes",
                    "Creme com Ameixa",
                    "Creme com Morango Fruta",
                    "Creme com Frutas Vermelhas",
                    "Creme com Geléia de Morango",
                    "Ferreiro Rocher",
                    "Creme com Damasco",
                    "Creme com Castanha de Caju",
                    "Sonho de Valsa",
                    "Ouro Branco",
                    "Creme com Pêssego",
                ],
                "Recheio Super Especial": [
                    "Pistache",
                    "Pistache com Geléia de Morango",
                    "Creme com Castanha do Pará",
                ],
                "Decoração": [
                    "Sem decoração",
                    "Morangos",
                    "Brigadeiro Festa",
                    "Macarrons",
                    "Arte a Mão",
                ],
                "Topo de Bolo": [
                    "Sem topo",
                    "Papel de Arroz",
                    "Impresso Simples",
                    "Impresso Detalhado",
                    "3D em Camadas",
                    "Flores Artificiais",
                    "Bolo de Andar",
                ],
            },
        },
        {
            "slug": "doces",
            "name": "Doces",
            "description": "Doces finos artesanais, brigadeiros gourmet, trufas e muito mais.",
            "icon": "🍬",
            "price_from": None,
            "options": {
                "Tipo": [
                    "Brigadeiro Gourmet",
                    "Brigadeiro Gourmet Especial",
                    "Copinho de Chocolate (Branco ou ao Leite)",
                    "Copinho de Acrílico 30ml",
                    "Mini Brownie",
                    "Mini Trufa",
                    "Doce Fino",
                    "Pipoca Gourmet",
                    "Coloridos ou Carimbados",
                ],
                "Sabor": [
                    "Brigadeiro Tradicional",
                    "Brigadeiro com Amendoim",
                    "Beijinho",
                    "Limão",
                    "Delícia de Amendoim",
                    "Churros",
                    "Maracujá",
                    "Dois Amores",
                    "Napolitano",
                    "Olho de Sogra",
                    "Beijinho Queimado",
                    "Morango",
                    "Cajuzinho",
                    "Ferreiro Rocher",
                    "Ninho com Nutella",
                    "Brigadeiro M&M",
                    "Brigadeiro com Granulado Meio Amargo",
                    "Café",
                    "Cappuccino",
                    "Ninho M&M",
                    "Castanha do Pará",
                    "Oreo",
                    "Pistache",
                    "Ninho Uva",
                    "Ninho Morango",
                    "Ninho Cereja",
                    "Ninho Damasco",
                    "Pedacim do Céu Pêssego",
                    "Ninho com Nozes",
                    "Coco",
                    "Cupuaçu",
                    "Ninho",
                    "Camafeu Nozes",
                    "Surpresa de Damasco",
                    "Surpresa de Castanha de Caju",
                    "Macarron",
                    "Bem Casado com Tag",
                    "Chocolate",
                    "Ovomaltine",
                ],
            },
        },
        {
            "slug": "salgados",
            "name": "Salgados",
            "description": "Salgados artesanais fritos ou assados, empadinhas e mini pastéis.",
            "icon": "🥟",
            "price_from": None,
            "options": {
                "Tipo": [
                    "Salgados Fritos",
                    "Salgados Assados",
                    "Empadinhas",
                    "Mini Pastel de Vento",
                ],
                "Sabor dos Fritos": [
                    "Coxinha de Frango",
                    "Risole de Carne",
                    "Croquete de Milho",
                    "Maravilha (Presunto, Queijo e Orégano)",
                    "Croquete de Carne Seca",
                    "Bolinha de Queijo",
                    "Pastel de Milho e Requeijão",
                    "Delícia de Calabresa",
                    "Enroladinho de Salsicha",
                    "Kibe",
                ],
                "Sabor dos Assados": [
                    "Esfira de Carne",
                    "Esfira de Frango",
                    "Enroladinho de Salsicha",
                    "Delícia de Calabresa",
                    "Delícia de Presunto e Queijo",
                    "Delícia de Creme de Milho",
                    "Delícia de Mortadela Defumada",
                    "Delícia de 4 Queijos",
                    "Enroladinho de Queijo",
                    "Mini Pizza (Queijo, Presunto, Frango e Calabresa)",
                ],
                "Sabor das Empadinhas": [
                    "Frango",
                    "Palmito",
                ],
                "Sabor do Mini Pastel de Vento": [
                    "Presunto e Queijo",
                    "Queijo",
                    "Carne",
                ],
            },
        },
        {
            "slug": "combos",
            "name": "Combos Especiais",
            "description": "Combos prontos para celebrar com praticidade e sabor.",
            "icon": "🎁",
            "price_from": None,
            "options": {
                "Escolha o Combo": [
                    "Combo Surpresinha (Mini naked cake + 4 docinhos + 10 salgadinhos + coca lata + caixa presenteável)",
                    "Combo Só um Bolinho (Caseirinho + 30 salgadinhos + 12 brigadeiros + guaraná 1L)",
                    "Combo Surpresa (Naked cake 500g + 12 docinhos + 30 salgados + refrigerante 1L + vela foguetinho)",
                ],
            },
        },
        {
            "slug": "kit-festa",
            "name": "Kits Festa",
            "description": "Kit completo: bolo + doces + salgados + bebida para sua festa.",
            "icon": "🎊",
            "price_from": None,
            "options": {
                "Escolha o Kit": [
                    "Kit PP (3 pessoas: bolo 500g + 15 docinhos + 30 salgados fritos + refri 600ml)",
                    "Kit P (10 pessoas: bolo 1kg + 25 docinhos + 50 salgados fritos + refri 2L)",
                    "Kit M (15 pessoas: bolo 1,5kg + 30 docinhos + 100 salgados fritos + refri 2L)",
                    "Kit G (20 pessoas: bolo 2kg + 50 docinhos + 100 salgados fritos + 2 refris 2L)",
                ],
                "Acréscimos (opcional)": [
                    "Sem acréscimos",
                    "Topo de Bolo Trabalhado",
                    "Suporte no Bolo de Andar",
                    "Decoração com Flores Naturais",
                    "Papel de Arroz",
                    "Ganache",
                ],
            },
        },
    ]

    for cat_data in categories:
        options = cat_data.pop("options")
        category = Category(**cat_data)
        db.session.add(category)
        db.session.flush()

        for option_group_key, choices in options.items():
            for choice in choices:
                product = Product(
                    category_id=category.id,
                    option_group=option_group_key,
                    name=choice,
                )
                db.session.add(product)

    db.session.commit()
