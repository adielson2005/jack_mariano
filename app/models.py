from datetime import datetime
from app import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(10))
    active = db.Column(db.Boolean, default=True)
    price_from = db.Column(db.String(100), nullable=True)
    catalog_version = db.Column(db.String(10), nullable=True)

    products = db.relationship("Product", backref="category", lazy=True)

    def to_dict(self):
        grouped = {}
        for p in self.products:
            raw_group = p.option_group  # may contain "Name|price_info"
            if "|" in raw_group:
                group_name, price_info = raw_group.split("|", 1)
            else:
                group_name, price_info = raw_group, None

            if group_name not in grouped:
                grouped[group_name] = {"price_info": price_info, "items": []}
            grouped[group_name]["items"].append(
                {"id": p.id, "name": p.name, "active": p.active}
            )
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "active": self.active,
            "price_from": self.price_from,
            "options": grouped,
        }


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    option_group = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean, default=True)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Customer data
    customer_name      = db.Column(db.String(150), nullable=False)
    customer_whatsapp  = db.Column(db.String(50),  nullable=False)
    customer_cpf       = db.Column(db.String(20))
    customer_birthdate = db.Column(db.String(10))

    # Scheduling
    pickup_date = db.Column(db.String(10), nullable=False)
    pickup_time = db.Column(db.String(5),  nullable=False)

    # Delivery type: "retirada" | "entrega"
    delivery_type         = db.Column(db.String(10), default="retirada")
    delivery_address      = db.Column(db.Text)
    delivery_neighborhood = db.Column(db.String(150))
    delivery_recipient    = db.Column(db.String(150))
    delivery_contact      = db.Column(db.String(50))

    allergies = db.Column(db.Text)
    notes     = db.Column(db.Text)

    # Status: pending | confirmed | in_progress | ready | cancelled
    status = db.Column(db.String(20), default="pending")
    admin_notes = db.Column(db.Text)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_items=True):
        data = {
            "id":                    self.id,
            "created_at":            self.created_at.strftime("%d/%m/%Y %H:%M"),
            "customer_name":         self.customer_name,
            "customer_whatsapp":     self.customer_whatsapp,
            "customer_cpf":          self.customer_cpf,
            "customer_birthdate":    self.customer_birthdate,
            "pickup_date":           self.pickup_date,
            "pickup_time":           self.pickup_time,
            "delivery_type":         self.delivery_type or "retirada",
            "delivery_address":      self.delivery_address,
            "delivery_neighborhood": self.delivery_neighborhood,
            "delivery_recipient":    self.delivery_recipient,
            "delivery_contact":      self.delivery_contact,
            "allergies":             self.allergies,
            "notes":                 self.notes,
            "admin_notes":           self.admin_notes,
            "status":                self.status,
            "status_label":          STATUS_LABELS.get(self.status, self.status),
        }
        data["item_count"] = len(self.items)
        if include_items:
            data["items"] = [i.to_dict() for i in self.items]
        return data


STATUS_LABELS = {
    "pending": "Aguardando confirmação",
    "confirmed": "Confirmado",
    "in_progress": "Em produção",
    "ready": "Pronto para retirada",
    "cancelled": "Cancelado",
}


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    category_slug = db.Column(db.String(50), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    selections = db.Column(db.Text)  # JSON string of {option_group: choice}
    item_notes = db.Column(db.Text)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "category_slug": self.category_slug,
            "category_name": self.category_name,
            "quantity": self.quantity,
            "selections": json.loads(self.selections) if self.selections else {},
            "item_notes": self.item_notes,
        }
