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
        type_    : 'electronics' | 'clothing' | 'grocery' (or anything else)
        **kwargs : extra fields (warranty_years, size, expiry_date, etc.)
        """
        type_ = type_.lower()
        cls = ProductFactory._registry.get(type_)
        
        # Fallback to GeneralProduct if type is unknown
        if cls is None:
            from models.product import GeneralProduct
            return GeneralProduct(product_id, name, price, stock, category_name=type_, **kwargs)
            
        return cls(product_id, name, price, stock, **kwargs)

    @staticmethod
    def register(type_: str, cls):
        """Extend the factory with new product types at runtime."""
        ProductFactory._registry[type_.lower()] = cls
