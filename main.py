import sys
import os
from tabulate import tabulate

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
    fetch_all_products, fetch_all_orders, save_product_db
)
from persistence.compression import compress_logs


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTOMATED DEMO (original logic)
# ═══════════════════════════════════════════════════════════════════════════════

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
        rows = [[p.name, p.category(), f"Rs.{p.price:,.0f}", p.stock] for p in products]
        headers = ["Product", "Category", "Price", "Stock"]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    except ImportError:
        print("  ⚠️  tabulate not installed")

    # ── DONE ──────────────────────────────────────────
    print_banner("ALL SYSTEMS OPERATIONAL ✅")
    logger.success("=== E-Commerce System Finished Successfully ===")
    print("\n  Files written to data/:")
    for fname in sorted(os.listdir("data")):
        size = os.path.getsize(f"data/{fname}")
        print(f"    📄 {fname:<25} {size:>8,} bytes")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
#  INTERACTIVE CLI MENU
# ═══════════════════════════════════════════════════════════════════════════════

def interactive_menu():
    """Provides a functional CLI for managing the store."""
    os.makedirs("data", exist_ok=True)
    initialize_db()
    logger = Logger()

    while True:
        print_banner("E-COMMERCE CLI MANAGER")
        print(" 1.  📋 List All Products (from SQLite)")
        print(" 2.  📦 Add New Product (Factory Pattern)")
        print(" 3.  🔧 Update Product Stock")
        print(" 4.  🗑️  Delete Product")
        print(" 5.  👤 List All Users")
        print(" 6.  ➕ Add New User")
        print(" 7.  🛒 Place New Order (Strategy Pattern)")
        print(" 8.  📜 View All Orders")
        print(" 9.  🧪 Run Automated Demo")
        print(" 0.  🚪 Exit")
        
        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            print_section("Product List")
            rows = fetch_all_products()
            if not rows: print("   (No products found)"); continue
            table_rows = [[r["product_id"], r["name"], r["category"], f"Rs.{r['price']:,.0f}", r["stock"]] for r in rows]
            print(tabulate(table_rows, headers=["ID", "Name", "Category", "Price", "Stock"], tablefmt="grid"))

        elif choice == "2":
            print_section("Add Product")
            # Dynamically get unique categories from DB to show the user
            all_db_p = fetch_all_products()
            existing_cats = sorted(list(set(r["category"].lower() for r in all_db_p)))
            if not existing_cats: existing_cats = ["electronics", "clothing", "grocery"]
            
            print(f"Existing Categories: {', '.join(existing_cats)}")
            print("Type one of the above OR a completely NEW one (e.g. furniture)")
            ptype = input("Product Category: ").lower().strip()
            pid   = int(input("Product ID: "))
            name  = input("Name: ")
            price = float(input("Price: "))
            stock = int(input("Stock: "))
            
            kwargs = {}
            if ptype == "electronics": kwargs["warranty_years"] = int(input("Warranty (years): "))
            elif ptype == "clothing":  kwargs["size"] = input("Size: ")
            elif ptype == "grocery":   kwargs["expiry_date"] = input("Expiry (YYYY-MM): ")

            try:
                p = ProductFactory.create_product(ptype, pid, name, price, stock, **kwargs)
                save_product_db(p)
                print(f"  ✅ Product '{name}' added successfully.")
            except Exception as e:
                print(f"  ❌ Error: {e}")

        elif choice == "3":
            print_section("Update Stock")
            pid = int(input("Product ID: "))
            new_stock = int(input("New stock: "))
            from persistence.db_handler import update_product_stock
            if update_product_stock(pid, new_stock):
                print("  ✅ Stock updated.")
            else:
                print("  ❌ Not found.")

        elif choice == "4":
            print_section("Delete Product")
            pid = int(input("Product ID to delete: "))
            from persistence.db_handler import get_connection
            conn = get_connection()
            conn.execute("DELETE FROM products WHERE product_id = ?", (pid,))
            conn.commit()
            conn.close()
            print("  ✅ Product deleted.")

        elif choice == "5":
            print_section("User List")
            from persistence.db_handler import fetch_all_users
            users = fetch_all_users()
            table = [[u["id"], u["name"], u["email"], u["role"]] for u in users]
            print(tabulate(table, headers=["ID", "Name", "Email", "Role"], tablefmt="grid"))

        elif choice == "6":
            print_section("Add User")
            uname = input("Name: ")
            uid   = int(input("ID: "))
            email = input("Email: ")
            u = User(uname, uid, email)
            save_user_db(u)
            print(f"  ✅ User {uname} saved.")

        elif choice == "7":
            print_section("Place Order")
            from persistence.db_handler import fetch_all_users
            all_users = fetch_all_users()
            if not all_users: print("   Add a user first!"); continue
            print("Select User ID:")
            for u in all_users: print(f"  [{u['id']}] {u['name']}")
            user_id = int(input("User ID: "))
            u_row = next((r for r in all_users if r["id"] == user_id), None)
            user_obj = User(u_row["name"], u_row["id"], u_row["email"], UserRole(u_row["role"]))

            order_items = []
            while True:
                pid = int(input("Product ID to add (0 to finish): "))
                if pid == 0: break
                qty = int(input("Quantity: "))
                from persistence.db_handler import fetch_product_by_id
                p_row = fetch_product_by_id(pid)
                if not p_row: continue
                prod_obj = ProductFactory.create_product(p_row["category"].lower(), p_row["product_id"], p_row["name"], p_row["price"], p_row["stock"])
                try:
                    buy_product(prod_obj, qty)
                    order_items.append((prod_obj, qty))
                    from persistence.db_handler import update_product_stock
                    update_product_stock(pid, prod_obj.stock)
                except Exception as e:
                    print(f"   ❌ {e}")

            if not order_items: continue
            pay = CashOnDelivery()
            order = Order(user_obj, order_items, pay)
            order.checkout()
            save_order_db(order)
            print(f"  ✅ Order placed! Total: Rs.{order.total:,.0f}")

        elif choice == "8":
            print_section("All Orders")
            orders = fetch_all_orders()
            table = [[o["order_id"], o["user_name"], f"Rs.{o['total']:,.0f}", o["status"]] for o in orders]
            print(tabulate(table, headers=["Order#", "Customer", "Total", "Status"], tablefmt="grid"))

        elif choice == "9":
            main()

        elif choice == "0":
            break
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        main()
    else:
        try:
            interactive_menu()
        except KeyboardInterrupt:
            print("\nExiting...")