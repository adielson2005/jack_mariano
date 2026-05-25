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

    app.register_blueprint(api_bp, url_prefix="/api")

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
            "price_from": "a partir de R$90,00/kg",
            "options": {
                "Massa": [
                    "Branca (Baunilha)",
                    "Chocolate",
                ],
                "Recheio Tradicional|R$90,00/kg": [
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
                "Recheio Especial|R$100,00/kg": [
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
                "Recheio Super Especial|R$110,00/kg": [
                    "Pistache",
                    "Pistache com Geléia de Morango",
                    "Creme com Castanha do Pará",
                ],
                "Decoração|a partir de R$15,00": [
                    "Sem decoração",
                    "Morangos (R$15,00)",
                    "Brigadeiro Festa (R$1,80/un)",
                    "Macarrons (R$7,50/un)",
                    "Arte a Mão (a partir de R$20,00)",
                ],
                "Topo de Bolo|a partir de R$15,00": [
                    "Sem topo",
                    "Papel de Arroz (a partir de R$15,00)",
                    "Impresso Simples (a partir de R$25,00)",
                    "Impresso Detalhado (a partir de R$30,00)",
                    "3D em Camadas (a partir de R$45,00)",
                    "Flores Artificiais (a partir de R$70,00)",
                    "Bolo de Andar (R$30,00/andar)",
                ],
            },
        },
        {
            "slug": "doces",
            "name": "Doces",
            "description": "Doces finos artesanais, brigadeiros gourmet, trufas e muito mais.",
            "icon": "🍬",
            "price_from": "a partir de R$2,90/un",
            "options": {
                "Tipo e Preço|preços variam": [
                    "Brigadeiro Gourmet — R$180,00/cento",
                    "Brigadeiro Gourmet Especial — R$250,00/cento",
                    "Copinho de Chocolate (Branco ou ao Leite) — R$4,90/un",
                    "Copinho de Acrílico 30ml",
                    "Mini Brownie — R$3,90/un",
                    "Mini Trufa — R$2,90/un",
                    "Doce Fino (preços variados)",
                    "Pipoca Gourmet — R$6,90/gr",
                    "Coloridos ou Carimbados — R$220,00/cento",
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
            "price_from": "a partir de R$85,00/cento",
            "options": {
                "Tipo e Preço|preços variam": [
                    "Salgados Fritos — R$85,00/cento",
                    "Salgados Assados — R$105,00/cento",
                    "Empadinhas — R$130,00/cento",
                    "Mini Pastel de Vento — R$95,00/cento",
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
            "price_from": "a partir de R$64,90",
            "options": {
                "Escolha o Combo|preços já inclusos": [
                    "Combo Surpresinha — R$64,90 (Mini naked cake + 4 docinhos + 10 salgadinhos + coca lata + caixa presenteável)",
                    "Combo Só um Bolinho — R$103,90 (Caseirinho + 30 salgadinhos + 12 brigadeiros + guaraná 1L)",
                    "Combo Surpresa — R$112,00 (Naked cake 500g + 12 docinhos + 30 salgados + refrigerante 1L + vela foguetinho)",
                ],
            },
        },
        {
            "slug": "kit-festa",
            "name": "Kits Festa",
            "description": "Kit completo: bolo + doces + salgados + bebida para sua festa.",
            "icon": "🎊",
            "price_from": "a partir de R$115,00",
            "options": {
                "Escolha o Kit|preços já inclusos": [
                    "Kit PP — R$115,00 (3 pessoas: bolo 500g + 15 docinhos + 30 salgados fritos + refri 600ml)",
                    "Kit P — R$209,00 (10 pessoas: bolo 1kg + 25 docinhos + 50 salgados fritos + refri 2L)",
                    "Kit M — R$299,00 (15 pessoas: bolo 1,5kg + 30 docinhos + 100 salgados fritos + refri 2L)",
                    "Kit G — R$395,00 (20 pessoas: bolo 2kg + 50 docinhos + 100 salgados fritos + 2 refris 2L)",
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
