from functools import wraps
from flask import Blueprint, jsonify, request, session
from app import db
from app.models import Order, STATUS_LABELS
from app.utils import build_client_link, build_admin_link, build_help_link

admin_bp = Blueprint("admin", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({
                'error': 'Sessão expirada. Faça login novamente.',
                'login_url': '/painel/login'
            }), 401
        return f(*args, **kwargs)
    return decorated

VALID_STATUSES = list(STATUS_LABELS.keys())


# ── List orders ───────────────────────────────────────────────────────────────

@admin_bp.get("/orders")
@login_required
def list_orders():
    status   = request.args.get("status")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    query = Order.query.order_by(Order.created_at.desc())
    if status and status in VALID_STATUSES:
        query = query.filter_by(status=status)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "orders":       [o.to_dict(include_items=False) for o in pagination.items],
        "total":        pagination.total,
        "pages":        pagination.pages,
        "current_page": page,
        "per_page":     per_page,
    })


# ── Get single order ──────────────────────────────────────────────────────────

@admin_bp.get("/orders/<int:order_id>")
@login_required
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())


# ── Update status ─────────────────────────────────────────────────────────────

@admin_bp.patch("/orders/<int:order_id>/status")
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    data  = request.get_json(silent=True) or {}

    new_status = data.get("status")
    if new_status not in VALID_STATUSES:
        return jsonify({
            "error": "Status invalido",
            "valid_statuses": VALID_STATUSES,
        }), 422

    order.status = new_status
    if "admin_notes" in data:
        order.admin_notes = data["admin_notes"].strip() or None

    db.session.commit()
    return jsonify({
        "message": f"Status atualizado para '{STATUS_LABELS[new_status]}'",
        "order":   order.to_dict(),
    })


# ── Delete order ──────────────────────────────────────────────────────────────

@admin_bp.delete("/orders/<int:order_id>")
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": f"Pedido #{order_id} removido."})


# ── WhatsApp links (admin-only) ───────────────────────────────────────────────

@admin_bp.get("/whatsapp/<int:order_id>")
@login_required
def whatsapp_links(order_id):
    """Retorna links wa.me para o admin contatar o cliente e para o cliente."""
    order = Order.query.get_or_404(order_id)
    return jsonify({
        "client_link": build_client_link(order),
        "admin_link":  build_admin_link(order),
        "help_link":   build_help_link(),
        "shop_number": "+55 94984239253",
    })


# ── Stats ─────────────────────────────────────────────────────────────────────

@admin_bp.get("/stats")
@login_required
def stats():
    from sqlalchemy import func
    from app.models import OrderItem

    total      = Order.query.count()
    by_status  = (
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status).all()
    )
    by_category = (
        db.session.query(OrderItem.category_name, func.sum(OrderItem.quantity))
        .group_by(OrderItem.category_name).all()
    )

    return jsonify({
        "total_orders": total,
        "by_status":    {STATUS_LABELS.get(s, s): count for s, count in by_status},
        "by_category":  {name: int(qty) for name, qty in by_category},
    })
