import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.repositories.order_repository import SqlAlchemyOrderRepository
from app.repositories.payment_repository import SqlAlchemyPaymentRepository
from app.services.payment_service import PaymentService
from app.models.order import Order, OrderPaymentStatus
from app.api.deps import get_payment_service
from app.core.config import settings
from app.main import app


engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def repos(db_session):
    order_repo = SqlAlchemyOrderRepository(db_session)
    payment_repo = SqlAlchemyPaymentRepository(db_session)
    return order_repo, payment_repo


@pytest.fixture
def payment_service(repos):
    order_repo, payment_repo = repos
    return PaymentService(order_repo, payment_repo)


@pytest.fixture
def client(db_session):

    def override_get_payment_service():
        order_repo = SqlAlchemyOrderRepository(db_session)
        payment_repo = SqlAlchemyPaymentRepository(db_session)
        return PaymentService(order_repo, payment_repo)

    app.dependency_overrides[get_payment_service] = override_get_payment_service

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def order_1000(db_session):

    order = Order(
        amount=Decimal("1000.00"),
        payment_status=OrderPaymentStatus.UNPAID,
    )

    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    return order