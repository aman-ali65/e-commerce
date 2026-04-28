import sys
import os

# Make sure imports work from any working directory
sys.path.insert(0, os.path.dirname(__file__))

# ── Models ────────────────────────────────────────────
from models.user import User, UserRole
from models.order import Order, OrderStatus

# ── Patterns ──────────────────────────────────────────
from patterns.factory import ProductFactory
from patterns.strategy import CreditCard, JazzCash, EasyPaisa, CashOnDelivery
from patterns.singleton import Logger

# ── Utils ─────────────────────────────────────────────
from utils.helpers import buy_product, print_banner, print_section, save_transaction, calculate_discount
from utils.exceptions import OutOfStockError, InvalidQuantityError

# ── Persistence ───────────────────────────────────────
from persistence.json_handler import save_products, save_orders, save_users
from persistence.xml_handler import save_products_xml
from persistence.pickle_handler import backup_products, restore_products
from persistence.db_handler import (
    initialize_db, save_all_products_db, save_user_db, save_order_db,
    fetch_all_products, fetch_all_orders
)
from persistence.compression import compress_logs



#  MAIN

def main():
    os.makedirs("data", exist_ok=True)

    logger = Logger()               # Singleton
    logger.info("=== E-Commerce System Started ===")

    # ── 1. SINGLETON CHECK ────────────────────────────
    print_banner("SMART E-COMMERCE BACKEND SYSTEM")
    print_section("1. Singleton Logger Verification")
    l1 = Logger()
    l2 = Logger()
    print(f"  Logger l1 is l2 → {l1 is l2}  (True = Singleton works ✅)")

    # ── 2. CREATE USERS ───────────────────────────────
    print_section("2. Creating Users")
    users = [
        User("Aman Khan",  1, "aman@daraz.pk",   UserRole.CUSTOMER),
        User("Sara Ali",   2, "sara@daraz.pk",   UserRole.CUSTOMER),
        User("Admin Bhai", 3, "admin@daraz.pk",  UserRole.ADMIN),
    ]
    for u in users:
        print(f"  👤 {u}")
        logger.info(f"User created: {u.name} [{u.role.value}]")

    # ── 3. CREATE PRODUCTS (Factory Pattern) ──────────
    print_section("3. Creating Products via Factory Pattern")
    products = [
        ProductFactory.create_product("electronics", 101, "Laptop",        95_000, 15, warranty_years=2),
        ProductFactory.create_product("electronics", 102, "Smartphone",    45_000, 30, warranty_years=1),
        ProductFactory.create_product("electronics", 103, "Headphones",     8_500, 50, warranty_years=1),
        ProductFactory.create_product("clothing",    201, "Shalwar Kameez",  2_200, 100, size="L"),
        ProductFactory.create_product("clothing",    202, "Jacket",          5_500,  40, size="XL"),
        ProductFactory.create_product("grocery",     301, "Basmati Rice 5kg",1_200, 200, expiry_date="2026-12"),
        ProductFactory.create_product("grocery",     302, "Olive Oil 1L",    1_800,  80, expiry_date="2025-06"),
    ]
    for p in products:
        print(f"  📦 {p}")
        logger.info(f"Product created: {p.name} | Rs.{p.price:,.0f} | Stock: {p.stock}")

    # ── 4. BUY PRODUCTS ───────────────────────────────
    print_section("4. Purchasing Products")

    # Normal purchase
    try:
        buy_product(products[0], 2)   # Buy 2 Laptops
        buy_product(products[1], 5)   # Buy 5 Smartphones
        buy_product(products[3], 3)   # Buy 3 Shalwar Kameez
        print("  ✅ Purchases completed successfully.")
    except (OutOfStockError, InvalidQuantityError) as e:
        logger.error(str(e))

    # Trigger OutOfStockError
    print("\n  -- Testing OutOfStockError --")
    try:
        buy_product(products[6], 9999)   # Way more than stock
    except OutOfStockError as e:
        logger.warning(f"OutOfStockError caught: {e}")
        print(f"  ⚠️  Handled: {e}")

    # Trigger InvalidQuantityError
    print("\n  -- Testing InvalidQuantityError --")
    try:
        buy_product(products[2], -5)
    except InvalidQuantityError as e:
        logger.warning(f"InvalidQuantityError caught: {e}")
        print(f"  ⚠️  Handled: {e}")

    # ── 5. CREATE ORDERS (Strategy Pattern) ───────────
    print_section("5. Placing Orders (Strategy Pattern — Payment Methods)")

    order1 = Order(users[0],
                   [(products[0], 1), (products[2], 2)],
                   CreditCard("5399 **** **** 8821"))

    order2 = Order(users[1],
                   [(products[1], 1), (products[3], 2)],
                   JazzCash("0311-1234567"))

    order3 = Order(users[0],
                   [(products[5], 3)],
                   CashOnDelivery())

    orders = [order1, order2, order3]

    for order in orders:
        print(order)
        order.checkout()
        logger.success(f"Order #{order.order_id} confirmed for {order.user.name} — Rs.{order.total:,.0f}")

    # Update one order status
    order1.update_status(OrderStatus.SHIPPED)
    logger.info(f"Order #{order1.order_id} status → {order1.status.value}")

    # ── 6. PERSISTENCE LAYER ──────────────────────────
    print_section("6. Saving Data — Multi-Format Persistence")

    # JSON
    save_products(products)
    save_orders(orders)
    save_users(users)

    # XML
    save_products_xml(products)

    # Pickle
    backup_products(products)

    # SQLite
    initialize_db()
    save_all_products_db(products)
    for u in users:
        save_user_db(u)
    for o in orders:
        save_order_db(o)
    print(f"  ✅ Users & orders saved → data/database.db")

    # ── 7. READ FROM DB ───────────────────────────────
    print_section("7. Reading from SQLite Database")
    db_products = fetch_all_products()
    print(f"  📋 Products in DB ({len(db_products)} rows):")
    for row in db_products:
        print(f"     {row}")

    db_orders = fetch_all_orders()
    print(f"\n  📋 Orders in DB ({len(db_orders)} rows):")
    for row in db_orders:
        print(f"     {row}")

    # ── 8. RESTORE FROM PICKLE ────────────────────────
    print_section("8. Restoring Products from Pickle Backup")
    restored = restore_products()
    print(f"  📦 Restored {len(restored)} product objects from pickle:")
    for p in restored[:3]:
        print(f"     {p}")
    if len(restored) > 3:
        print(f"     ... and {len(restored)-3} more")

    # ── 9. LOG COMPRESSION ────────────────────────────
    print_section("9. Compressing Log File (GZIP)")
    compress_logs()

    # ── 10. TEXT FILE TRANSACTIONS (Step 9 — new.txt) ─
    print_section("10. Text-File Transaction Log")
    for o in orders:
        for p, qty in o.items:
            save_transaction(o.user.name, p.price * qty, "purchase")
    print(f"  ✅ Transactions appended → data/transactions.txt")

    # ── 11. DISCOUNT + pdb DEMO (Step 8 — new.txt) ───
    print_section("11. Discount Calculation (assert + logging)")
    sample_price = products[0].price
    discounted = calculate_discount(sample_price, 0.10)
    print(f"  💰 {products[0].name}: Rs.{sample_price:,.0f} → Rs.{discounted:,.0f} (10% off)")

    # ── 12. TABULATE SUMMARY (Step 11 — new.txt) ──────
    print_section("12. Final Product Summary Report (tabulate)")
    try:
        from tabulate import tabulate
        rows = [
            [
                p.name,
                p.category(),
                f"Rs.{p.price:,.0f}",
                p.stock,
            ]
            for p in products
        ]
        headers = ["Product", "Category", "Price", "Stock"]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    except ImportError:
        print("  ⚠️  tabulate not installed — run: pip install tabulate")

    # ── DONE ──────────────────────────────────────────
    print_banner("ALL SYSTEMS OPERATIONAL ✅")
    logger.success("=== E-Commerce System Finished Successfully ===")
    print("\n  Files written to data/:")
    for fname in sorted(os.listdir("data")):
        size = os.path.getsize(f"data/{fname}")
        print(f"    📄 {fname:<25} {size:>8,} bytes")
    print()


if __name__ == "__main__":
    main()