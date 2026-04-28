import pdb
import os
import logging

from utils.exceptions import (
    OutOfStockError, InvalidQuantityError,
    ProductNotFoundError, UserNotFoundError, PaymentFailedError,
)
from patterns.singleton import Logger

logger = Logger()
std_logger = logging.getLogger(__name__)

TRANSACTIONS_FILE = "data/transactions.txt"


# ── Product helpers ───────────────────────────────────────────────────────────

def buy_product(product, qty: int):
    """
    Reduce product stock by qty.
    Raises InvalidQuantityError or OutOfStockError on failure.
    """
    if qty <= 0:
        raise InvalidQuantityError(f"Quantity must be positive, got {qty}.")

    assert isinstance(qty, int), "Quantity must be an integer."

    if product.stock < qty:
        raise OutOfStockError(
            f"'{product.name}' has only {product.stock} units left; "
            f"you requested {qty}."
        )

    product.update_stock(-qty)
    logger.info(f"Sold {qty}x '{product.name}'. Remaining stock: {product.stock}")


def find_product(catalog: list, product_id: int):
    """
    Find a product by ID from a catalog list.
    Raises ProductNotFoundError if not found.
    """
    for product in catalog:
        if product.product_id == product_id:
            return product
    raise ProductNotFoundError(
        f"Product with ID {product_id} not found in catalog."
    )


def find_user(users: list, user_id: int):
    """
    Find a user by ID from a users list.
    Raises UserNotFoundError if not found.
    """
    for user in users:
        if user.id == user_id:
            return user
    raise UserNotFoundError(
        f"User with ID {user_id} not found."
    )


def safe_checkout(order):
    """
    Attempt order checkout; wraps bare exceptions into PaymentFailedError.
    """
    try:
        order.payment_method.pay(order.total)
        from models.order import OrderStatus
        order.status = OrderStatus.CONFIRMED
    except Exception as exc:
        raise PaymentFailedError(
            f"Payment failed for order #{order.order_id}: {exc}"
        ) from exc


# ── Text-file transaction log (Step 9 — new.txt) ─────────────────────────────

def save_transaction(owner: str, amount: float, action: str):
    """Append a transaction line to data/transactions.txt (plain text persistence)."""
    os.makedirs("data", exist_ok=True)
    with open(TRANSACTIONS_FILE, "a", encoding="utf-8") as f:
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {owner} | {action.upper()} | Rs.{amount:,.0f}\n")
    logger.info(f"Transaction logged → {owner} {action} Rs.{amount:,.0f}")


# ── Transfer with assert + logging (Step 8 — new.txt) ────────────────────────

def transfer(product, qty: int):
    """
    Perform a stock transfer with:
      - assert  : validates qty is a positive int
      - logging : records every successful transfer
      - raises  : OutOfStockError / InvalidQuantityError on failure
    """
    assert isinstance(qty, int) and qty > 0, \
        f"Transfer qty must be a positive integer, got {qty!r}"

    try:
        buy_product(product, qty)
        std_logger.info("Transferred %dx '%s'. Remaining stock: %d",
                        qty, product.name, product.stock)
        save_transaction(product.name, product.price * qty, "transfer")
    except (OutOfStockError, InvalidQuantityError) as exc:
        std_logger.error("Transfer failed: %s", exc)
        raise


# ── Discount calculation with pdb hook (Step 8 — new.txt) ────────────────────

def calculate_discount(price: float, rate: float) -> float:
    """
    Calculate discounted price.
    Call with ECOM_DEBUG=1 env var to activate pdb step-through.

    Usage:
        ECOM_DEBUG=1 python -c "from utils.helpers import calculate_discount; calculate_discount(1000, 0.1)"
    """
    if os.environ.get("ECOM_DEBUG") == "1":
        pdb.set_trace()            # debugger activates only when env var is set
    assert 0 <= rate <= 1, f"Discount rate must be between 0 and 1, got {rate}"
    discounted = price * (1 - rate)
    std_logger.info("Discount applied: Rs.%.0f → Rs.%.0f (%.0f%% off)",
                    price, discounted, rate * 100)
    return discounted


# ── Display helpers ───────────────────────────────────────────────────────────

def print_banner(title: str, width: int = 50):
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_section(title: str):
    print(f"\n{'-'*45}")
    print(f"  >> {title}")
    print(f"{'-'*45}")
