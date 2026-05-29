from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")

    db.init_app(app)
    # Permite apenas requisições da mesma origem (sem acesso cross-origin externo)
    CORS(app, resources={r"/api/*": {"origins": "*"}},
         methods=["GET", "POST"],
         allow_headers=["Content-Type"])

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
                    "Sem recheio tradicional",
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
                    "Sem recheio especial",
                    "Creme com Nozes",
                    "Creme com Ameixa",
                    "Creme com Morango Fruta",
                    "Creme com Frutas Vermelhas",
                    "Creme com Geléia de Morango",
                    "Ferreiro Rocher (brigadeiro, nutella e amendoim)",
                    "Creme com Damasco",
                    "Creme com Castanha de Caju",
                    "Sonho de Valsa (brigadeiro ou creme)",
                    "Ouro Branco",
                    "Creme com Pêssego",
                ],
                "Recheio Super Especial": [
                    "Sem recheio super especial",
                    "Pistache",
                    "Pistache com Geléia de Morango",
                    "Creme com Castanha do Pará",
                ],
                "Decoração": [
                    "Sem decoração",
                    "Morangos",
                    "Brigadeiro Festa Tradicional",
                    "Macarrons",
                    "Arte a Mão",
                ],
                "Topo de Bolo": [
                    "Sem topo",
                    "Impresso Simples",
                    "Impresso Detalhado",
                    "3D em Camadas Trabalhado",
                    "Flores Artificiais",
                    "Bolo de Andar",
                    "Papel de Arroz",
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
                "Brigadeiro Gourmet": [
                    "Não quero",
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
                ],
                "Brigadeiro Gourmet Especial": [
                    "Não quero",
                    "Ferreiro Rocher",
                    "Ninho com Nutella",
                    "Brigadeiro M&M",
                    "Brigadeiro com Granulado Meio Amargo",
                    "Café",
                    "Cappuccino",
                    "Ninho M&M",
                    "Castanha do Pará",
                    "Surpresa de Uva",
                ],
                "Copinho de Chocolate (Branco ou ao Leite)": [
                    "Não quero",
                    "Morango",
                    "Brigadeiro",
                    "Ninho Morango",
                    "Ninho Cereja",
                    "Ninho Damasco",
                    "Oreo",
                    "Pistache",
                    "Ninho Uva",
                    "Pedacim do Céu Pêssego",
                    "Ninho com Nozes",
                ],
                "Copinho de Acrílico 30ml": [
                    "Não quero",
                    "Morango",
                    "Brigadeiro",
                    "Ninho Morango",
                    "Ninho Cereja",
                    "Ninho Damasco",
                    "Oreo",
                    "Ninho Uva",
                    "Pedacim do Céu Pêssego",
                    "Napolitano",
                ],
                "Mini Brownie": [
                    "Não quero",
                    "Morango",
                    "Brigadeiro",
                    "Ninho Morango",
                    "Ninho",
                    "Oreo",
                    "Pistache",
                    "Ninho Uva",
                ],
                "Mini Trufa": [
                    "Não quero",
                    "Castanha Triturada",
                    "Brigadeiro",
                    "Coco",
                    "Cupuaçu",
                    "Ninho",
                ],
                "Doce Fino": [
                    "Não quero",
                    "Camafeu Nozes",
                    "Surpresa de Damasco",
                    "Surpresa de Castanha de Caju",
                    "Macarrom",
                    "Bem Casado com Tag",
                ],
                "Pipoca Gourmet": [
                    "Não quero",
                    "Ninho",
                    "Chocolate",
                    "Oreo",
                    "Ovomaltine",
                ],
                "Coloridos ou Carimbados": [
                    "Não quero",
                    "Carimbo Dourado com Sabor Ninho",
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
                "Salgados Fritos": [
                    "Não quero",
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
                "Salgados Assados": [
                    "Não quero",
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
                "Empadinhas": [
                    "Não quero",
                    "Frango",
                    "Palmito",
                ],
                "Mini Pastel de Vento": [
                    "Não quero",
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
                    "Combo Surpresinha (1 mini naked cake + 4 docinhos + 10 salgadinhos + 1 coca lata + 1 caixa presenteável)",
                    "Combo Só um Bolinho (1 caseirinho + 30 salgadinhos + 12 brigadeiros + 1 guaraná 1L)",
                    "Combo Surpresa (1 naked cake 500g + 12 docinhos + 30 salgados + 1 refrigerante 1L + vela foguetinho)",
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
                    "Kit PP — 3 pessoas (bolo 500g + topo simples + 15 docinhos + 30 salgados fritos + refri 600ml)",
                    "Kit P — 10 pessoas (bolo 1kg + topo simples + 25 docinhos + 50 salgados fritos + refri 2L)",
                    "Kit M — 15 pessoas (bolo 1,5kg + topo simples + 30 docinhos + 100 salgados fritos + refri 2L)",
                    "Kit G — 20 pessoas (bolo 2kg + topo simples + 50 docinhos + 100 salgados fritos + 2 refris 2L)",
                ],
                "Acréscimos": [
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
