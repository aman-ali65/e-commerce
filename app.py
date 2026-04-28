"""
app.py — Flask Web Server for ECommerce
========================================

HOW TO RUN:
    python app.py
    Then open:  http://127.0.0.1:5000   ← Dashboard
                http://127.0.0.1:5000/api/products  ← raw JSON API

HOW THIS FILE IS ORGANIZED (read top to bottom):
─────────────────────────────────────────────────
  Step 1: IMPORTS         — bring in all classes and functions we need
  Step 2: BOOTSTRAP       — start DB, logger, load products into memory
  Step 3: CATALOG DICT    — PRODUCT_CATALOG = {id: Product}  (fast lookup)
  Step 4: ROUTES          — each @app.route(...) is one URL endpoint
  Step 5: ERROR HANDLERS  — convert exceptions → clean JSON error responses

API ENDPOINTS QUICK REFERENCE:
──────────────────────────────
  Products:
    GET    /api/products           → list all  (filter: ?category=&in_stock=true)
    GET    /api/products/<id>      → one product
    POST   /api/products           → add new   body: {type, product_id, name, price, stock}
    PATCH  /api/products/<id>/stock→ update stock  body: {stock: 50}
    DELETE /api/products/<id>      → delete

  Users:
    GET    /api/users              → list all
    GET    /api/users/next-id      → returns next available ID (auto-generate)
    POST   /api/users              → create user

  Orders:
    GET    /api/orders             → list all  (filter: ?status=Confirmed)
    POST   /api/orders             → place new order
    PATCH  /api/orders/<id>/status → change status

  System:
    GET    /api/stats              → dashboard numbers
    GET    /api/logs?n=80          → last N lines of app.log
    GET    /api/datafiles          → all files in data/ with size & format
    GET    /api/health             → "API is running" check
"""

import sys
import os

# ── Make sure sub-packages are importable ─────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── Flask core ────────────────────────────────────────────────────────────────
from flask import Flask, request, jsonify, abort, render_template

# ── Domain models ─────────────────────────────────────────────────────────────
from models.user  import User, UserRole
from models.order import Order, OrderStatus

# ── Design Patterns ───────────────────────────────────────────────────────────
from patterns.factory   import ProductFactory
from patterns.singleton import Logger
from patterns.strategy  import CreditCard, JazzCash, EasyPaisa, CashOnDelivery

# ── Custom exceptions ─────────────────────────────────────────────────────────
from utils.exceptions import (
    OutOfStockError, InvalidQuantityError,
    ProductNotFoundError, UserNotFoundError, PaymentFailedError,
)

# ── Helpers — only buy_product is used in Flask routes ──────────────────────
from utils.helpers import buy_product            # validates qty + decrements in-memory stock
# NOTE: find_product, find_user were removed — PRODUCT_CATALOG dict is used directly instead

# ── Persistence — SQLite (primary relational DB) ────────────────────────────
from persistence.db_handler import (
    initialize_db,           # creates products/users/orders tables if not exist
    fetch_all_products,      # used by _rebuild_catalog() to populate PRODUCT_CATALOG dict
    fetch_all_orders,        # used by list_orders, get_stats
    fetch_all_users,         # used by list_users, next_user_id, get_stats
    save_all_products_db,    # used by _persist_catalog() — bulk upsert
    save_product_db,         # used by create_product — single upsert
    save_user_db,            # used by create_user, place_order
    save_order_db,           # used by place_order
    update_product_stock,    # used by patch_product_stock, place_order (stock decrement)
    update_order_status,     # used by patch_order_status
    get_connection,          # used by delete_product for raw DELETE SQL
)
# NOTE: fetch_product_by_id removed — PRODUCT_CATALOG.get(id) is O(1) and faster

# ── Persistence — JSON (secondary backup, runs alongside SQLite) ─────────────
from persistence.json_handler import save_products  # called after every catalog write
# NOTE: load_products, load_orders_raw, load_users_raw, save_orders, save_users removed
#       Flask reads from SQLite; JSON is write-only backup from Flask's perspective

# ── Bootstrap ─────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
initialize_db()
logger = Logger()

# Sync Order ID counter from DB so restarts don't re-use existing order IDs
# (Root cause fix: _order_counter resets to 1000 on every restart → INSERT OR REPLACE
#  was silently overwriting orders 1001-1004 with new data)
_existing_orders = fetch_all_orders()
if _existing_orders:
    _max_order_id = max(o["order_id"] for o in _existing_orders)
    Order.sync_counter_from_db(_max_order_id)
    logger.info(f"Order counter synced: next order_id = {Order._order_counter + 1}")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# ═══════════════════════════════════════════════════════════════════════════════
#  CENTRAL PRODUCT CATALOG  (dict keyed by product_id)
#  Single source of truth — loaded from SQLite on startup,
#  kept in sync with SQLite + JSON on every write.
# ═══════════════════════════════════════════════════════════════════════════════

# { product_id(int): Product object }
PRODUCT_CATALOG: dict = {}

def _rebuild_catalog():
    """
    Re-hydrate every row from SQLite into a real Product object via
    ProductFactory and store it in PRODUCT_CATALOG.
    Called once at startup, and after any write operation.
    """
    global PRODUCT_CATALOG
    PRODUCT_CATALOG = {}
    for row in fetch_all_products():
        try:
            p = ProductFactory.create_product(
                row["category"].lower(),   # type string
                row["product_id"],
                row["name"],
                float(row["price"]),
                int(row["stock"]),
            )
            PRODUCT_CATALOG[p.product_id] = p
        except Exception as exc:
            logger.warning(f"Catalog: skipped product {row} — {exc}")

def _catalog_to_rows(filters: dict = None) -> list:
    """
    Convert PRODUCT_CATALOG values to list-of-dicts (same shape as DB rows).
    Optional filters: category(str), in_stock(bool), min_price(float), max_price(float)
    """
    rows = [p.to_dict() for p in PRODUCT_CATALOG.values()]
    if filters:
        if filters.get("category"):
            rows = [r for r in rows if r["category"].lower() == filters["category"].lower()]
        if filters.get("in_stock"):
            rows = [r for r in rows if r["stock"] > 0]
        if filters.get("min_price") is not None:
            rows = [r for r in rows if r["price"] >= filters["min_price"]]
        if filters.get("max_price") is not None:
            rows = [r for r in rows if r["price"] <= filters["max_price"]]
    return rows

def _persist_catalog():
    """Write entire catalog to SQLite AND JSON (keeps both formats in sync)."""
    products_list = list(PRODUCT_CATALOG.values())
    save_all_products_db(products_list)   # SQLite
    save_products(products_list)          # JSON backup

# ── Load catalog on startup ────────────────────────────────────────────────────
_rebuild_catalog()
logger.info(f"Catalog loaded: {len(PRODUCT_CATALOG)} products from SQLite")

# ── Payment method factory helper ─────────────────────────────────────────────
PAYMENT_MAP = {
    "creditcard":    lambda d: CreditCard(d.get("card_number", "**** **** **** 0000")),
    "jazzcash":      lambda d: JazzCash(d.get("mobile", "0300-0000000")),
    "easypaisa":     lambda d: EasyPaisa(d.get("mobile", "0333-0000000")),
    "cashondelivery": lambda _: CashOnDelivery(),
}

def get_payment_method(method_str: str, details: dict):
    key = method_str.lower().replace("_", "").replace(" ", "")
    factory = PAYMENT_MAP.get(key)
    if factory is None:
        abort(400, description=f"Unknown payment method '{method_str}'. "
                               f"Valid: {list(PAYMENT_MAP.keys())}")
    return factory(details)


# ═══════════════════════════════════════════════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/", methods=["GET"])
def dashboard():
    """Serve the frontend dashboard."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Quick health check."""
    return jsonify({"status": "ok", "message": "E-Commerce API is running ✅"})


# ═══════════════════════════════════════════════════════════════════════════════
#  PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/products", methods=["GET"])
def list_products():
    """
    GET /api/products  — served from in-memory PRODUCT_CATALOG dict.
    Query params: category, in_stock, min_price, max_price
    """
    filters = {
        "category":  request.args.get("category", ""),
        "in_stock":  request.args.get("in_stock", "").lower() == "true",
        "min_price": request.args.get("min_price", type=float),
        "max_price": request.args.get("max_price", type=float),
    }
    rows = _catalog_to_rows(filters)
    return jsonify({"count": len(rows), "products": rows})


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """GET /api/products/<id> — lookup from PRODUCT_CATALOG dict."""
    product = PRODUCT_CATALOG.get(product_id)
    if product is None:
        raise ProductNotFoundError(f"Product {product_id} not found.")
    return jsonify(product.to_dict())


@app.route("/api/products", methods=["POST"])
def create_product():
    """
    POST /api/products
    Creates product via ProductFactory, adds to PRODUCT_CATALOG dict,
    and persists to SQLite + JSON immediately.
    """
    data = request.get_json(force=True) or {}

    required = ("type", "product_id", "name", "price", "stock")
    missing = [k for k in required if k not in data]
    if missing:
        abort(400, description=f"Missing required fields: {missing}")

    pid = int(data["product_id"])
    if pid in PRODUCT_CATALOG:
        abort(409, description=f"Product ID {pid} already exists in catalog.")

    kwargs = {k: v for k, v in data.items()
              if k not in ("type", "product_id", "name", "price", "stock")}
    try:
        product = ProductFactory.create_product(
            data["type"], pid, data["name"],
            float(data["price"]), int(data["stock"]), **kwargs,
        )
    except ValueError as exc:
        abort(400, description=str(exc))

    # ── Add to in-memory catalog dict ────────────────────────────────────
    PRODUCT_CATALOG[product.product_id] = product

    # ── Persist to SQLite + JSON ─────────────────────────────────────────
    save_product_db(product)
    save_products(list(PRODUCT_CATALOG.values()))   # full JSON re-write

    logger.info(f"API: Created product '{product.name}' (ID={product.product_id}) "
                f"— catalog now has {len(PRODUCT_CATALOG)} products")
    return jsonify({"message": "Product created", "product": product.to_dict()}), 201


@app.route("/api/products/<int:product_id>/stock", methods=["PATCH"])
def patch_product_stock(product_id: int):
    """
    PATCH /api/products/<id>/stock
    Updates stock in PRODUCT_CATALOG dict + SQLite + JSON.
    Body: {"stock": 50}
    """
    data = request.get_json(force=True) or {}
    new_stock = data.get("stock")
    if new_stock is None or not isinstance(new_stock, int) or new_stock < 0:
        abort(400, description="'stock' must be a non-negative integer.")

    product = PRODUCT_CATALOG.get(product_id)
    if product is None:
        raise ProductNotFoundError(f"Product {product_id} not found.")

    # Update dict
    product.update_stock(new_stock - product.stock)  # delta

    # Persist
    update_product_stock(product_id, new_stock)       # SQLite
    save_products(list(PRODUCT_CATALOG.values()))      # JSON

    logger.info(f"API: Stock updated for product {product_id} → {new_stock}")
    return jsonify({"message": "Stock updated", "product_id": product_id, "new_stock": new_stock})


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id: int):
    """DELETE /api/products/<id> — removes from PRODUCT_CATALOG dict + SQLite + JSON."""
    if product_id not in PRODUCT_CATALOG:
        raise ProductNotFoundError(f"Product {product_id} not found.")

    # Remove from dict
    removed = PRODUCT_CATALOG.pop(product_id)

    # Remove from SQLite
    from persistence.db_handler import get_connection
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()

    # Re-write JSON without deleted product
    save_products(list(PRODUCT_CATALOG.values()))

    logger.info(f"API: Deleted product '{removed.name}' (ID={product_id}) "
                f"— catalog now has {len(PRODUCT_CATALOG)} products")
    return jsonify({"message": f"Product '{removed.name}' (ID={product_id}) deleted",
                   "catalog_size": len(PRODUCT_CATALOG)})


# ═══════════════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/users", methods=["GET"])
def list_users():
    """GET /api/users"""
    rows = fetch_all_users()
    return jsonify({"count": len(rows), "users": rows})


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """GET /api/users/<id>"""
    rows = fetch_all_users()
    user = next((r for r in rows if r["id"] == user_id), None)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found.")
    return jsonify(user)


@app.route("/api/users", methods=["POST"])
def create_user():
    """
    POST /api/users
    Body:
      { "id": 10, "name": "Zara Khan", "email": "zara@pk.com", "role": "Customer" }
    """
    data = request.get_json(force=True) or {}

    required = ("id", "name", "email")
    missing = [k for k in required if k not in data]
    if missing:
        abort(400, description=f"Missing required fields: {missing}")

    # Map role string → enum (default CUSTOMER)
    role_str = data.get("role", "Customer").upper()
    try:
        role = UserRole[role_str]
    except KeyError:
        abort(400, description=f"Invalid role '{data.get('role')}'. "
                               f"Valid: {[r.name for r in UserRole]}")

    user = User(
        name=data["name"],
        id=int(data["id"]),
        email=data["email"],
        role=role,
    )
    save_user_db(user)
    logger.info(f"API: Created user {user.name} (ID={user.id})")
    return jsonify({"message": "User created", "user": user.to_dict()}), 201


# ═══════════════════════════════════════════════════════════════════════════════
#  ORDERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/orders", methods=["GET"])
def list_orders():
    """
    GET /api/orders
    Query params:
      status — filter by status (Pending | Confirmed | Shipped | Delivered | Cancelled)
      user_id — filter by user
    """
    rows = fetch_all_orders()

    status_filter = request.args.get("status", "").strip()
    user_id_filter = request.args.get("user_id", type=int)

    if status_filter:
        rows = [r for r in rows if r["status"].lower() == status_filter.lower()]
    if user_id_filter is not None:
        rows = [r for r in rows if r["user_id"] == user_id_filter]

    return jsonify({"count": len(rows), "orders": rows})


@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order(order_id: int):
    """GET /api/orders/<id>"""
    rows = fetch_all_orders()
    order = next((r for r in rows if r["order_id"] == order_id), None)
    if order is None:
        abort(404, description=f"Order {order_id} not found.")
    return jsonify(order)


@app.route("/api/orders", methods=["POST"])
def place_order():
    """
    POST /api/orders
    Body:
    {
      "user": { "id": 1, "name": "Aman Khan", "email": "aman@pk.com", "role": "Customer" },
      "items": [
        { "product_id": 101, "qty": 2 },
        { "product_id": 201, "qty": 1 }
      ],
      "payment": {
        "method": "CreditCard",
        "card_number": "5399 **** **** 0001"
      }
    }
    The stock for each product is checked and decremented in the DB live.
    """
    data = request.get_json(force=True) or {}

    # ── Validate user ──────────────────────────────────────────────────────
    u_data = data.get("user")
    if not u_data or "id" not in u_data or "name" not in u_data:
        abort(400, description="'user' object with 'id' and 'name' is required.")

    role_str = u_data.get("role", "Customer").upper()
    try:
        role = UserRole[role_str]
    except KeyError:
        role = UserRole.CUSTOMER

    user = User(
        name=u_data["name"],
        id=int(u_data["id"]),
        email=u_data.get("email", ""),
        role=role,
    )

    # ── Validate items — use PRODUCT_CATALOG dict directly ────────────────
    items_data = data.get("items", [])
    if not items_data:
        abort(400, description="'items' list cannot be empty.")

    order_items = []
    for item in items_data:
        pid = item.get("product_id")
        qty = item.get("qty")

        if pid is None or qty is None:
            abort(400, description="Each item needs 'product_id' and 'qty'.")

        # Look up from central catalog dict (includes all products, not just 7)
        product = PRODUCT_CATALOG.get(int(pid))
        if product is None:
            abort(404, description=f"Product ID {pid} not found in catalog.")

        try:
            buy_product(product, int(qty))   # validates & decrements in-memory stock
        except InvalidQuantityError as exc:
            abort(400, description=str(exc))
        except OutOfStockError as exc:
            abort(409, description=str(exc))

        order_items.append((product, int(qty)))

        # Sync decremented stock back to SQLite immediately
        update_product_stock(product.product_id, product.stock)

    # ── Payment method ─────────────────────────────────────────────────────
    pay_data = data.get("payment", {})
    method_str = pay_data.get("method", "CashOnDelivery")
    payment = get_payment_method(method_str, pay_data)

    # ── Create & save order ────────────────────────────────────────────────
    order = Order(user, order_items, payment)
    try:
        order.checkout()
    except Exception as exc:
        raise PaymentFailedError(str(exc)) from exc

    save_order_db(order)
    save_user_db(user)
    # Persist entire updated catalog to JSON (all products with new stock values)
    save_products(list(PRODUCT_CATALOG.values()))

    logger.success(
        f"API: Order #{order.order_id} placed by {user.name} — "
        f"Rs.{order.total:,.0f} via {method_str}"
    )

    return jsonify({
        "message": "Order placed successfully",
        "order": order.to_dict(),
    }), 201


@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
def patch_order_status(order_id: int):
    """
    PATCH /api/orders/<id>/status
    Body: { "status": "Shipped" }
    Valid statuses: Pending | Confirmed | Shipped | Delivered | Cancelled
    """
    data  = request.get_json(force=True) or {}
    new_status = data.get("status", "")

    valid = [s.value for s in OrderStatus]
    if new_status not in valid:
        abort(400, description=f"Invalid status '{new_status}'. Valid: {valid}")

    updated = update_order_status(order_id, new_status)
    if not updated:
        abort(404, description=f"Order {order_id} not found.")

    logger.info(f"API: Order #{order_id} status → {new_status}")
    return jsonify({"message": "Status updated", "order_id": order_id, "status": new_status})


# ═══════════════════════════════════════════════════════════════════════════════
#  STATS  (dashboard widget data)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    GET /api/stats
    Returns aggregate dashboard statistics.
    """
    # Use PRODUCT_CATALOG dict (includes all products ever added via API)
    products = [p.to_dict() for p in PRODUCT_CATALOG.values()]
    orders   = fetch_all_orders()
    users    = fetch_all_users()

    total_revenue = sum(o["total"] for o in orders if o["status"] == "Confirmed")
    out_of_stock  = [p for p in products if p["stock"] == 0]

    # Revenue by payment method
    revenue_by_payment: dict[str, float] = {}
    for o in orders:
        pm = o.get("payment", "Unknown")
        revenue_by_payment[pm] = revenue_by_payment.get(pm, 0) + o["total"]

    # Orders by status
    orders_by_status: dict[str, int] = {}
    for o in orders:
        s = o.get("status", "Unknown")
        orders_by_status[s] = orders_by_status.get(s, 0) + 1

    # Products by category
    by_category: dict[str, int] = {}
    for p in products:
        c = p.get("category", "Unknown")
        by_category[c] = by_category.get(c, 0) + 1

    return jsonify({
        "totals": {
            "products": len(products),
            "orders":   len(orders),
            "users":    len(users),
            "confirmed_revenue": round(total_revenue, 2),
        },
        "out_of_stock_count": len(out_of_stock),
        "orders_by_status":   orders_by_status,
        "revenue_by_payment": {k: round(v, 2) for k, v in revenue_by_payment.items()},
        "products_by_category": by_category,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """
    GET /api/logs?n=50
    Returns the last N lines of data/app.log (default 100).
    """
    n = request.args.get("n", 100, type=int)
    log_path = os.path.join(os.path.dirname(__file__), "data", "app.log")
    if not os.path.exists(log_path):
        return jsonify({"lines": [], "message": "No log file found."})

    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()

    tail = [l.rstrip() for l in lines[-n:]]
    return jsonify({"total_lines": len(lines), "returned": len(tail), "lines": tail})


# ═══════════════════════════════════════════════════════════════════════════════
#  NEXT USER-ID  (auto-generate — fixes viva issue #1)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/users/next-id", methods=["GET"])
def next_user_id():
    """
    GET /api/users/next-id
    Returns the next available user ID (max existing + 1).
    Frontend uses this so the user never has to type an ID manually.
    """
    rows = fetch_all_users()
    next_id = max((r["id"] for r in rows), default=0) + 1
    return jsonify({"next_id": next_id})


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA FILES  (persistence explorer — fixes viva issue #2)
# ═══════════════════════════════════════════════════════════════════════════════

DATA_FILE_META = {
    "products.json":  {"format": "JSON",   "icon": "📄", "desc": "Product catalogue — human-readable, easy to edit"},
    "orders.json":    {"format": "JSON",   "icon": "📄", "desc": "All placed orders in JSON format"},
    "users.json":     {"format": "JSON",   "icon": "📄", "desc": "Registered users — JSON array"},
    "products.xml":   {"format": "XML",    "icon": "🗂️",  "desc": "Products in XML — structured markup, used in web services"},
    "products.pkl":   {"format": "Pickle", "icon": "🥒", "desc": "Binary Python object serialization (backup)"},
    "database.db":    {"format": "SQLite", "icon": "🗄️",  "desc": "Relational database — products, users, orders tables"},
    "app.log":        {"format": "Text",   "icon": "📋", "desc": "Human-readable event log written by Singleton Logger"},
    "app_logs.gz":    {"format": "GZIP",   "icon": "🗜️",  "desc": "Compressed log archive (89%+ size reduction)"},
    "transactions.txt": {"format": "Text", "icon": "📝", "desc": "Plain-text transaction ledger (Step 9 — new.txt)"},
}

@app.route("/api/datafiles", methods=["GET"])
def get_datafiles():
    """
    GET /api/datafiles
    Returns metadata about every file in the data/ directory:
    format, size, description, last modified.
    Demonstrates all persistence techniques in one endpoint.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    files = []
    if os.path.isdir(data_dir):
        for fname in sorted(os.listdir(data_dir)):
            fpath = os.path.join(data_dir, fname)
            if not os.path.isfile(fpath):
                continue
            size = os.path.getsize(fpath)
            meta = DATA_FILE_META.get(fname, {
                "format": fname.rsplit(".", 1)[-1].upper(),
                "icon": "📁",
                "desc": "Data file",
            })
            import time
            files.append({
                "name":     fname,
                "format":   meta["format"],
                "icon":     meta["icon"],
                "desc":     meta["desc"],
                "size_bytes": size,
                "size_kb":  round(size / 1024, 2),
                "modified": time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(os.path.getmtime(fpath))
                ),
            })
    return jsonify({"count": len(files), "files": files})


# ═══════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS  (convert custom exceptions → JSON responses)
# ═══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(ProductNotFoundError)
def handle_product_not_found(exc):
    return jsonify({"error": "ProductNotFoundError", "message": str(exc)}), 404

@app.errorhandler(UserNotFoundError)
def handle_user_not_found(exc):
    return jsonify({"error": "UserNotFoundError", "message": str(exc)}), 404

@app.errorhandler(OutOfStockError)
def handle_out_of_stock(exc):
    return jsonify({"error": "OutOfStockError", "message": str(exc)}), 409

@app.errorhandler(InvalidQuantityError)
def handle_invalid_quantity(exc):
    return jsonify({"error": "InvalidQuantityError", "message": str(exc)}), 400

@app.errorhandler(PaymentFailedError)
def handle_payment_failed(exc):
    return jsonify({"error": "PaymentFailedError", "message": str(exc)}), 402

@app.errorhandler(400)
def handle_bad_request(exc):
    return jsonify({"error": "BadRequest", "message": exc.description}), 400

@app.errorhandler(404)
def handle_not_found(exc):
    return jsonify({"error": "NotFound", "message": exc.description}), 404


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("Flask E-Commerce API starting…")
    app.run(debug=True, host="0.0.0.0", port=5000)
