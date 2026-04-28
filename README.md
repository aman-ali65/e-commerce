# 🛒 ECommerce Management System

> A full-stack E-Commerce backend built with Python OOP, demonstrating 3 design patterns, 5 persistence formats, and a live Flask REST API with a modern web dashboard.

---

## 📸 Dashboard Preview

| Dashboard | Products | Orders |
|-----------|----------|--------|
| Stats, charts, recent orders | Filter, add, edit stock | Status tracking, live update |

---

## ✨ Features

- **3 Design Patterns** — Factory, Strategy, Singleton
- **5 Persistence Formats** — JSON, XML, Pickle, SQLite, GZIP + plain Text
- **Full OOP** — ABC, Encapsulation, Polymorphism, Dataclass, Enums
- **REST API** — 15 endpoints via Flask
- **Live Dashboard** — Single-page web UI with real-time stats, charts, modals
- **Product Catalog** — In-memory dict synced with SQLite (O(1) lookups)
- **Auto-generated IDs** — No manual user/order ID entry needed

---

## 🗂️ Project Structure

```
ECommerce_Project/
│
├── app.py                  # Flask REST API (run this for the web dashboard)
├── main.py                 # CLI demo / database seeder
├── requirements.txt
│
├── models/                 # Domain layer
│   ├── product.py          # Abstract Product + Electronics / Clothing / Grocery
│   ├── user.py             # User dataclass + UserRole enum
│   └── order.py            # Order class + OrderStatus enum
│
├── patterns/               # Design Patterns
│   ├── factory.py          # ProductFactory  — FACTORY pattern
│   ├── singleton.py        # Logger          — SINGLETON pattern
│   └── strategy.py         # CreditCard, JazzCash, EasyPaisa, COD — STRATEGY pattern
│
├── persistence/            # 5 storage formats
│   ├── db_handler.py       # SQLite (primary DB)
│   ├── json_handler.py     # JSON  (human-readable backup)
│   ├── xml_handler.py      # XML   (structured markup)
│   ├── pickle_handler.py   # Pickle (binary serialization)
│   └── gzip_handler.py     # GZIP  (compressed log archive)
│
├── utils/
│   ├── helpers.py          # buy_product, save_transaction → transactions.txt
│   └── exceptions.py       # Custom exception hierarchy
│
├── tests/
│   └── test_suite.py       # pytest unit tests
│
├── templates/
│   └── index.html          # Single-page dashboard
│
└── static/
    ├── css/style.css
    └── js/main.js          # Dashboard logic (API calls, charts, modals)
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/your-username/ecommerce-project.git
cd ecommerce-project
pip install -r requirements.txt
```

### 2. Seed the database (optional — adds sample products, users, orders)
```bash
python main.py
```

### 3. Start the web server
```bash
# Windows
set PYTHONIOENCODING=utf-8 && python app.py

# Linux / Mac
PYTHONIOENCODING=utf-8 python app.py
```

### 4. Open the dashboard
```
http://127.0.0.1:5000
```

---

## 🔌 API Endpoints

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products` | List all — supports `?category=Electronics&in_stock=true` |
| `GET` | `/api/products/<id>` | Single product |
| `POST` | `/api/products` | Create product |
| `PATCH` | `/api/products/<id>/stock` | Update stock `{"stock": 50}` |
| `DELETE` | `/api/products/<id>` | Delete |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users` | All users |
| `GET` | `/api/users/next-id` | Next auto-generated ID |
| `POST` | `/api/users` | Create user |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/orders` | All orders — supports `?status=Confirmed` |
| `POST` | `/api/orders` | Place new order |
| `PATCH` | `/api/orders/<id>/status` | Update status |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Dashboard statistics |
| `GET` | `/api/logs?n=80` | Last N log lines (live) |
| `GET` | `/api/datafiles` | All `data/` files with format & size |
| `GET` | `/api/health` | Health check |

---

## 🏗️ Design Patterns

### Factory Pattern — `patterns/factory.py`
Creates product objects without exposing which class is instantiated.
```python
product = ProductFactory.create_product("electronics", 101, "Laptop", 95000, 13)
```

### Singleton Pattern — `patterns/singleton.py`
Ensures only one Logger instance exists across the entire application.
```python
logger = Logger()   # always returns the same object
logger.info("Order placed")  # writes to data/app.log
```

### Strategy Pattern — `patterns/strategy.py`
Swaps payment algorithms at runtime without if/elif chains.
```python
payment = JazzCash("0300-1234567")
order = Order(user, items, payment)
order.checkout()   # calls payment.pay() — no if/elif needed
```

---

## 💾 Persistence Layer

| Format | File | Purpose |
|--------|------|---------|
| **SQLite** | `data/database.db` | Primary relational DB — products, users, orders tables |
| **JSON** | `data/products.json` | Human-readable backup, synced on every write |
| **XML** | `data/products.xml` | Structured markup (seeded by `main.py`) |
| **Pickle** | `data/products.pkl` | Binary Python object serialization |
| **GZIP** | `data/app_logs.gz` | Compressed log archive |
| **Text** | `data/transactions.txt` | Plain-text purchase ledger |

---

## 🧩 OOP Concepts

| Concept | Where |
|---------|-------|
| **Abstract Base Class (ABC)** | `models/product.py` — `Product(ABC)` |
| **Dataclass** | `models/user.py` — `@dataclass class User` |
| **Enum** | `models/user.py` — `UserRole`, `models/order.py` — `OrderStatus` |
| **Encapsulation** | `Product` — `__price` private, `@property` read-only |
| **Inheritance** | `Electronics`, `Clothing`, `Grocery` inherit from `Product` |
| **Polymorphism** | `p.display_info()` — different output per subclass |

---

## 🧪 Running Tests

```bash
pytest tests/test_suite.py -v
```

---

## 📁 Data Files (auto-created)

After running `main.py` or `app.py`, a `data/` directory is created:

```
data/
├── database.db       SQLite — primary store
├── products.json     JSON   — backup
├── products.xml      XML    — backup
├── products.pkl      Pickle — binary backup
├── app.log           Logger output (Singleton Logger)
├── app_logs.gz       Compressed log archive
└── transactions.txt  Purchase ledger
```

---

## ⚙️ Requirements

```
flask>=2.3.0
tabulate>=0.9.0
```

---

## 📄 License

MIT — free to use for academic and personal projects.

---

> Built as an academic project demonstrating Python OOP, Design Patterns, and Full-Stack development with Flask.
