from decimal import Decimal

from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.bank_payment import BankPayment, BankPaymentStatus
from app.services.payment_service import PaymentService
from app.services.exceptions import (
    PaymentNotFoundError, 
    BankPaymentError,
    )
from app.integrations.bank.client import BankApiClient
from app.integrations.bank.exceptions import (
    BankPaymentNotFoundError,
)
from app.repositories.payment_repository import SqlAlchemyPaymentRepository
from app.repositories.bank_payment_repository import SqlAlchemyBankPaymentRepository


class BankPaymentService:
    def __init__(
        self,
        payment_service: PaymentService,
        payment_repo: SqlAlchemyPaymentRepository,
        bank_payment_repo: SqlAlchemyBankPaymentRepository,
        bank_api_client: BankApiClient,
    ) -> None:
        self.payment_service = payment_service
        self.payment_repo = payment_repo
        self.bank_payment_repo = bank_payment_repo
        self.bank_api_client = bank_api_client

    def create_acquiring_payment(self, order_id: int, amount: Decimal) -> Payment:
        payment = self.payment_service.create_payment(
            order_id=order_id,
            amount=amount,
            payment_type=PaymentType.ACQUIRING,
        )

        try:
            bank_payment_id = self.bank_api_client.acquiring_start(
                order_number=str(order_id),
                amount=amount,
            )
        except Exception as error:
            self.payment_service.mark_failed(payment.id)
            raise BankPaymentError() from error

        bank_payment = BankPayment(
            payment_id=payment.id,
            bank_payment_id=bank_payment_id,
            status=BankPaymentStatus.PENDING,
        )
        self.bank_payment_repo.save(bank_payment)

        return payment

    def sync_payment(self, payment_id: int) -> BankPayment:
        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()

        bank_payment = self.bank_payment_repo.get_by_payment_id(payment_id)
        if bank_payment is None:
            raise BankPaymentNotFoundError()

        result = self.bank_api_client.acquiring_check(bank_payment.bank_payment_id)
        
        if result.status == "paid":
            self._sync_paid(payment_id, payment.amount, result.amount)
            bank_payment.status = BankPaymentStatus.PAID
            bank_payment.paid_at = result.paid_at

        elif result.status == "failed":
            self._sync_failed(payment_id)
            bank_payment.status = BankPaymentStatus.FAILED

        else:
            bank_payment.status = BankPaymentStatus.PENDING

        return self.bank_payment_repo.save(bank_payment)

    def mark_failed(self, payment_id: int) -> BankPayment:
        bank_payment = self.bank_payment_repo.get_by_payment_id(payment_id)
        if bank_payment is None:
            raise BankPaymentNotFoundError()

        bank_payment.status = BankPaymentStatus.FAILED
        return self.bank_payment_repo.save(bank_payment)

    def get_by_payment_id(self, payment_id: int) -> BankPayment:
        bank_payment = self.bank_payment_repo.get_by_payment_id(payment_id)
        if bank_payment is None:
            raise BankPaymentNotFoundError()
        return bank_payment
    
    def _sync_paid(self, payment_id: int, payment_amount: Decimal, bank_amount: Decimal) -> None:
        capture_amount = min(payment_amount, bank_amount)
        local_paid = self.payment_service.get_paid_amount(payment_id)

        if capture_amount > local_paid:
            self.payment_service.deposit_payment(payment_id, capture_amount - local_paid)
        elif capture_amount < local_paid:
            self.payment_service.refund_payment(payment_id, local_paid - capture_amount)

    def _sync_failed(self, payment_id: int) -> None:
        payment = self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()

        local_paid = self.payment_service.get_paid_amount(payment_id)
        if local_paid > Decimal("0"):
            self.payment_service.refund_payment(payment_id, local_paid)

        updated = self.payment_repo.get_by_id(payment_id)
        if updated and updated.status == PaymentStatus.PENDING:
            self.payment_service.mark_failed(payment_id)