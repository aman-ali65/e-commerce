class ECommerceError(Exception):
    """Base exception for all e-commerce errors."""
    pass


class OutOfStockError(ECommerceError):
    """Raised when requested quantity exceeds available stock."""
    pass


class ProductNotFoundError(ECommerceError):
    """Raised when a product ID doesn't exist in the catalog."""
    pass


class UserNotFoundError(ECommerceError):
    """Raised when a user ID doesn't exist."""
    pass


class InvalidQuantityError(ECommerceError):
    """Raised when quantity is zero or negative."""
    pass


class PaymentFailedError(ECommerceError):
    """Raised on payment processing failures."""
    pass
