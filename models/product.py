from abc import ABC, abstractmethod


class Product(ABC):
    """Base Product class with encapsulation."""

    def __init__(self, product_id: int, name: str, price: float, stock: int):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._stock = stock

    # ---------- Properties ----------

    @property
    def product_id(self):
        return self._product_id

    @property
    def name(self):
        return self._name

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value < 0:
            raise ValueError("Price cannot be negative.")
        self._price = value

    @property
    def stock(self):
        return self._stock

    # ---------- Methods ----------

    def update_stock(self, qty: int):
        """Add or remove stock. Use negative qty to reduce."""
        if self._stock + qty < 0:
            raise ValueError("Stock cannot go below zero.")
        self._stock += qty

    @abstractmethod
    def category(self) -> str:
        pass

    def __str__(self):
        return (f"[{self.category()}] {self._name} | "
                f"Price: Rs.{self._price:,.0f} | Stock: {self._stock}")

    def to_dict(self):
        return {
            "product_id": self._product_id,
            "name": self._name,
            "price": self._price,
            "stock": self._stock,
            "category": self.category()
        }


# ---------- Concrete Product Classes ----------

class Electronics(Product):
    def __init__(self, product_id, name, price, stock, warranty_years=1):
        super().__init__(product_id, name, price, stock)
        self.warranty_years = warranty_years

    def category(self):
        return "Electronics"

    def to_dict(self):
        d = super().to_dict()
        d["warranty_years"] = self.warranty_years
        return d


class Clothing(Product):
    def __init__(self, product_id, name, price, stock, size="M"):
        super().__init__(product_id, name, price, stock)
        self.size = size

    def category(self):
        return "Clothing"

    def to_dict(self):
        d = super().to_dict()
        d["size"] = self.size
        return d


class Grocery(Product):
    def __init__(self, product_id, name, price, stock, expiry_date="N/A"):
        super().__init__(product_id, name, price, stock)
        self.expiry_date = expiry_date

    def category(self):
        return "Grocery"

    def to_dict(self):
        d = super().to_dict()
        d["expiry_date"] = self.expiry_date
        return d


class GeneralProduct(Product):
    """Fallback for any category that doesn't have a specialized class."""
    def __init__(self, product_id, name, price, stock, category_name="General", **kwargs):
        super().__init__(product_id, name, price, stock)
        self._custom_category = category_name
        self.info = kwargs  # Store any extra data as a dict

    def category(self):
        return self._custom_category.capitalize()

    def to_dict(self):
        d = super().to_dict()
        d.update(self.info)
        return d
