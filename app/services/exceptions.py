class OverpaymentError(Exception):
    pass


class InvalidDepositAmountError(Exception):
    pass


class InvalidRefundAmountError(Exception):
    pass

class PaymentNotFoundError(Exception):
    pass

class OrderNotFoundError(Exception):
    pass

class InvalidAmountError(Exception):
    pass

class BankApiError(Exception):
    pass

class BankPaymentNotFoundError(Exception):
    pass

class BankPaymentError(Exception):
    pass