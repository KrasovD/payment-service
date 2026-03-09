import pytest
from decimal import Decimal
from unittest.mock import Mock

from app.models.payment import PaymentType
from app.models.bank_payment import BankPaymentStatus
from app.models.order import OrderPaymentStatus
from app.services.exceptions import (
    BankPaymentNotFoundError,
    BankPaymentError,
)


def test_create_acquiring_payment_calls_bank_and_saves_bank_payment_id(
    bank_payment_service,
    bank_api_client_mock,
    order_1000,
):
    bank_api_client_mock.acquiring_start.return_value = "bank-12345"

    payment = bank_payment_service.create_acquiring_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
    )

    assert payment.order_id == order_1000.id
    assert payment.amount == Decimal("300.00")
    assert payment.type == PaymentType.ACQUIRING

    bank_payment = bank_payment_service.get_by_payment_id(payment.id)

    assert bank_payment.bank_payment_id == "bank-12345"
    assert bank_payment.status == BankPaymentStatus.PENDING
    assert bank_payment.payment_id == payment.id

    bank_api_client_mock.acquiring_start.assert_called_once()

def test_create_acquiring_payment_raises_when_bank_start_fails(
    bank_payment_service,
    bank_api_client_mock,
    order_1000,
):
    bank_api_client_mock.acquiring_start.side_effect = BankPaymentError()

    with pytest.raises(BankPaymentError):
        bank_payment_service.create_acquiring_payment(
            order_id=order_1000.id,
            amount=Decimal("300.00"),
        )

    assert order_1000.payment_status == OrderPaymentStatus.UNPAID

def test_sync_payment_deposits_money_when_bank_reports_paid(
    bank_payment_service,
    bank_api_client_mock,
    order_1000,
):
    bank_api_client_mock.acquiring_start.return_value = "bank-12345"

    payment = bank_payment_service.create_acquiring_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
    )

    bank_api_client_mock.acquiring_check.return_value = Mock(
        bank_payment_id="bank-12345",
        amount=Decimal("300.00"),
        status="paid",
        paid_at=None,
    )

    bank_payment = bank_payment_service.sync_payment(payment.id)

    assert bank_payment.status == BankPaymentStatus.PAID
    assert bank_payment.payment_id == payment.id
    assert order_1000.payment_status == OrderPaymentStatus.PARTIALLY_PAID


def test_sync_payment_does_not_deposit_when_bank_reports_pending(
    bank_payment_service,
    bank_api_client_mock,
    order_1000,
):
    bank_api_client_mock.acquiring_start.return_value = "bank-12345"

    payment = bank_payment_service.create_acquiring_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
    )
    payment.bank_payment_id = "bank-12345"
    payment.bank_status = "pending"

    bank_api_client_mock.acquiring_check.return_value = Mock(
        bank_payment_id="bank-12345",
        amount=Decimal("300.00"),
        status="pending",
        paid_at=None,
    )

    synced_payment = bank_payment_service.sync_payment(payment.id)

    assert synced_payment.status == "pending"
    assert order_1000.payment_status == OrderPaymentStatus.UNPAID


def test_sync_payment_marks_failed_when_bank_reports_failed(
    bank_payment_service,
    bank_api_client_mock,
    order_1000,
):
    bank_api_client_mock.acquiring_start.return_value = "bank-12345"

    payment = bank_payment_service.create_acquiring_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
    )

    bank_api_client_mock.acquiring_check.return_value = Mock(
        bank_payment_id="bank-12345",
        amount=Decimal("300.00"),
        status="failed",
        paid_at=None,
    )

    bank_payment = bank_payment_service.sync_payment(payment.id)

    assert bank_payment.status == BankPaymentStatus.FAILED
    assert order_1000.payment_status == OrderPaymentStatus.UNPAID

def test_sync_payment_is_idempotent_when_paid_status_checked_twice(
    bank_payment_service,
    bank_api_client_mock,
    order_1000,
):
    bank_api_client_mock.acquiring_start.return_value = "bank-12345"

    payment = bank_payment_service.create_acquiring_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
    )

    bank_api_client_mock.acquiring_check.return_value = Mock(
        bank_payment_id="bank-12345",
        amount=Decimal("300.00"),
        status="paid",
        paid_at=None,
    )

    first_bank_payment = bank_payment_service.sync_payment(payment.id)
    second_bank_payment = bank_payment_service.sync_payment(payment.id)

    refreshed_payment = bank_payment_service.get_by_payment_id(payment.id)

    assert first_bank_payment.status == BankPaymentStatus.PAID
    assert second_bank_payment.status == BankPaymentStatus.PAID
    assert order_1000.payment_status == OrderPaymentStatus.PARTIALLY_PAID

def test_sync_payment_raises_when_bank_payment_not_found(
    bank_payment_service,
    bank_api_client_mock,
    order_1000,
):
    bank_api_client_mock.acquiring_start.return_value = "bank-12345"

    payment = bank_payment_service.create_acquiring_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
    )

    bank_api_client_mock.acquiring_check.side_effect = BankPaymentNotFoundError()

    with pytest.raises(BankPaymentNotFoundError):
        bank_payment_service.sync_payment(payment.id)