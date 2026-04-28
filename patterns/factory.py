from models.product import Electronics, Clothing, Grocery


class ProductFactory:
    """Factory Pattern — creates the right Product subclass from a type string."""

    _registry = {
        "electronics": Electronics,
        "clothing": Clothing,
        "grocery": Grocery,
    }

    @staticmethod
    def create_product(type_: str, product_id: int, name: str, price: float,
                       stock: int, **kwargs):
        """
        type_    : 'electronics' | 'clothing' | 'grocery'
        **kwargs : extra fields (warranty_years, size, expiry_date, etc.)
        """
        type_ = type_.lower()
        cls = ProductFactory._registry.get(type_)
        if cls is None:
            raise ValueError(
                f"Unknown product type '{type_}'. "
                f"Valid types: {list(ProductFactory._registry.keys())}"
            )
        return cls(product_id, name, price, stock, **kwargs)

    @staticmethod
    def register(type_: str, cls):
        """Extend the factory with new product types at runtime."""
        ProductFactory._registry[type_.lower()] = cls
