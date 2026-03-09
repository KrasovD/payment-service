import pytest
from decimal import Decimal

from app.models.payment import PaymentType, OperationType, PaymentStatus
from app.services.exceptions import (
    InvalidRefundAmountError,
    InvalidAmountError,
)


def test_refund_decreases_net_paid_amount(payment_service, order_1000):

    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("800.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("500.00"),
    )
    updated_payment = payment_service.refund_payment(
        payment_id=payment.id,
        amount=Decimal("200.00"),
    )

    assert sum(op.amount for op in updated_payment.operations if op.type == OperationType.REFUND) == Decimal("200.00")
    assert sum(op.amount for op in updated_payment.operations if op.type == OperationType.DEPOSIT) == Decimal("500.00")


def test_refund_updates_order_status_from_paid_to_partially_paid(payment_service, order_1000):

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

    payment_service.refund_payment(
        payment_id=payment.id,
        amount=Decimal("300.00"),
    )

    assert order_1000.payment_status == "partially_paid"


def test_full_refund_returns_order_to_unpaid(payment_service, order_1000):

    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("1000.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("1000.00"),
    )

    payment_service.refund_payment(
        payment_id=payment.id,
        amount=Decimal("1000.00"),
    )

    assert order_1000.payment_status == "unpaid"


def test_can_make_partial_refund(payment_service, order_1000):

    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("700.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("700.00"),
    )

    payment_service.refund_payment(
        payment_id=payment.id,
        amount=Decimal("200.00"),
    )

    assert sum(op.amount for op in payment.operations if op.type == OperationType.REFUND) == Decimal("200.00")
    assert order_1000.payment_status == "partially_paid"


def test_cannot_refund_more_than_deposited_amount(payment_service, order_1000):

    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("500.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("300.00"),
    )

    with pytest.raises(InvalidRefundAmountError):
        payment_service.refund_payment(
            payment_id=payment.id,
            amount=Decimal("400.00"),
        )


def test_cannot_refund_more_than_remaining_net_deposit(payment_service, order_1000):

    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("600.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("600.00"),
    )
    payment_service.refund_payment(
        payment_id=payment.id,
        amount=Decimal("250.00"),
    )

    with pytest.raises(InvalidRefundAmountError):
        payment_service.refund_payment(
            payment_id=payment.id,
            amount=Decimal("400.00"),
        )


def test_partial_refund_keeps_order_paid_if_other_payments_cover_full_amount(payment_service, order_1000):

    payment_1 = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("600.00"),
        payment_type=PaymentType.CASH,
    )
    payment_2 = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("400.00"),
        payment_type=PaymentType.ACQUIRING,
    )

    payment_service.deposit_payment(
        payment_id=payment_1.id,
        amount=Decimal("600.00"),
    )
    payment_service.deposit_payment(
        payment_id=payment_2.id,
        amount=Decimal("400.00"),
    )

    assert order_1000.payment_status == "paid"

    payment_service.refund_payment(
        payment_id=payment_1.id,
        amount=Decimal("100.00"),
    )

    assert order_1000.payment_status == "partially_paid"


def test_refund_after_partial_deposit_can_return_order_to_unpaid(payment_service, order_1000):

    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("500.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(
        payment_id=payment.id,
        amount=Decimal("300.00"),
    )
    assert order_1000.payment_status == "partially_paid"

    payment_service.refund_payment(
        payment_id=payment.id,
        amount=Decimal("300.00"),
    )

    assert sum(op.amount for op in payment.operations if op.type == OperationType.REFUND) == Decimal("300.00")
    assert order_1000.payment_status == "unpaid"

def test_full_refund_sets_payment_status_to_refunded(payment_service, order_1000):
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("400.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(payment.id, Decimal("400.00"))
    updated = payment_service.refund_payment(payment.id, Decimal("400.00"))

    assert updated.status == PaymentStatus.REFUNDED


def test_refund_rejects_non_positive_amount(payment_service, order_1000):
    payment = payment_service.create_payment(
        order_id=order_1000.id,
        amount=Decimal("400.00"),
        payment_type=PaymentType.CASH,
    )

    payment_service.deposit_payment(payment.id, Decimal("100.00"))
    with pytest.raises(InvalidAmountError):
        payment_service.refund_payment(payment.id, Decimal("0"))
