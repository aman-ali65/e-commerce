import pickle
import os

PICKLE_FILE = "data/products.pkl"


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


def backup_products(products: list):
    """Serialize product objects directly with pickle."""
    _ensure_dir()
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(products, f)
    print(f"  ✅ Pickle backup → {PICKLE_FILE}")


def restore_products() -> list:
    """Deserialize and return product objects."""
    if not os.path.exists(PICKLE_FILE):
        return []
    with open(PICKLE_FILE, "rb") as f:
        products = pickle.load(f)
    print(f"  ✅ Pickle loaded ← {PICKLE_FILE}  ({len(products)} products)")
    return products
