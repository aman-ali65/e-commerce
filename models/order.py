from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class Order:
    """Represents a customer order."""

    # Starts at 1000; synced from DB by app.py on startup (so restarts don't overwrite)
    _order_counter = 1000

    @classmethod
    def sync_counter_from_db(cls, max_existing_id: int):
        """Call once at startup so new orders never reuse an existing order_id."""
        if max_existing_id and max_existing_id > cls._order_counter:
            cls._order_counter = max_existing_id

    def __init__(self, user, items: list, payment_method):
        """
        user          : User instance
        items         : list of (Product, quantity) tuples
        payment_method: PaymentMethod strategy instance
        """
        Order._order_counter += 1
        self.order_id = Order._order_counter
        self.user = user
        self.items = items                  # [(product, qty), ...]
        self.payment_method = payment_method
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.total = self._calculate_total()

    def _calculate_total(self) -> float:
        return sum(p.price * qty for p, qty in self.items)

    def checkout(self):
        """Process payment and confirm order."""
        self.payment_method.pay(self.total)
        self.status = OrderStatus.CONFIRMED

    def update_status(self, new_status: OrderStatus):
        self.status = new_status

    def __str__(self):
        lines = [
            f"\n{'='*45}",
            f"  ORDER #{self.order_id}  |  {self.created_at}",
            f"  Customer : {self.user.name}",
            f"  Status   : {self.status.value}",
            f"{'─'*45}"
        ]
        for product, qty in self.items:
            lines.append(f"  {product.name:<20} x{qty}  Rs.{product.price * qty:,.0f}")
        lines.append(f"{'─'*45}")
        lines.append(f"  TOTAL    : Rs.{self.total:,.0f}")
        lines.append(f"{'='*45}\n")
        return "\n".join(lines)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "user": self.user.name,
            "user_id": self.user.id,
            "items": [{"product": p.name, "qty": q, "subtotal": p.price * q}
                      for p, q in self.items],
            "total": self.total,
            "payment": type(self.payment_method).__name__,
            "status": self.status.value,
            "created_at": self.created_at
        }
