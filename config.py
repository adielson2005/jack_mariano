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
            "\n\n"
            "  ╔══════════════════════════════════════════════════════════╗\n"
            "  ║  DATABASE_URL não definida — aplicação não pode iniciar  ║\n"
            "  ╠══════════════════════════════════════════════════════════╣\n"
            "  ║  Localmente: crie o arquivo .env com:                    ║\n"
            "  ║    DATABASE_URL=postgresql://user:senha@host:5432/db     ║\n"
            "  ║                                                          ║\n"
            "  ║  No Render: vá em Environment e adicione DATABASE_URL.   ║\n"
            "  ║  Use neon.tech para obter um PostgreSQL gratuito.        ║\n"
            "  ╚══════════════════════════════════════════════════════════╝\n"
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
    SESSION_COOKIE_SECURE   = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True          # JS não consegue ler o cookie
    SESSION_COOKIE_SAMESITE = "Lax"        # protege contra CSRF

    # ── Monitoramento ─────────────────────────────────────────────────────────
    METRICS_DB_PATH         = os.environ.get("METRICS_DB_PATH", "/tmp/metrics.db")
    SLOW_QUERY_MS           = int(os.environ.get("SLOW_QUERY_MS", "100"))
    LOG_LEVEL               = os.environ.get("LOG_LEVEL", "INFO")
    ALERT_WEBHOOK_URL       = os.environ.get("ALERT_WEBHOOK_URL", "")
    ALERT_ERROR_RATE        = float(os.environ.get("ALERT_ERROR_RATE_THRESHOLD", "0.10"))
    ALERT_LATENCY_P95_MS    = int(os.environ.get("ALERT_LATENCY_P95_MS", "2000"))
    ALERT_ORDER_SPIKE_PM    = int(os.environ.get("ALERT_ORDER_SPIKE_PER_MINUTE", "10"))
    ALERT_COOLDOWN_SECS     = int(os.environ.get("ALERT_COOLDOWN_SECONDS", "300"))
