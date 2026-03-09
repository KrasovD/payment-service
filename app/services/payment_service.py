from decimal import Decimal
from app.models.order import Order, OrderPaymentStatus
from app.models.payment import (
    Payment,
    PaymentType,
    PaymentOperation,
    OperationType,
    PaymentStatus,
)
from app.services.exceptions import (
    OverpaymentError,
    InvalidDepositAmountError,
    InvalidRefundAmountError,
    OrderNotFoundError,
    PaymentNotFoundError,
    InvalidAmountError,
)
from app.repositories.order_repository import SqlAlchemyOrderRepository
from app.repositories.payment_repository import (
    SqlAlchemyPaymentRepository,
    SqlAlchemyPaymentOperationRepository,
)


class PaymentService:
    def __init__(
        self,
        order_repo: SqlAlchemyOrderRepository,
        payment_repo: SqlAlchemyPaymentRepository,
        payment_operation_repo: SqlAlchemyPaymentOperationRepository,
    ) -> None:
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.payment_operation_repo = payment_operation_repo

    def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        payment_type: PaymentType,
    ) -> Payment:
        self._ensure_positive_amount(amount)
        
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError()

        current_total = sum(payment.amount for payment in order.payments)
        if current_total + amount > order.amount:
            raise OverpaymentError()

        payment = Payment(
            order_id=order.id,
            amount=amount,
            type=payment_type,
            status=PaymentStatus.PENDING,
        )

        payment = self.payment_repo.save(payment)
        order.payments.append(payment)
        return payment

    def deposit_payment(self, payment_id: int, amount: Decimal) -> Payment:
        self._ensure_positive_amount(amount)

        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()

        order = self.order_repo.get_by_id(payment.order_id)
        if order is None:
            raise OrderNotFoundError()

        if self._total_operations(payment) + amount > payment.amount:
            raise InvalidDepositAmountError()

        total_paid = self._total_paid(order)
        if total_paid + amount > order.amount:
            raise OverpaymentError()

        operation = PaymentOperation(
            payment_id=payment_id,
            type=OperationType.DEPOSIT,
            amount=amount,
        )

        self.payment_operation_repo.save(operation)
        payment.operations.append(operation)
        payment.status = self._resolve_payment_status(payment)
        payment = self.payment_repo.save(payment)

        self._update_order_status(order)
        self.order_repo.save(order)

        return payment

    def refund_payment(self, payment_id: int, amount: Decimal) -> Payment:
        self._ensure_positive_amount(amount)
                                     
        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()

        order = self.order_repo.get_by_id(payment.order_id)
        if order is None:
            raise OrderNotFoundError()

        if self._total_operations(payment) - amount < Decimal("0"):
            raise InvalidRefundAmountError()

        operation = PaymentOperation(
            payment_id=payment_id,
            type=OperationType.REFUND,
            amount=amount,
        )

        self.payment_operation_repo.save(operation)
        payment.operations.append(operation)
        payment.status = self._resolve_payment_status(payment)
        payment = self.payment_repo.save(payment)

        self._update_order_status(order)
        self.order_repo.save(order)

        return payment

    def get_paid_amount(self, payment_id: int) -> Decimal:
        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        return self._total_operations(payment)

    def mark_failed(self, payment_id: int) -> Payment:
        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()

        payment.status = PaymentStatus.FAILED
        return self.payment_repo.save(payment)

    def _total_paid(self, order: Order) -> Decimal:
        return sum(
            self._total_operations(payment)
            for payment in order.payments
        )

    def _total_operations(self, payment: Payment) -> Decimal:
        if payment.operations is None:
            return Decimal("0.00")

        return sum(
            operation.amount if operation.type == OperationType.DEPOSIT else -operation.amount
            for operation in payment.operations
        )

    def _update_order_status(self, order: Order) -> None:
        total_paid = self._total_paid(order)

        if total_paid == Decimal("0.00"):
            order.payment_status = OrderPaymentStatus.UNPAID
        elif total_paid < order.amount:
            order.payment_status = OrderPaymentStatus.PARTIALLY_PAID
        else:
            order.payment_status = OrderPaymentStatus.PAID

    def _resolve_payment_status(self, payment: Payment) -> PaymentStatus:
        operations = self.payment_operation_repo.list_by_payment_id(payment.id)
        if not operations:
            return PaymentStatus.PENDING

        total = sum(
            op.amount if op.type == OperationType.DEPOSIT else -op.amount for op in operations
        )

        if total == Decimal("0"):
            had_deposit = any(
                op.type == OperationType.DEPOSIT for op in operations)
            had_refund = any(
                op.type == OperationType.REFUND for op in operations)
            if had_deposit and had_refund:
                return PaymentStatus.REFUNDED
            return PaymentStatus.PENDING

        return PaymentStatus.SUCCEEDED

    def _ensure_positive_amount(self, amount: Decimal) -> None:
        if amount <= Decimal("0"):
            raise InvalidAmountError()
