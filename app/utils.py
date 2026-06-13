import json
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


def build_client_link(order, base_url: str = None) -> str:
    """
    Link que o cliente abre após confirmar o pedido.
    O WhatsApp já abre com a mensagem completa pré-preenchida
    apontando para o número da loja — basta apertar Enviar.
    """
    lines = []
    for item in order.items:
        emoji = _EMOJI.get(item.category_slug, "📦")
        lines.append(f"{emoji} *{item.category_name}* × {item.quantity}")

        sels = json.loads(item.selections) if item.selections else {}
        for group, choice in sels.items():
            lines.append(f"    ‣ _{group}:_ {choice}")

        if item.item_notes:
            lines.append(f"    📝 {item.item_notes}")

    items_block = "\n".join(lines)

    delivery_type = getattr(order, "delivery_type", None) or "retirada"

    parts = [
        f"Olá, *{SHOP_NAME}*! 🧁",
        "",
        "Acabei de finalizar meu pedido pelo site.",
        "",
        f"👤 *Cliente:* {order.customer_name}",
        f"📱 *WhatsApp:* {order.customer_whatsapp}",
    ]

    cpf = getattr(order, "customer_cpf", None)
    if cpf:
        parts.append(f"🪪 *CPF:* {cpf}")

    parts += [
        "",
        "🛍️ *Itens do pedido:*",
        items_block,
        "",
    ]

    if delivery_type == "entrega":
        parts.append(f"🛵 *Entrega:* {_fmt_date(order.pickup_date)} às {order.pickup_time}")
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
            parts.append(f"📱 *Contato destinatário:* {cont}")
    else:
        parts.append(f"📅 *Retirada:* {_fmt_date(order.pickup_date)} às {order.pickup_time}")

    if order.allergies:
        parts.append(f"⚠️ *Alergias/restrições:* {order.allergies}")
    if order.notes:
        parts.append(f"📝 *Observações:* {order.notes}")

    # Links das fotos de referência (apenas se o servidor estiver disponível)
    if base_url:
        if getattr(order, "bolo_photo_data", None):
            parts.append(f"📸 *Referência de bolo:* {base_url}/api/orders/{order.id}/photo/bolo")
        if getattr(order, "topo_photo_data", None):
            parts.append(f"🎨 *Design/referência do topo:* {base_url}/api/orders/{order.id}/photo/topo")

    parts += ["", f"_Pedido #{order.id} — aguardo a confirmação! 😊_"]

    return f"https://wa.me/{SHOP_WHATSAPP}?text={quote(chr(10).join(parts))}"


def build_admin_link(order) -> str:
    """Link para o admin contatar o cliente com resumo do pedido."""
    phone = _normalize_phone(order.customer_whatsapp)
    items_lines = "\n".join(
        f"  • {item.category_name} × {item.quantity}"
        for item in order.items
    )

    delivery_type = getattr(order, "delivery_type", None) or "retirada"

    if delivery_type == "entrega":
        addr = getattr(order, "delivery_address", "") or ""
        nbhd = getattr(order, "delivery_neighborhood", "") or ""
        local = f"{addr}, {nbhd}".strip(", ") if addr or nbhd else ""
        schedule_line = f"🛵 *Entrega:* {_fmt_date(order.pickup_date)} às {order.pickup_time}"
        if local:
            schedule_line += f"\n📍 *Endereço:* {local}"
    else:
        schedule_line = f"📅 *Retirada:* {_fmt_date(order.pickup_date)} às {order.pickup_time}"

    msg = (
        f"Olá, *{order.customer_name}*! 👋\n\n"
        f"Aqui é da *{SHOP_NAME}*! 🧁\n"
        f"Recebemos seu pedido *#{order.id}* e gostaríamos de confirmar os detalhes.\n\n"
        f"📦 *Itens solicitados:*\n{items_lines}\n\n"
        f"{schedule_line}\n\n"
        f"Em breve confirmamos disponibilidade e valor. Obrigada pela preferência! 🎂"
    )
    return f"https://wa.me/{phone}?text={quote(msg)}"


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
