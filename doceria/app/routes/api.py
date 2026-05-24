import json
from flask import Blueprint, jsonify, request
from app import db
from app.models import Category, Order, OrderItem
from app.utils import build_client_link, build_admin_link

api_bp = Blueprint("api", __name__)


# ── Categories ──────────────────────────────────────────────────────────────

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
    if not data:
        return jsonify({"error": "JSON inválido"}), 400

    errors = _validate_order(data)
    if errors:
        return jsonify({"error": "Dados inválidos", "details": errors}), 422

    items_data = data.get("items", [])
    if not items_data:
        return jsonify({"error": "O pedido deve ter ao menos um item"}), 422

    order = Order(
        customer_name=data["customer_name"].strip(),
        customer_whatsapp=_clean_phone(data["customer_whatsapp"]),
        customer_birthdate=data.get("customer_birthdate", "").strip() or None,
        pickup_date=data["pickup_date"].strip(),
        pickup_time=data["pickup_time"].strip(),
        allergies=data.get("allergies", "").strip() or None,
        notes=data.get("notes", "").strip() or None,
    )
    db.session.add(order)
    db.session.flush()

    for item in items_data:
        order_item = OrderItem(
            order_id=order.id,
            category_slug=item["category_slug"],
            category_name=item["category_name"],
            quantity=int(item.get("quantity", 1)),
            selections=json.dumps(item.get("selections", {}), ensure_ascii=False),
            item_notes=item.get("item_notes", "").strip() or None,
        )
        db.session.add(order_item)

    db.session.commit()

    return jsonify({
        "message": "Pedido recebido! Entraremos em contato via WhatsApp em breve. 🧁",
        "whatsapp_link": build_client_link(order.id, order.customer_name),
        "order": order.to_dict(),
    }), 201


@api_bp.get("/orders/<int:order_id>")
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())


# ── WhatsApp ──────────────────────────────────────────────────────────────────

@api_bp.get("/whatsapp/<int:order_id>")
def whatsapp_links(order_id):
    """Retorna link wa.me para o cliente contatar a loja."""
    order = Order.query.get_or_404(order_id)
    return jsonify({
        "client_link": build_client_link(order.id, order.customer_name),
        "admin_link":  build_admin_link(order),
        "shop_number": "+55 94984239253",
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_order(data: dict) -> list[str]:
    errors = []
    required = {
        "customer_name": "Nome completo",
        "customer_whatsapp": "WhatsApp",
        "pickup_date": "Data de retirada",
        "pickup_time": "Horário de retirada",
    }
    for field, label in required.items():
        if not data.get(field, "").strip():
            errors.append(f"{label} é obrigatório")
    return errors


def _clean_phone(phone: str) -> str:
    return "".join(c for c in phone if c.isdigit() or c in "+-() ")
