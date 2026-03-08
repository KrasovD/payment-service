from decimal import Decimal
from enum import Enum

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrderPaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_status: Mapped[OrderPaymentStatus] = mapped_column(
        SqlEnum(OrderPaymentStatus),
        default=OrderPaymentStatus.UNPAID,
        nullable=False,
    )