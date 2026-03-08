class OverpaymentError(Exception):
    pass


class InvalidDepositAmountError(Exception):
    pass


class InvalidRefundAmountError(Exception):
    pass

class PaymentNotFoundError():
    pass

class OrderNotFoundError():
    pass