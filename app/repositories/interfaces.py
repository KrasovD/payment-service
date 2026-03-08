from app.models.order import Order
from app.models.payment import Payment

class OrderRepository:
    def get_by_id(self, order_id: int) -> Order | None:
        ...

    def save(self, order: Order) -> None:
        ...


class PaymentRepository:
    def get_by_id(self, payment_id: int) -> Payment | None:
        ...

    def save(self, payment: Payment) -> Payment:
        ...