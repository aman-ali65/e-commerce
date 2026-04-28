from abc import ABC, abstractmethod


class PaymentMethod(ABC):
    """Strategy interface for payment."""

    @abstractmethod
    def pay(self, amount: float) -> None:
        pass

    @abstractmethod
    def method_name(self) -> str:
        pass


# ---------- Concrete Strategies ----------

class CreditCard(PaymentMethod):
    def __init__(self, card_number: str = "**** **** **** 1234"):
        self.card_number = card_number

    def pay(self, amount: float):
        print(f"  💳 Credit Card Payment")
        print(f"     Card    : {self.card_number}")
        print(f"     Amount  : Rs.{amount:,.0f}  ✅ Approved")

    def method_name(self):
        return "CreditCard"


class JazzCash(PaymentMethod):
    def __init__(self, mobile: str = "0300-0000000"):
        self.mobile = mobile

    def pay(self, amount: float):
        print(f"  📱 JazzCash Payment")
        print(f"     Mobile  : {self.mobile}")
        print(f"     Amount  : Rs.{amount:,.0f}  ✅ Sent")

    def method_name(self):
        return "JazzCash"


class EasyPaisa(PaymentMethod):
    def __init__(self, mobile: str = "0333-0000000"):
        self.mobile = mobile

    def pay(self, amount: float):
        print(f"  📱 EasyPaisa Payment")
        print(f"     Mobile  : {self.mobile}")
        print(f"     Amount  : Rs.{amount:,.0f}  ✅ Sent")

    def method_name(self):
        return "EasyPaisa"


class CashOnDelivery(PaymentMethod):
    def pay(self, amount: float):
        print(f"  💵 Cash on Delivery")
        print(f"     Amount  : Rs.{amount:,.0f}  📦 Pay on arrival")

    def method_name(self):
        return "CashOnDelivery"
