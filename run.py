import os
import socket
import time
from collections import defaultdict
from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template, session, redirect, request, Response, abort
from app import create_app

# ── Rate-limit de login por IP (server-side) ─────────────────────────────────
# Estrutura: { ip: [timestamp, timestamp, ...] }
_LOGIN_ATTEMPTS: dict = defaultdict(list)
_MAX_ATTEMPTS   = 5       # tentativas antes de bloquear
_WINDOW_SECONDS = 600     # janela de 10 minutos

app = create_app()

@app.route("/")
def index():
    return render_template("index.html")

_ADMIN_USER     = os.environ.get("ADMIN_USER", "admin")
_admin_password = os.environ.get("ADMIN_PASSWORD", "")
if not _admin_password:
    import warnings
    warnings.warn(
        "ADMIN_PASSWORD não definida — usando senha padrão insegura. "
        "Defina a variável de ambiente ADMIN_PASSWORD antes de ir a produção.",
        stacklevel=2,
    )
    _admin_password = "jackmariano2024"
_ADMIN_HASH = generate_password_hash(_admin_password)
del _admin_password  # não mantém a senha em memória desnecessariamente


@app.route("/painel")
def admin_panel():
    if not session.get("admin_logged_in"):
        return redirect("/painel/login")
    return render_template("admin.html")


def _get_ip() -> str:
    """Obtém o IP real do cliente, respeitando proxies."""
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "unknown"
    )


def _is_rate_limited(ip: str) -> bool:
    """Retorna True se o IP excedeu o limite de tentativas na janela de tempo."""
    now = time.time()
    # Remove tentativas fora da janela
    _LOGIN_ATTEMPTS[ip] = [t for t in _LOGIN_ATTEMPTS[ip] if now - t < _WINDOW_SECONDS]
    return len(_LOGIN_ATTEMPTS[ip]) >= _MAX_ATTEMPTS


def _record_attempt(ip: str) -> None:
    _LOGIN_ATTEMPTS[ip].append(time.time())


@app.route("/painel/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect("/painel")

    error = None
    if request.method == "POST":
        ip = _get_ip()
        if _is_rate_limited(ip):
            error = f"Muitas tentativas. Aguarde {_WINDOW_SECONDS // 60} minutos e tente novamente."
        else:
            user = request.form.get("username", "").strip()
            pwd  = request.form.get("password", "")
            if user == _ADMIN_USER and check_password_hash(_ADMIN_HASH, pwd):
                # Login bem-sucedido — limpa tentativas e inicia sessão
                _LOGIN_ATTEMPTS.pop(ip, None)
                session.clear()
                session["admin_logged_in"] = True
                session.permanent = True
                return redirect("/painel")
            _record_attempt(ip)
            remaining = _MAX_ATTEMPTS - len(_LOGIN_ATTEMPTS[ip])
            error = f"Usuário ou senha incorretos. ({remaining} tentativa(s) restante(s))"

    return render_template("admin_login.html", error=error)


@app.route("/painel/logout")
def admin_logout():
    session.clear()
    return redirect("/painel/login")


# ── Ações públicas de pedido via WhatsApp ─────────────────────────────────────

_ACTION_CFG = {
    "confirmar": {
        "status":  "confirmed",
        "emoji":   "✅",
        "heading": "Pedido confirmado!",
        "msg":     "Ótimo! Seu pedido foi confirmado e em breve entraremos em contato com detalhes.",
        "badge":   "Confirmado",
        "cls":     "ok",
    },
    "producao": {
        "status":  "in_progress",
        "emoji":   "🔧",
        "heading": "Em produção!",
        "msg":     "Seu pedido já está sendo preparado com muito carinho. 🧁",
        "badge":   "Em Produção",
        "cls":     "info",
    },
    "pronto": {
        "status":  "ready",
        "emoji":   "🎁",
        "heading": "Pronto para retirada!",
        "msg":     "Seu pedido está prontinho! Venha buscar quando quiser. 🎂",
        "badge":   "Pronto",
        "cls":     "ok",
    },
    "cancelar": {
        "status":  "cancelled",
        "emoji":   "❌",
        "heading": "Pedido cancelado",
        "msg":     "O pedido foi cancelado. Entre em contato pelo WhatsApp se precisar de ajuda.",
        "badge":   "Cancelado",
        "cls":     "err",
    },
}


@app.route("/pedido/<int:order_id>/<action>/<token>")
def public_order_action(order_id, action, token):
    """Rota pública — muda status do pedido via link seguro enviado pelo WhatsApp."""
    from app.utils import verify_order_token
    from app.models import Order
    from app import db

    cfg = _ACTION_CFG.get(action)
    if not cfg:
        return render_template(
            "order_action.html",
            emoji="⚠️", heading="Ação inválida", order_id=order_id,
            badge=f"'{action}' desconhecido", badge_cls="err",
            msg="Este link não corresponde a uma ação válida.",
        ), 404

    if not verify_order_token(order_id, token, app.config["SECRET_KEY"]):
        return render_template(
            "order_action.html",
            emoji="🔒", heading="Link inválido", order_id=order_id,
            badge="Não autorizado", badge_cls="err",
            msg="Este link é inválido ou não pertence a este pedido.",
        ), 403

    order = Order.query.get_or_404(order_id)

    # Idempotente: só atualiza se o status for diferente
    already_done = order.status == cfg["status"]
    if not already_done:
        order.status = cfg["status"]
        db.session.commit()

    return render_template(
        "order_action.html",
        emoji=cfg["emoji"],
        heading=cfg["heading"],
        order_id=order_id,
        badge=cfg["badge"],
        badge_cls=cfg["cls"],
        msg=cfg["msg"] if not already_done else "Status já estava atualizado.",
        customer_name=order.customer_name,
        pickup_date=order.pickup_date,
        pickup_time=order.pickup_time,
    )


# ── Produção / infra ──────────────────────────────────────────────────────────


@app.route("/robots.txt")
def robots():
    """Impede indexação do painel admin por buscadores."""
    content = (
        "User-agent: *\n"
        "Disallow: /painel/\n"
        "Disallow: /admin/\n"
        "Allow: /\n"
    )
    return Response(content, mimetype="text/plain")


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    port = 5000
    print("\n" + "="*52)
    print("  Jack Mariano Confeitaria - Servidor iniciado")
    print("="*52)
    print(f"  Local:       http://localhost:{port}")
    print(f"  Rede local:  http://{ip}:{port}")
    print("="*52)
    print("  Compartilhe 'Rede local' com qualquer")
    print("  dispositivo conectado ao mesmo Wi-Fi.\n")
    # debug=True apenas em desenvolvimento; NUNCA em produção
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
