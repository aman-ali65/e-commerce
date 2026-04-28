import json
import os

PRODUCTS_FILE = "data/products.json"
ORDERS_FILE   = "data/orders.json"
USERS_FILE    = "data/users.json"


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


# ── PRODUCTS ──────────────────────────────────────────────────────────────────

def save_products(products: list):
    _ensure_dir()
    data = [p.to_dict() for p in products]
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"  ✅ Products saved → {PRODUCTS_FILE}")


def load_products_raw() -> list:
    """Return raw list of dicts (no re-hydration)."""
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_products() -> list:
    """
    Load products.json and re-hydrate every dict into the matching
    Product subclass via ProductFactory.
    Returns a list of Electronics / Clothing / Grocery instances.
    """
    # Import here to avoid circular imports at module level
    from patterns.factory import ProductFactory

    raw = load_products_raw()
    objects = []
    for d in raw:
        category = d.get("category", "").lower()
        kwargs = {}
        # Pass category-specific extra fields
        if category == "electronics" and "warranty_years" in d:
            kwargs["warranty_years"] = int(d["warranty_years"])
        elif category == "clothing" and "size" in d:
            kwargs["size"] = d["size"]
        elif category == "grocery" and "expiry_date" in d:
            kwargs["expiry_date"] = d["expiry_date"]

        try:
            obj = ProductFactory.create_product(
                category,
                int(d["product_id"]),
                d["name"],
                float(d["price"]),
                int(d["stock"]),
                **kwargs,
            )
            objects.append(obj)
        except (ValueError, KeyError) as exc:
            print(f"  ⚠️  Skipping product {d.get('name', '?')}: {exc}")
    return objects


# ── ORDERS ────────────────────────────────────────────────────────────────────

def save_orders(orders: list):
    _ensure_dir()
    data = [o.to_dict() for o in orders]
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"  ✅ Orders saved  → {ORDERS_FILE}")


def load_orders_raw() -> list:
    """Return raw list of order dicts."""
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ── USERS ─────────────────────────────────────────────────────────────────────

def save_users(users: list):
    _ensure_dir()
    data = [u.to_dict() for u in users]
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"  ✅ Users saved   → {USERS_FILE}")


def load_users_raw() -> list:
    """Return raw list of user dicts."""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
