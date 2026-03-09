from decimal import Decimal
from enum import Enum
from typing import List

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentType(str, Enum):
    CASH = "cash"
    ACQUIRING = "acquiring"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    REFUNDED = "refunded"
    FAILED = "failed"

class OperationType(str, Enum):
    DEPOSIT = "deposit"
    REFUND = "refund"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    type: Mapped[PaymentType] = mapped_column(
        SqlEnum(PaymentType),
        default=PaymentType.CASH,
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
    )

    order: Mapped["Order"] = relationship(back_populates="payments")
    operations: Mapped[List["PaymentOperation"]] = relationship(back_populates="payment", lazy="selectin")


class PaymentOperation(Base):
    __tablename__ = "payment_operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)

    type: Mapped[OperationType] = mapped_column(
        SqlEnum(OperationType),
        default=OperationType.DEPOSIT,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    payment: Mapped["Payment"] = relationship(back_populates="operations")