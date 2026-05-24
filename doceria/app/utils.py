from urllib.parse import quote

SHOP_WHATSAPP = "5594984239253"
SHOP_NAME = "Jack Mariano Confeitaria"


def build_client_link(order_id: int, customer_name: str) -> str:
    """Link para o cliente iniciar conversa com a loja após fazer pedido."""
    msg = (
        f"Olá! 👋 Sou {customer_name} e acabei de fazer o pedido *#{order_id}* "
        f"pelo site da *{SHOP_NAME}*. Aguardo a confirmação! 🧁"
    )
    return f"https://wa.me/{SHOP_WHATSAPP}?text={quote(msg)}"


def build_admin_link(order) -> str:
    """Link para o admin contatar o cliente com resumo do pedido."""
    phone = _normalize_phone(order.customer_whatsapp)
    items_lines = "\n".join(
        f"  • {item.category_name} × {item.quantity}"
        for item in order.items
    )
    msg = (
        f"Olá, *{order.customer_name}*! 👋\n\n"
        f"Aqui é da *{SHOP_NAME}*! 🧁\n"
        f"Recebemos seu pedido *#{order.id}* e gostaríamos de confirmar os detalhes.\n\n"
        f"📦 *Itens solicitados:*\n{items_lines}\n\n"
        f"📅 *Retirada:* {_fmt_date(order.pickup_date)} às {order.pickup_time}\n\n"
        f"Em breve confirmamos disponibilidade e valor. Obrigada pela preferência! 🎂"
    )
    return f"https://wa.me/{phone}?text={quote(msg)}"


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
