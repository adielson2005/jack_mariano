import json
import hmac as _hmac
import hashlib
from urllib.parse import quote

SHOP_WHATSAPP = "5594984239253"
SHOP_NAME     = "Jack Mariano Confeitaria"

_EMOJI = {
    "bolo-tradicional":  "🎂",
    "bolo-especial":     "🎂",
    "bolo-super":        "🎂",
    "doces":             "🍬",
    "doces-finos":       "🍫",
    "salgados-fritos":   "🍗",
    "salgados-assados":  "🥧",
    "salgados-finos":    "🥐",
    "combos":            "🎁",
    "kit-festa":         "🎉",
}


_DIV = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Mapa de ação (URL slug) → novo status
ORDER_ACTIONS = {
    "confirmar":  "confirmed",
    "producao":   "in_progress",
    "pronto":     "ready",
    "cancelar":   "cancelled",
}


def make_order_token(order_id: int, secret: str) -> str:
    """Token HMAC-SHA256 (24 chars) que autentica ações públicas de pedido."""
    key = f"jm-action:{secret}".encode("utf-8")
    msg = str(order_id).encode("utf-8")
    return _hmac.new(key, msg, hashlib.sha256).hexdigest()[:24]


def verify_order_token(order_id: int, token: str, secret: str) -> bool:
    """Retorna True se o token é válido para o pedido."""
    try:
        return _hmac.compare_digest(make_order_token(order_id, secret), token)
    except (TypeError, ValueError):
        return False


def build_client_link(order, base_url: str = None, secret: str = None) -> str:
    """
    Link que o cliente abre após confirmar o pedido.
    O WhatsApp já abre com a mensagem completa pré-preenchida
    apontando para o número da loja — basta apertar Enviar.
    """
    lines = []
    for item in order.items:
        emoji = _EMOJI.get(item.category_slug, "📦")
        lines.append(f"  {emoji} *{item.category_name}* × {item.quantity}")

        sels = json.loads(item.selections) if item.selections else {}
        for group, choice in sels.items():
            lines.append(f"     ‣ _{group}:_ {choice}")

        if item.item_notes:
            lines.append(f"     📝 _{item.item_notes}_")

    items_block = "\n".join(lines)

    delivery_type = getattr(order, "delivery_type", None) or "retirada"

    parts = [
        f"🧁 *{SHOP_NAME.upper()}*",
        _DIV,
        f"📋 *NOVO PEDIDO #{order.id}*",
        _DIV,
        f"👤 *Nome:* {order.customer_name}",
        f"📱 *WhatsApp:* {order.customer_whatsapp}",
    ]

    cpf = getattr(order, "customer_cpf", None)
    if cpf:
        parts.append(f"🪪 *CPF:* {cpf}")

    parts += [
        "",
        f"🛍️ *ITENS DO PEDIDO*",
        _DIV,
        items_block,
        _DIV,
    ]

    if delivery_type == "entrega":
        parts.append(f"🛵 *Tipo:* Entrega")
        parts.append(f"📅 *Data/hora:* {_fmt_date(order.pickup_date)} às {order.pickup_time}")
        addr = getattr(order, "delivery_address", None)
        nbhd = getattr(order, "delivery_neighborhood", None)
        recp = getattr(order, "delivery_recipient", None)
        cont = getattr(order, "delivery_contact", None)
        if addr:
            parts.append(f"📍 *Endereço:* {addr}")
        if nbhd:
            parts.append(f"🏘️ *Bairro:* {nbhd}")
        if recp:
            parts.append(f"👤 *Recebe:* {recp}")
        if cont:
            parts.append(f"📱 *Contato entrega:* {cont}")
    else:
        parts.append(f"📦 *Tipo:* Retirada na loja")
        parts.append(f"📅 *Data/hora:* {_fmt_date(order.pickup_date)} às {order.pickup_time}")

    if order.allergies:
        parts += ["", f"⚠️ *Alergias/restrições:* {order.allergies}"]
    if order.notes:
        parts += ["", f"📝 *Observações:* {order.notes}"]

    # Links das fotos de referência (apenas se o servidor estiver disponível)
    if base_url:
        if getattr(order, "bolo_photo_data", None):
            parts.append(f"📸 *Ref. bolo:* {base_url}/api/orders/{order.id}/photo/bolo")
        if getattr(order, "topo_photo_data", None):
            parts.append(f"🎨 *Ref. topo:* {base_url}/api/orders/{order.id}/photo/topo")

    parts += [
        _DIV,
        f"_Enviado pelo site — aguardo confirmação! 😊_",
    ]

    return f"https://wa.me/{SHOP_WHATSAPP}?text={quote(chr(10).join(parts))}"


def build_admin_link(order, base_url: str = None, secret: str = None) -> str:
    """Link para o admin contatar o cliente com resumo do pedido."""
    phone = _normalize_phone(order.customer_whatsapp)

    items_lines = "\n".join(
        f"  {_EMOJI.get(item.category_slug, '📦')} *{item.category_name}* × {item.quantity}"
        for item in order.items
    )

    delivery_type = getattr(order, "delivery_type", None) or "retirada"

    if delivery_type == "entrega":
        addr = getattr(order, "delivery_address", "") or ""
        nbhd = getattr(order, "delivery_neighborhood", "") or ""
        local = f"{addr}, {nbhd}".strip(", ") if addr or nbhd else ""
        schedule_parts = [
            f"🛵 *Tipo:* Entrega",
            f"📅 *Data/hora:* {_fmt_date(order.pickup_date)} às {order.pickup_time}",
        ]
        if local:
            schedule_parts.append(f"📍 *Endereço:* {local}")
    else:
        schedule_parts = [
            f"📦 *Tipo:* Retirada na loja",
            f"📅 *Data/hora:* {_fmt_date(order.pickup_date)} às {order.pickup_time}",
        ]

    schedule_block = "\n".join(schedule_parts)

    parts = [
        f"Olá, *{order.customer_name}*! 👋",
        "",
        f"Aqui é da *{SHOP_NAME}*! 🧁",
        _DIV,
        f"✅ Recebemos seu pedido *#{order.id}* e gostaríamos de confirmar os detalhes:",
        "",
        f"🛍️ *ITENS:*",
        items_lines,
        "",
        schedule_block,
        _DIV,
        f"Em breve confirmamos disponibilidade e valor. Obrigada pela preferência! 🎂",
    ]

    # Ações rápidas — visíveis apenas para o admin neste link
    if base_url and secret:
        tk = make_order_token(order.id, secret)
        parts += [
            "",
            _DIV,
            "⚡ *AÇÕES RÁPIDAS:*",
            f"  ✅ Confirmar → {base_url}/pedido/{order.id}/confirmar/{tk}",
            f"  🔧 Em produção → {base_url}/pedido/{order.id}/producao/{tk}",
            f"  🎁 Pronto → {base_url}/pedido/{order.id}/pronto/{tk}",
            f"  ❌ Cancelar → {base_url}/pedido/{order.id}/cancelar/{tk}",
            _DIV,
        ]

    return f"https://wa.me/{phone}?text={quote(chr(10).join(parts))}"


def build_help_link() -> str:
    """Link direto para a loja — botão de ajuda."""
    msg = f"Olá! Gostaria de tirar uma dúvida sobre os produtos da *{SHOP_NAME}*. 🧁"
    return f"https://wa.me/{SHOP_WHATSAPP}?text={quote(msg)}"


def _normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if not digits.startswith("55"):
        digits = "55" + digits
    return digits


def _fmt_date(date_str: str) -> str:
    if not date_str or "-" not in date_str:
        return date_str or ""
    y, m, d = date_str.split("-")
    return f"{d}/{m}/{y}"
