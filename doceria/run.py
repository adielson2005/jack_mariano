import socket
from flask import render_template
from app import create_app

app = create_app()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/painel")
def admin():
    return render_template("admin.html")

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
