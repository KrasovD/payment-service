import pytest
from decimal import Decimal

from app.models.payment import PaymentType
from app.services.exceptions import OverpaymentError, InvalidAmountError


def test_can_create_cash_payment(payment_service, order_1000):
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
        payment_type=PaymentType.CASH,
    )

    assert payment is not None
    assert payment.order_id == order_1000.id
    assert payment.amount == Decimal("300.00")
    assert payment.type == PaymentType.CASH


def test_can_create_acquiring_payment(payment_service, order_1000):
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
        payment_type=PaymentType.ACQUIRING,
    )

    assert payment is not None
    assert payment.order_id == order_1000.id
    assert payment.amount == Decimal("300.00")
    assert payment.type == PaymentType.ACQUIRING


def test_payment_types_share_same_model(payment_service, order_1000):
    cash_payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("200.00"),
        payment_type=PaymentType.CASH,
    )

    acquiring_payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("300.00"),
        payment_type=PaymentType.ACQUIRING,
    )

    assert type(cash_payment) is type(acquiring_payment)
    assert cash_payment.type == PaymentType.CASH
    assert acquiring_payment.type == PaymentType.ACQUIRING


def test_cannot_create_payment_exceeding_order_remaining_amount(payment_service, order_1000):
    payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("800.00"),
        payment_type=PaymentType.CASH,
    )

    with pytest.raises(OverpaymentError):
        payment_service.create_payment(
            order_id=order_1000.id,
            amount=Decimal("300.00"),
            payment_type=PaymentType.ACQUIRING,
        )


def test_can_create_multiple_payments_within_order_limit(payment_service, order_1000):
    first_payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("400.00"),
        payment_type=PaymentType.CASH,
    )

    second_payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("600.00"),
        payment_type=PaymentType.ACQUIRING,
    )

    assert first_payment.amount == Decimal("400.00")
    assert second_payment.amount == Decimal("600.00")
    assert first_payment.type == PaymentType.CASH
    assert second_payment.type == PaymentType.ACQUIRING

    total = sum(payment.amount for payment in order_1000.payments)
    assert total == Decimal("1000.00")

def test_cannot_create_payment_with_non_positive_amount(payment_service, order_1000):
    with pytest.raises(InvalidAmountError):
        payment_service.create_payment(
            order_id=order_1000.id,
            amount=Decimal("0"),
            payment_type=PaymentType.CASH,
        )