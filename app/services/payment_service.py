from decimal import Decimal

from app.models.payment import Payment, PaymentType
from app.models.order import Order
from app.services.exceptions import (
    OverpaymentError,
    InvalidDepositAmountError,
    InvalidRefundAmountError,
    OrderNotFoundError,
    PaymentNotFoundError,
)
from app.repositories.interfaces import OrderRepository, PaymentRepository


class PaymentService:
    def __init__(self, order_repo: OrderRepository, payment_repo: PaymentRepository):
        self._next_id = 1
        self.order_repo = order_repo
        self.payment_repo = payment_repo

    def create_payment(self, order_id: int, amount: Decimal, payment_type: PaymentType) -> Payment:
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError()

        current_total = sum(p.amount for p in order.payments)

        if current_total + amount > order.amount:
            raise OverpaymentError()

        payment = Payment(
            id=self._next_id,
            order_id=order.id,
            amount=amount,
            type=payment_type,
        )
        self._next_id += 1
        payment = self.payment_repo.save(payment)
        order.payments.append(payment)
        self.order_repo.save(order)
        return payment

    def deposit_payment(self, payment_id: int, amount: Decimal) -> Payment:
        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        
        order = self.order_repo.get_by_id(payment.order_id)
        if order is None:
            raise OrderNotFoundError()
        
        if payment.deposited_amount + amount > payment.amount:
            raise InvalidDepositAmountError() 

        total_paid = self._total_paid(order)

        if total_paid + amount > order.amount:
            raise OverpaymentError()

        payment.deposited_amount += amount

        self._update_order_status(order)

        return payment

    def refund_payment(self, payment_id: int, amount: Decimal) -> Payment:
        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        
        order = self.order_repo.get_by_id(payment.order_id)
        if order is None:
            raise OrderNotFoundError()
        
        if payment.refunded_amount + amount > payment.deposited_amount:
            raise InvalidRefundAmountError()

        payment.refunded_amount += amount

        self._update_order_status(order)

        return payment

    def _total_paid(self, order: Order) -> Decimal:
        return sum(p.deposited_amount - p.refunded_amount for p in order.payments)

    def _update_order_status(self, order: Order):
        total_paid = self._total_paid(order)

        if total_paid == 0:
            order.payment_status = "unpaid"
        elif total_paid < order.amount:
            order.payment_status = "partially_paid"
        else:
            order.payment_status = "paid"