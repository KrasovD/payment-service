from fastapi import FastAPI, HTTPException

from app.api.routes.payments import router as payments_router
from app.services.exceptions import (
    InvalidDepositAmountError,
    InvalidRefundAmountError,
    OrderNotFoundError,
    OverpaymentError,
    PaymentNotFoundError,
    BankPaymentError,
    BankPaymentNotFoundError,
    InvalidAmountError,
)

app = FastAPI(title="Payment Service")


@app.exception_handler(OrderNotFoundError)
async def order_not_found_handler(request, exc):
    raise HTTPException(status_code=404, detail="Заказ не найден")


@app.exception_handler(PaymentNotFoundError)
async def payment_not_found_handler(request, exc):
    raise HTTPException(status_code=404, detail="Платёж не найден")


@app.exception_handler(OverpaymentError)
async def overpayment_handler(request, exc):
    raise HTTPException(
        status_code=409,
        detail="Общая сумма платежей не может превышать сумму заказа",
    )


@app.exception_handler(InvalidDepositAmountError)
async def invalid_deposit_handler(request, exc):
    raise HTTPException(
        status_code=400,
        detail="Сумма внесения превышает сумму платежа",
    )


@app.exception_handler(InvalidRefundAmountError)
async def invalid_refund_handler(request, exc):
    raise HTTPException(
        status_code=400,
        detail="Сумма возврата превышает внесённую сумму",
    )


@app.exception_handler(BankPaymentNotFoundError)
async def bank_payment_not_found_handler(request, exc):
    raise HTTPException(
        status_code=404,
        detail="Банковский платёж не найден",
    )


@app.exception_handler(BankPaymentError)
async def bank_payment_error_handler(request, exc):
    raise HTTPException(
        status_code=502,
        detail="Ошибка при взаимодействии с банковским сервисом",
    )

@app.exception_handler(InvalidAmountError)
async def invalid_amount_handler(request, exc):
    raise HTTPException(
        status_code=400,
        detail="Сумма должна быть больше нуля",
    )



app.include_router(payments_router)