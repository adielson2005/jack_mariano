import os
import socket
from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template, session, redirect, request, Response
from app import create_app

app = create_app()

@app.route("/")
def index():
    return render_template("index.html")

_ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
_ADMIN_HASH = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "jackmariano2024"))


@app.route("/painel")
def admin_panel():
    if not session.get("admin_logged_in"):
        return redirect("/painel/login")
    return render_template("admin.html")


@app.route("/painel/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect("/painel")
    error = None
    if request.method == "POST":
        attempts = session.get("_login_attempts", 0)
        if attempts >= 5:
            error = "Muitas tentativas. Feche o navegador e tente novamente."
        else:
            user = request.form.get("username", "").strip()
            pwd  = request.form.get("password", "")
            if user == _ADMIN_USER and check_password_hash(_ADMIN_HASH, pwd):
                session.clear()
                session["admin_logged_in"] = True
                session.permanent = True
                return redirect("/painel")
            session["_login_attempts"] = attempts + 1
            error = "Usuário ou senha incorretos."
    return render_template("admin_login.html", error=error)


@app.route("/painel/logout")
def admin_logout():
    session.clear()
    return redirect("/painel/login")


# ── Produção / infra ──────────────────────────────────────────────────────────

@app.route("/health")
def health():
    """Health check para load balancers e plataformas de deploy."""
    from app import db
    try:
        db.session.execute(db.text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}, status


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
    app.run(host="0.0.0.0", port=port, debug=True)
