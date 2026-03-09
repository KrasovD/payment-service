import pytest
from decimal import Decimal

from app.models.payment import PaymentType
from app.services.exceptions import (
    InvalidDepositAmountError,
    OverpaymentError,
)


def test_deposit_increases_paid_amount(payment_service, order_1000):
    
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("600.00"),
        payment_type=PaymentType.CASH,
    )

    updated_payment = payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("250.00"),
    )

    assert sum(op.amount for op in updated_payment.operations) == Decimal("250.00")


def test_deposit_updates_order_status_to_partially_paid(payment_service, order_1000):
    
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("1000.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("400.00"),
    )

    assert order_1000.payment_status == "partially_paid"


def test_deposit_updates_order_status_to_paid(payment_service, order_1000):
    
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("1000.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("1000.00"),
    )

    assert order_1000.payment_status == "paid"


def test_cannot_deposit_more_than_payment_amount(payment_service, order_1000):
    
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("500.00"),
        payment_type=PaymentType.CASH,
    )

    with pytest.raises(InvalidDepositAmountError):
        payment_service.deposit_payment(
            payment_id=payment.id,
            amount=Decimal("600.00"),
        )


def test_can_make_partial_deposits(payment_service, order_1000):
    
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("700.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("200.00"),
    )
    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("300.00"),
    )

    assert sum(op.amount for op in payment.operations) == Decimal("500.00")
    assert order_1000.payment_status == "partially_paid"


def test_cannot_deposit_if_total_deposit_would_exceed_payment_amount(payment_service, order_1000):
    
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("500.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("300.00"),
    )

    with pytest.raises(InvalidDepositAmountError):
        payment_service.deposit_payment(
            payment_id=payment.id,
            amount=Decimal("250.00"),
        )


def test_cannot_overpay_order_via_payment_creation(payment_service, order_1000):
    

    payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("600.00"),
        payment_type=PaymentType.CASH,
    )
    
    with pytest.raises(OverpaymentError):
        payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("500.00"),
        payment_type=PaymentType.ACQUIRING,
    )


def test_exact_full_deposit_marks_order_as_paid(payment_service, order_1000):
    

    payment_1 = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("400.00"),
        payment_type=PaymentType.CASH,
    )
    payment_2 = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("600.00"),
        payment_type=PaymentType.ACQUIRING,
    )

    payment_service.deposit_payment(
        payment_id=payment_1.id,
        amount=Decimal("400.00"),
    )
    payment_service.deposit_payment(
        payment_id=payment_2.id,
        amount=Decimal("600.00"),
    )

    assert order_1000.payment_status == "paid"
    assert sum(op.amount for op in payment_1.operations) == Decimal("400.00")
    assert sum(op.amount for op in payment_2.operations) == Decimal("600.00")