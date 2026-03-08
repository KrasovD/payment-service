from app.repositories.interfaces import OrderRepository, PaymentRepository
from app.models.order import Order
from app.models.payment import Payment


class InMemoryOrderRepository(OrderRepository):

    def __init__(self):
        self.orders: dict[int, Order] = {}

    def get_by_id(self, order_id: int) -> Order | None:
        return self.orders.get(order_id)

    def save(self, order: Order) -> None:
        self.orders[order.id] = order

    def clear(self):
        self.orders.clear()


class InMemoryPaymentRepository(PaymentRepository):

    def __init__(self):
        self.payments: dict[int, Payment] = {}
        self._id = 1

    def get_by_id(self, payment_id: int) -> Payment | None:
        return self.payments.get(payment_id)

    def save(self, payment: Payment) -> Payment:
        if payment.id is None:
            payment.id = self._id
            self._id += 1
        self.payments[payment.id] = payment
        return payment

    def clear(self):
        self.payments.clear()
        self._id = 1