import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    _secret = os.environ.get("SECRET_KEY", "")
    if not _secret:
        import warnings
        warnings.warn(
            "SECRET_KEY não definida — usando valor padrão inseguro. "
            "Defina SECRET_KEY como uma string aleatória longa antes de ir a produção.",
            stacklevel=2,
        )
        _secret = "doceria-secret-key-2024"
    SECRET_KEY = _secret

    # Lê a URL do banco de dados da variável de ambiente DATABASE_URL.
    # Plataformas como Heroku/Render entregam "postgres://..." — corrigimos
    # para "postgresql://..." que é o formato aceito pelo SQLAlchemy 1.4+.
    _db_url = os.environ.get("DATABASE_URL", "")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    if not _db_url:
        raise RuntimeError(
            "DATABASE_URL não definida. "
            "Crie o arquivo .env com: DATABASE_URL=postgresql://usuario:senha@localhost:5432/doceria"
        )

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # testa a conexão antes de usar do pool
        "pool_recycle": 1800,    # recicla conexões a cada 30 min
    }
    JSON_SORT_KEYS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ── Segurança de sessão (HTTPS em produção) ───────────────────────────────
    # Em produção no Render, o tráfego é sempre HTTPS.
    # SESSION_COOKIE_SECURE garante que o cookie só vai em conexões seguras.
    SESSION_COOKIE_SECURE   = os.environ.get("FLASK_ENV") != "development"
    SESSION_COOKIE_HTTPONLY = True          # JS não consegue ler o cookie
    SESSION_COOKIE_SAMESITE = "Lax"        # protege contra CSRF
