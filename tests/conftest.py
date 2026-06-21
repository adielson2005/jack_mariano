import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("METRICS_DB_PATH", "/tmp/test_metrics.db")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "testpass123")


@pytest.fixture(scope="session")
def app_fixture():
    from app import create_app, db
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        db.create_all()
        _seed_test_data(db)
        yield app


def _seed_test_data(db):
    from app.models import Category, Product
    if Category.query.count() > 0:
        return
    cat = Category(
        name="Bolos",
        slug="bolos",
        icon="🎂",
        active=True,
        options={},
        base_price=50.0,
    )
    db.session.add(cat)
    db.session.flush()
    db.session.add(Product(name="Bolo de chocolate", category_id=cat.id, active=True))
    db.session.commit()


@pytest.fixture
def client(app_fixture):
    return app_fixture.test_client()


@pytest.fixture
def sample_order_payload():
    import datetime
    future = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
    return {
        "customer_name": "Maria Teste",
        "customer_whatsapp": "(94) 99999-0000",
        "delivery_type": "retirada",
        "pickup_date": future,
        "pickup_time": "10:00",
        "items": [
            {
                "category_slug": "bolos",
                "category_name": "Bolos",
                "selections": {"sabor": "chocolate"},
                "quantity": 1,
                "unit_price": 50.0,
            }
        ],
    }
