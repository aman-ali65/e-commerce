import sqlite3
import os

DB_FILE = "data/database.db"


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


def get_connection():
    _ensure_dir()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row   # returns dict-like rows
    return conn


def initialize_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id   INTEGER PRIMARY KEY,
            name         TEXT    NOT NULL,
            price        REAL    NOT NULL,
            stock        INTEGER NOT NULL,
            category     TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY,
            name         TEXT    NOT NULL,
            email        TEXT,
            role         TEXT,
            created_at   TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id     INTEGER PRIMARY KEY,
            user_name    TEXT,
            user_id      INTEGER,
            total        REAL,
            payment      TEXT,
            status       TEXT,
            created_at   TEXT
        )
    """)

    conn.commit()
    conn.close()


# ── Write helpers ─────────────────────────────────────────────────────────────

def save_product_db(product):
    conn = get_connection()
    cur = conn.cursor()
    d = product.to_dict()
    cur.execute("""
        INSERT OR REPLACE INTO products (product_id, name, price, stock, category)
        VALUES (?, ?, ?, ?, ?)
    """, (d["product_id"], d["name"], d["price"], d["stock"], d["category"]))
    conn.commit()
    conn.close()


def save_all_products_db(products: list):
    initialize_db()
    for p in products:
        save_product_db(p)
    print(f"  ✅ SQLite saved  → {DB_FILE}  ({len(products)} products)")


def save_user_db(user):
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    d = user.to_dict()
    cur.execute("""
        INSERT OR REPLACE INTO users (id, name, email, role, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (d["id"], d["name"], d["email"], d["role"], d["created_at"]))
    conn.commit()
    conn.close()


def save_order_db(order):
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    d = order.to_dict()
    cur.execute("""
        INSERT OR REPLACE INTO orders
        (order_id, user_name, user_id, total, payment, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (d["order_id"], d["user"], d["user_id"], d["total"],
          d["payment"], d["status"], d["created_at"]))
    conn.commit()
    conn.close()


# ── Read helpers ──────────────────────────────────────────────────────────────

def fetch_all_products() -> list:
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def fetch_product_by_id(product_id: int) -> dict | None:
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def fetch_all_orders() -> list:
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def fetch_all_users() -> list:
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def update_product_stock(product_id: int, new_stock: int) -> bool:
    """Set stock for a product. Returns True if a row was updated."""
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET stock = ? WHERE product_id = ?",
        (new_stock, product_id),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def update_order_status(order_id: int, status: str) -> bool:
    """Update order status. Returns True if a row was updated."""
    initialize_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE orders SET status = ? WHERE order_id = ?",
        (status, order_id),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed
