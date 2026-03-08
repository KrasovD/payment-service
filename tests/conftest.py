import pytest
from fastapi.testclient import TestClient

from app.services.payment_service import PaymentService
from app.main import app
from tests.factories.order import make_order


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def payment_service():
    return PaymentService()


@pytest.fixture
def order_1000():
    return make_order(amount="1000.00")


@pytest.fixture
def seeded_order_1000():
    return {
        "id": 1,
        "amount": "1000.00",
        "payment_status": "unpaid",
    }