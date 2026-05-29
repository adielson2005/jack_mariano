import json
import re
from datetime import date as date_type
from flask import Blueprint, jsonify, request
from app import db
from app.models import Category, Order, OrderItem
from app.utils import build_client_link, build_help_link

api_bp = Blueprint("api", __name__)

# Limites de tamanho dos campos de texto
_MAX_NAME      = 150
_MAX_PHONE     = 30
_MAX_DATE      = 10
_MAX_TIME      = 5
_MAX_TEXT      = 500
_MAX_NOTES     = 1000
_MAX_ITEMS     = 20
_MAX_SEL_KEY   = 150
_MAX_SEL_VAL   = 300


# ── Categories ───────────────────────────────────────────────────────────────

@api_bp.get("/categories")
def get_categories():
    categories = Category.query.filter_by(active=True).all()
    return jsonify([c.to_dict() for c in categories])


@api_bp.get("/categories/<slug>")
def get_category(slug):
    cat = Category.query.filter_by(slug=slug, active=True).first_or_404()
    return jsonify(cat.to_dict())


# ── Orders ───────────────────────────────────────────────────────────────────

@api_bp.post("/orders")
def create_order():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "JSON inválido"}), 400

    errors = _validate_order(data)
    if errors:
        return jsonify({"error": "Dados inválidos", "details": errors}), 422

    items_data = data.get("items", [])
    if not isinstance(items_data, list) or not items_data:
        return jsonify({"error": "O pedido deve ter ao menos um item"}), 422
    if len(items_data) > _MAX_ITEMS:
        return jsonify({"error": f"Máximo de {_MAX_ITEMS} itens por pedido"}), 422

    # Valida slugs das categorias contra o banco
    valid_slugs = {c.slug for c in Category.query.filter_by(active=True).all()}

    order = Order(
        customer_name=data["customer_name"].strip()[:_MAX_NAME],
        customer_whatsapp=_clean_phone(data["customer_whatsapp"])[:_MAX_PHONE],
        customer_birthdate=data.get("customer_birthdate", "").strip()[:_MAX_DATE] or None,
        pickup_date=data["pickup_date"].strip(),
        pickup_time=data["pickup_time"].strip(),
        allergies=data.get("allergies", "").strip()[:_MAX_TEXT] or None,
        notes=data.get("notes", "").strip()[:_MAX_NOTES] or None,
    )
    db.session.add(order)
    db.session.flush()

    for item in items_data:
        if not isinstance(item, dict):
            db.session.rollback()
            return jsonify({"error": "Item inválido no pedido"}), 422

        slug = str(item.get("category_slug", ""))[:50]
        if slug not in valid_slugs:
            db.session.rollback()
            return jsonify({"error": f"Categoria '{slug}' inválida"}), 422

        try:
            qty = max(1, min(999, int(item.get("quantity", 1))))
        except (TypeError, ValueError):
            db.session.rollback()
            return jsonify({"error": "Quantidade inválida"}), 422

        # Sanitiza e limita o tamanho das seleções
        raw_sels = item.get("selections", {})
        if not isinstance(raw_sels, dict):
            raw_sels = {}
        sels = {
            str(k)[:_MAX_SEL_KEY]: str(v)[:_MAX_SEL_VAL]
            for k, v in list(raw_sels.items())[:30]
        }

        order_item = OrderItem(
            order_id=order.id,
            category_slug=slug,
            category_name=str(item.get("category_name", slug))[:100],
            quantity=qty,
            selections=json.dumps(sels, ensure_ascii=False),
            item_notes=str(item.get("item_notes", "")).strip()[:_MAX_TEXT] or None,
        )
        db.session.add(order_item)

    db.session.commit()

    return jsonify({
        "message": "Pedido recebido! Entraremos em contato via WhatsApp em breve. 🧁",
        "whatsapp_link": build_client_link(order),
        "order_id": order.id,
    }), 201


# ── WhatsApp ajuda (público — somente link de dúvidas para a loja) ───────────

@api_bp.get("/help-link")
def help_link():
    """Retorna apenas o link de ajuda genérico da loja."""
    return jsonify({"help_link": build_help_link()})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_order(data: dict) -> list[str]:
    errors = []

    # Campos obrigatórios
    required = {
        "customer_name":     "Nome completo",
        "customer_whatsapp": "WhatsApp",
        "pickup_date":       "Data de retirada",
        "pickup_time":       "Horário de retirada",
    }
    for field, label in required.items():
        val = data.get(field, "")
        if not isinstance(val, str) or not val.strip():
            errors.append(f"{label} é obrigatório")

    if errors:
        return errors  # não adianta validar mais se faltam campos

    # Comprimento mínimo do nome
    if len(data["customer_name"].strip()) < 2:
        errors.append("Nome deve ter ao menos 2 caracteres")

    # Formato de data: YYYY-MM-DD e deve ser futuro (>= amanhã)
    pickup_date = data["pickup_date"].strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pickup_date):
        errors.append("Data de retirada em formato inválido (esperado YYYY-MM-DD)")
    else:
        try:
            y, m, d = pickup_date.split("-")
            pedido_date = date_type(int(y), int(m), int(d))
            if pedido_date <= date_type.today():
                errors.append("A data de retirada deve ser a partir de amanhã")
        except ValueError:
            errors.append("Data de retirada inválida")

    # Formato de hora: HH:MM
    pickup_time = data["pickup_time"].strip()
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", pickup_time):
        errors.append("Horário de retirada em formato inválido (esperado HH:MM)")

    return errors


def _clean_phone(phone: str) -> str:
    return "".join(c for c in str(phone) if c.isdigit() or c in "+-() ")
