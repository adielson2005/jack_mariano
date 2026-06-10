import base64 as _b64
import json
import re
from datetime import date as date_type
from flask import Blueprint, Response, jsonify, redirect, request
from app import db
from app.models import Category, Order, OrderItem, CatalogImage
from app.utils import build_client_link, build_help_link

api_bp = Blueprint("api", __name__)

# Limites de tamanho dos campos de texto
_MAX_NAME      = 150
_MAX_PHONE     = 50
_MAX_CPF       = 20
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

    delivery_type = data.get("delivery_type", "retirada")

    order = Order(
        customer_name         = data["customer_name"].strip()[:_MAX_NAME],
        customer_whatsapp     = _clean_phone(data["customer_whatsapp"])[:_MAX_PHONE],
        customer_cpf          = data.get("customer_cpf", "").strip()[:_MAX_CPF] or None,
        customer_birthdate    = data.get("customer_birthdate", "").strip()[:_MAX_DATE] or None,
        pickup_date           = data["pickup_date"].strip(),
        pickup_time           = data["pickup_time"].strip(),
        delivery_type         = delivery_type,
        delivery_address      = data.get("delivery_address",      "").strip()[:_MAX_TEXT]  or None,
        delivery_neighborhood = data.get("delivery_neighborhood", "").strip()[:_MAX_TEXT]  or None,
        delivery_recipient    = data.get("delivery_recipient",    "").strip()[:_MAX_NAME]  or None,
        delivery_contact      = _clean_phone(data.get("delivery_contact", ""))[:_MAX_PHONE] or None,
        allergies             = data.get("allergies", "").strip()[:_MAX_TEXT]  or None,
        notes                 = data.get("notes",     "").strip()[:_MAX_NOTES] or None,
        bolo_photo_data       = data.get("bolo_photo_data") or None,
        topo_photo_data       = data.get("topo_photo_data") or None,
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

    base_url = request.url_root.rstrip("/")
    return jsonify({
        "message": "Pedido recebido! Entraremos em contato via WhatsApp em breve. 🧁",
        "whatsapp_link": build_client_link(order, base_url),
        "order_id": order.id,
    }), 201


# ── Catalog Images (público — galeria de referências para o cliente) ─────────

@api_bp.get("/catalog-images")
def get_catalog_images():
    tag   = request.args.get("tag", "").strip()
    query = CatalogImage.query.filter_by(active=True)
    if tag:
        query = query.filter_by(category_tag=tag)
    images = query.order_by(CatalogImage.created_at.desc()).all()
    return jsonify([img.to_dict() for img in images])


# ── Fotos de pedido (público — usadas nos links do WhatsApp) ─────────────────

@api_bp.get("/orders/<int:order_id>/photo/<which>")
def order_photo(order_id, which):
    """Serve a foto de referência de bolo ou topo de um pedido."""
    order = Order.query.get_or_404(order_id)
    data = None
    if which == "bolo":
        data = order.bolo_photo_data
    elif which == "topo":
        data = order.topo_photo_data
    if not data:
        return jsonify({"error": "Foto não encontrada"}), 404
    # Se for data URL base64: decodifica e serve como imagem
    if data.startswith("data:"):
        try:
            header, b64data = data.split(",", 1)
            mime = header.split(":")[1].split(";")[0]
            img_bytes = _b64.b64decode(b64data)
            return Response(img_bytes, mimetype=mime,
                            headers={"Cache-Control": "public, max-age=31536000"})
        except Exception:
            return jsonify({"error": "Erro ao decodificar imagem"}), 500
    # URL externa (galeria): redireciona
    return redirect(data)


# ── WhatsApp ajuda (público — somente link de dúvidas para a loja) ───────────

@api_bp.get("/help-link")
def help_link():
    """Retorna apenas o link de ajuda genérico da loja."""
    return jsonify({"help_link": build_help_link()})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_order(data: dict) -> list[str]:
    errors = []

    # Campos obrigatórios básicos
    required = {
        "customer_name":     "Nome completo",
        "customer_whatsapp": "WhatsApp",
        "pickup_date":       "Data",
        "pickup_time":       "Horário",
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

    # Tipo de entrega
    delivery_type = data.get("delivery_type", "retirada")
    if delivery_type not in ("retirada", "entrega"):
        errors.append("Tipo de entrega inválido")

    # Campos obrigatórios para entrega
    if delivery_type == "entrega":
        if not data.get("delivery_address", "").strip():
            errors.append("Endereço é obrigatório para entrega")
        if not data.get("delivery_neighborhood", "").strip():
            errors.append("Bairro é obrigatório para entrega")

    # Formato de data: YYYY-MM-DD e deve ser >= hoje (timezone do cliente pode variar)
    pickup_date = data["pickup_date"].strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pickup_date):
        errors.append("Data em formato inválido (esperado YYYY-MM-DD)")
    else:
        try:
            y, m, d = pickup_date.split("-")
            pedido_date = date_type(int(y), int(m), int(d))
            if pedido_date < date_type.today():
                errors.append("A data deve ser hoje ou uma data futura")
        except ValueError:
            errors.append("Data inválida")

    # Formato de hora: HH:MM
    pickup_time = data["pickup_time"].strip()
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", pickup_time):
        errors.append("Horário em formato inválido (esperado HH:MM)")

    return errors


def _clean_phone(phone: str) -> str:
    return "".join(c for c in str(phone) if c.isdigit() or c in "+-() ")
