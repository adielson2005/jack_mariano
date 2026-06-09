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
        _migrate_db()
        _seed_data()

    return app


def _migrate_db():
    """Adiciona colunas novas a tabelas existentes (idempotente — PostgreSQL)."""
    from sqlalchemy import text

    stmts = [
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS catalog_version VARCHAR(10)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_cpf VARCHAR(20)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_birthdate VARCHAR(10)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(10) DEFAULT 'retirada'",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_address TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_neighborhood VARCHAR(150)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_recipient VARCHAR(150)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_contact VARCHAR(50)",
    ]

    with db.engine.connect() as conn:
        # Ampliar whatsapp — sintaxe segura no PostgreSQL
        try:
            conn.execute(text(
                "ALTER TABLE orders ALTER COLUMN customer_whatsapp TYPE VARCHAR(50)"
            ))
            conn.commit()
        except Exception:
            conn.rollback()

        for stmt in stmts:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                conn.rollback()


# Versão do catálogo — suba este número sempre que alterar produtos/opções.
# O sistema vai apagar e recriar o catálogo automaticamente no próximo deploy.
_CATALOG_VERSION = "v17"


def _seed_data():
    from app.models import Category, Product

    # Verifica se o catálogo já está na versão atual
    first = Category.query.first()
    if first and getattr(first, "catalog_version", None) == _CATALOG_VERSION:
        return

    # Apaga catálogo antigo (OrderItem usa category_slug como string — sem FK,
    # portanto pedidos existentes NÃO são afetados)
    Product.query.delete()
    Category.query.delete()
    db.session.commit()

    _TRAD = [
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
    ]

    _ESP = [
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
    ]

    _SUPER = [
        "Pistache",
        "Pistache com Geléia de Morango",
        "Creme com Castanha do Pará",
    ]

    _FRITOS = [
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
    ]

    _ASSADOS = [
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
    ]

    categories = [
        # ── Bolos ────────────────────────────────────────────────────────────
        {
            "slug": "bolo-tradicional",
            "name": "Bolo Tradicional",
            "description": "Bolo personalizado com recheios tradicionais, massa e decoração à escolha.",
            "icon": "🎂",
            "price_from": "a partir de R$90",
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "Quilo|a partir de R$ 90,00": ["500g", "700g", "1kg", "1,5kg", "2kg", "2,5kg", "3kg", "4kg"],
                "1º Sabor": [*_TRAD],
                "2º Sabor": ["Sem segundo sabor", *_TRAD],
                "Massa": ["Branca (Baunilha)", "Chocolate", "Red Velvet"],
                "Decoração": [
                    "Sem decoração", "Chantilly", "Pasta Americana", "Morangos",
                    "Brigadeiro Festa Tradicional", "Macarrons", "Arte a Mão",
                ],
                "Topo de Bolo": [
                    "Sem topo", "Impresso Simples", "Impresso Detalhado",
                    "3D em Camadas Trabalhado", "Flores Artificiais", "Bolo de Andar", "Papel de Arroz",
                ],
            },
        },
        {
            "slug": "bolo-especial",
            "name": "Bolo Especial",
            "description": "Recheios especiais cremosos com frutas e combinações diferenciadas.",
            "icon": "🎂",
            "price_from": "a partir de R$100",
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "Quilo|a partir de R$ 100,00": ["500g", "700g", "1kg", "1,5kg", "2kg", "2,5kg", "3kg", "4kg"],
                "1º Sabor": [*_ESP],
                "2º Sabor": ["Sem segundo sabor", *_ESP],
                "Massa": ["Branca (Baunilha)", "Chocolate", "Red Velvet"],
                "Decoração": [
                    "Sem decoração", "Chantilly", "Pasta Americana", "Morangos",
                    "Brigadeiro Festa Tradicional", "Macarrons", "Arte a Mão",
                ],
                "Topo de Bolo": [
                    "Sem topo", "Impresso Simples", "Impresso Detalhado",
                    "3D em Camadas Trabalhado", "Flores Artificiais", "Bolo de Andar", "Papel de Arroz",
                ],
            },
        },
        {
            "slug": "bolo-super",
            "name": "Bolo Super Especial",
            "description": "Recheios premium: pistache, castanha do Pará e combinações exclusivas.",
            "icon": "🎂",
            "price_from": "a partir de R$130",
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "Quilo|a partir de R$ 130,00": ["500g", "700g", "1kg", "1,5kg", "2kg", "2,5kg", "3kg", "4kg"],
                "1º Sabor": [*_SUPER],
                "2º Sabor": ["Sem segundo sabor", *_SUPER],
                "Massa": ["Branca (Baunilha)", "Chocolate", "Red Velvet"],
                "Decoração": [
                    "Sem decoração", "Chantilly", "Pasta Americana", "Morangos",
                    "Brigadeiro Festa Tradicional", "Macarrons", "Arte a Mão",
                ],
                "Topo de Bolo": [
                    "Sem topo", "Impresso Simples", "Impresso Detalhado",
                    "3D em Camadas Trabalhado", "Flores Artificiais", "Bolo de Andar", "Papel de Arroz",
                ],
            },
        },
        # ── Doces ────────────────────────────────────────────────────────────
        {
            "slug": "doces",
            "name": "Doces Tradicionais",
            "description": "Brigadeiros gourmet, copinhos, brownies, pipoca e coloridos artesanais.",
            "icon": "🍫",
            "price_from": None,
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "Brigadeiro Gourmet|R$ 180,00 o cento": [
                    "Nenhum",
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
                "Brigadeiro Gourmet Especial|R$ 250,00 o cento": [
                    "Nenhum",
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
                "Copinho de Chocolate (Branco ou ao Leite)|R$ 4,90 un": [
                    "Nenhum",
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
                "Copinho de Acrílico 30ml|R$ 4,90 un": [
                    "Nenhum",
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
                "Mini Brownie|R$ 3,90 un": [
                    "Nenhum",
                    "Morango",
                    "Brigadeiro",
                    "Ninho Morango",
                    "Ninho",
                    "Oreo",
                    "Pistache",
                    "Ninho Uva",
                ],
                "Mini Trufa|R$ 2,90 un": [
                    "Nenhum",
                    "Castanha Triturada",
                    "Brigadeiro",
                    "Coco",
                    "Cupuaçu",
                    "Ninho",
                ],
                "Doce Fino|a partir de R$ 3,50 un": [
                    "Nenhum",
                    "Camafeu Nozes",
                    "Surpresa de Damasco",
                    "Surpresa de Castanha de Caju",
                    "Macarrom",
                    "Bem Casado com Tag",
                ],
                "Pipoca Gourmet|R$ 6,90 gr": [
                    "Nenhum",
                    "Ninho",
                    "Chocolate",
                    "Oreo",
                    "Ovomaltine",
                ],
                "Coloridos ou Carimbados|R$ 220,00 o cento": [
                    "Nenhum",
                    "Carimbo Dourado com Sabor Ninho",
                ],
            },
        },
        {
            "slug": "doces-finos",
            "name": "Doces Finos",
            "description": "Trufas artesanais e doces finos elegantes para eventos especiais.",
            "icon": "💎",
            "price_from": None,
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "Mini Trufa|R$ 2,90 un": [
                    "Nenhum",
                    "Castanha Triturada",
                    "Brigadeiro",
                    "Coco",
                    "Cupuaçu",
                    "Ninho",
                ],
                "Doce Fino|a partir de R$ 3,50 un": [
                    "Nenhum",
                    "Camafeu Nozes",
                    "Surpresa de Damasco",
                    "Surpresa de Castanha de Caju",
                    "Macarrom",
                    "Bem Casado com Tag",
                ],
            },
        },
        # ── Salgados ─────────────────────────────────────────────────────────
        {
            "slug": "salgados-fritos",
            "name": "Salgados Fritos",
            "description": "Coxinha, croquete, bolinha, pastel e muito mais — até 5 sabores diferentes.",
            "icon": "🍗",
            "price_from": None,
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "1º Sabor": [*_FRITOS],
                "2º Sabor": ["Nenhum", *_FRITOS],
                "3º Sabor": ["Nenhum", *_FRITOS],
                "4º Sabor": ["Nenhum", *_FRITOS],
                "5º Sabor": ["Nenhum", *_FRITOS],
            },
        },
        {
            "slug": "salgados-assados",
            "name": "Salgados Assados",
            "description": "Esfiras, enroladinhos, delícias assadas, mini pizza e empadinhas.",
            "icon": "🥧",
            "price_from": None,
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "Mini Pastel de Vento": [
                    "Nenhum",
                    "Presunto e Queijo",
                    "Queijo",
                    "Carne",
                ],
                "1º Sabor": [*_ASSADOS],
                "2º Sabor": ["Nenhum", *_ASSADOS],
                "3º Sabor": ["Nenhum", *_ASSADOS],
                "4º Sabor": ["Nenhum", *_ASSADOS],
                "5º Sabor": ["Nenhum", *_ASSADOS],
                "Empadinhas": ["Nenhum", "Frango", "Palmito"],
            },
        },
        {
            "slug": "salgados-finos",
            "name": "Salgados Finos",
            "description": "Canudínhos, canapés, torteletes e barquetes para eventos elegantes.",
            "icon": "🥂",
            "price_from": None,
            "catalog_version": _CATALOG_VERSION,
            "options": {
                "Canudinho|R$ 140,00 o cento": [
                    "Nenhum",
                    "Creme de Milho e Requeijão",
                    "Frango",
                    "Carne Seca",
                    "Carne Moída Cremosa",
                ],
                "Canapés|de R$ 140,00 a R$ 490,00/cento": [
                    "Nenhum",
                    "Frango — R$ 140,00/cento",
                    "Carne Seca com Banana — R$ 200,00/cento",
                    "Creme de Milho com Tomate — R$ 250,00/cento",
                    "Camarão — R$ 490,00/cento",
                    "Camarão e Cream Cheese — R$ 490,00/cento",
                    "Cream Cheese c/ Geléia de Pimenta — R$ 490,00/cento",
                ],
                "Tortelete|de R$ 150,00 a R$ 290,00/cento": [
                    "Nenhum",
                    "Frango — R$ 150,00/cento",
                    "Patê de Atum — R$ 160,00/cento",
                    "Carne Seca com Banana — R$ 220,00/cento",
                    "Salmão com Cream Cheese — R$ 220,00/cento",
                    "Frutas — R$ 290,00/cento",
                ],
                "Barquete|de R$ 250,00 a R$ 390,00/cento": [
                    "Nenhum",
                    "Frango com Tomate Seco — R$ 250,00/cento",
                    "Milho — R$ 250,00/cento",
                    "Carne Seca com Banana — R$ 290,00/cento",
                    "Camarão com Creme — R$ 390,00/cento",
                ],
            },
        },
        # ── Combos e Kits ────────────────────────────────────────────────────
        {
            "slug": "combos",
            "name": "Combos Especiais",
            "description": "Combos prontos para celebrar com praticidade e sabor.",
            "icon": "🎁",
            "price_from": None,
            "catalog_version": _CATALOG_VERSION,
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
            "icon": "🎈",
            "price_from": None,
            "catalog_version": _CATALOG_VERSION,
            "options": {
                # ── Kit ──────────────────────────────────────────────────────
                "Escolha o Kit": [
                    "Kit PP — 3 pessoas (bolo 500g + topo simples + 15 docinhos + 30 salgados fritos + refri 600ml)",
                    "Kit P — 10 pessoas (bolo 1kg + topo simples + 25 docinhos + 50 salgados fritos + refri 2L)",
                    "Kit M — 15 pessoas (bolo 1,5kg + topo simples + 30 docinhos + 100 salgados fritos + refri 2L)",
                    "Kit G — 20 pessoas (bolo 2kg + topo simples + 50 docinhos + 100 salgados fritos + 2 refris 2L)",
                ],
                # ── Bolo ─────────────────────────────────────────────────────
                "Massa": ["Branca (Baunilha)", "Chocolate", "Red Velvet"],
                "Recheio Tradicional — 1º Sabor": [*_TRAD],
                "Recheio Tradicional — 2º Sabor": ["Sem segundo sabor", *_TRAD],
                "Recheio Especial — 1º Sabor": [*_ESP],
                "Recheio Especial — 2º Sabor": ["Sem segundo sabor", *_ESP],
                "Recheio Super Especial — 1º Sabor": [*_SUPER],
                "Recheio Super Especial — 2º Sabor": ["Sem segundo sabor", *_SUPER],
                "Decoração": [
                    "Sem decoração", "Chantilly", "Pasta Americana", "Morangos",
                    "Brigadeiro Festa Tradicional", "Macarrons", "Arte a Mão",
                ],
                "Topo de Bolo": [
                    "Sem topo", "Impresso Simples", "Impresso Detalhado",
                    "3D em Camadas Trabalhado", "Flores Artificiais", "Bolo de Andar", "Papel de Arroz",
                ],
                # ── Salgados ─────────────────────────────────────────────────
                "Salgados Fritos — 1º Sabor": [*_FRITOS],
                "Salgados Fritos — 2º Sabor": ["Nenhum", *_FRITOS],
                "Salgados Fritos — 3º Sabor": ["Nenhum", *_FRITOS],
                "Salgados Fritos — 4º Sabor": ["Nenhum", *_FRITOS],
                "Salgados Fritos — 5º Sabor": ["Nenhum", *_FRITOS],
                "Mini Pastel de Vento": ["Nenhum", "Presunto e Queijo", "Queijo", "Carne"],
                "Salgados Assados": ["Nenhum", *_ASSADOS],
                "Empadinhas": ["Nenhum", "Frango", "Palmito"],
                "Salgados Finos": ["Nenhum", "Canapés", "Tortelete", "Barquete"],
                # ── Doces ────────────────────────────────────────────────────
                "Brigadeiro Gourmet": [
                    "Nenhum", "Brigadeiro Tradicional", "Brigadeiro com Amendoim",
                    "Beijinho", "Limão", "Delícia de Amendoim", "Churros", "Maracujá",
                    "Dois Amores", "Napolitano", "Olho de Sogra", "Beijinho Queimado",
                    "Morango", "Cajuzinho",
                ],
                "Brigadeiro Gourmet Especial": [
                    "Nenhum", "Ferreiro Rocher", "Ninho com Nutella", "Brigadeiro M&M",
                    "Brigadeiro com Granulado Meio Amargo", "Café", "Cappuccino",
                    "Ninho M&M", "Castanha do Pará", "Surpresa de Uva",
                ],
                "Copinho de Chocolate (Branco ou ao Leite)": [
                    "Nenhum", "Morango", "Brigadeiro", "Ninho Morango", "Ninho Cereja",
                    "Ninho Damasco", "Oreo", "Pistache", "Ninho Uva",
                    "Pedacim do Céu Pêssego", "Ninho com Nozes",
                ],
                "Copinho de Acrílico 30ml": [
                    "Nenhum", "Morango", "Brigadeiro", "Ninho Morango", "Ninho Cereja",
                    "Ninho Damasco", "Oreo", "Ninho Uva", "Pedacim do Céu Pêssego", "Napolitano",
                ],
                "Mini Brownie": [
                    "Nenhum", "Morango", "Brigadeiro", "Ninho Morango", "Ninho",
                    "Oreo", "Pistache", "Ninho Uva",
                ],
                "Mini Trufa": ["Nenhum", "Castanha Triturada", "Brigadeiro", "Coco", "Cupuaçu", "Ninho"],
                "Doce Fino": [
                    "Nenhum", "Camafeu Nozes", "Surpresa de Damasco",
                    "Surpresa de Castanha de Caju", "Macarrom", "Bem Casado com Tag",
                ],
                "Pipoca Gourmet": ["Nenhum", "Ninho", "Chocolate", "Oreo", "Ovomaltine"],
                # ── Extras ───────────────────────────────────────────────────
                "Acréscimos": [
                    "Sem acréscimos", "Topo de Bolo Trabalhado", "Suporte no Bolo de Andar",
                    "Decoração com Flores Naturais", "Papel de Arroz", "Ganache",
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
