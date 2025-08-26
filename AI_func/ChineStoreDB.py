# database.py
import sqlite3
import os
from datetime import datetime

DATABASE = 'store.db'


def init_db():
    """Создаёт базу данных и все таблицы, если их нет"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Включаем внешние ключи
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Таблицы (вставлены как в твой SQL)
    schema_sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS suppliers (
        id_supplier         INTEGER PRIMARY KEY AUTOINCREMENT,
        name                TEXT    NOT NULL,
        platform            TEXT    NOT NULL,
        contact_info        TEXT,
        min_order_value     REAL,
        shipping_method     TEXT,
        avg_delivery_days   INTEGER,
        active              INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
        created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS products (
        id_product          INTEGER PRIMARY KEY AUTOINCREMENT,
        name                TEXT    NOT NULL,
        description         TEXT,
        price_rub           REAL    NOT NULL CHECK (price_rub > 0),
        original_price_yuan REAL    NOT NULL,
        category            TEXT    DEFAULT 'обувь',
        taobao_url          TEXT    NOT NULL,
        taobao_item_id      TEXT    NOT NULL UNIQUE,
        image_urls          TEXT,
        attributes          TEXT,
        last_updated        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS customers (
        id_customer         INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id         INTEGER NOT NULL UNIQUE,
        full_name           TEXT,
        username            TEXT,
        phone               TEXT,
        delivery_address    TEXT,
        city                TEXT,
        country             TEXT    NOT NULL DEFAULT 'Russia',
        language            TEXT    NOT NULL DEFAULT 'ru',
        created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS user_sessions (
        id_session          INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id         INTEGER NOT NULL,
        query               TEXT    NOT NULL,
        results_json        TEXT,
        status              TEXT    NOT NULL DEFAULT 'active' 
                            CHECK (status IN ('active', 'completed', 'expired')),
        created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        expires_at          TEXT    NOT NULL DEFAULT (datetime('now', '+1 hour')),
        FOREIGN KEY (telegram_id) REFERENCES customers(telegram_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS cart (
        id_cart             INTEGER PRIMARY KEY AUTOINCREMENT,
        id_customer         INTEGER NOT NULL,
        id_product          INTEGER NOT NULL,
        size                TEXT,
        color               TEXT,
        quantity            INTEGER NOT NULL DEFAULT 1 
                            CHECK (quantity >= 1 AND quantity <= 10),
        added_at            TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (id_customer) REFERENCES customers(id_customer) ON DELETE CASCADE,
        FOREIGN KEY (id_product) REFERENCES products(id_product) ON DELETE SET NULL,
        UNIQUE (id_customer, id_product, size, color)
    );

    CREATE TABLE IF NOT EXISTS orders (
        id_order            INTEGER PRIMARY KEY AUTOINCREMENT,
        id_customer         INTEGER NOT NULL,
        total_amount_rub    REAL    NOT NULL,
        currency            TEXT    NOT NULL DEFAULT 'RUB',
        order_date          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        status              TEXT    NOT NULL DEFAULT 'pending' 
                            CHECK (status IN ('pending', 'confirmed', 'paid', 'processing_supplier', 'shipped', 'delivered', 'cancelled')),
        payment_status      TEXT    NOT NULL DEFAULT 'unpaid' 
                            CHECK (payment_status IN ('unpaid', 'paid', 'refunded')),
        payment_method      TEXT,
        delivery_address    TEXT    NOT NULL,
        tracking_number     TEXT,
        admin_note          TEXT,
        exchange_rate_used  REAL,
        FOREIGN KEY (id_customer) REFERENCES customers(id_customer) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id_item             INTEGER PRIMARY KEY AUTOINCREMENT,
        id_order            INTEGER NOT NULL,
        id_product          INTEGER,
        product_name        TEXT    NOT NULL,
        product_price_rub   REAL    NOT NULL,
        size                TEXT,
        color               TEXT,
        quantity            INTEGER NOT NULL,
        subtotal            REAL    NOT NULL,
        FOREIGN KEY (id_order) REFERENCES orders(id_order) ON DELETE CASCADE,
        FOREIGN KEY (id_product) REFERENCES products(id_product) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS exchange_rates (
        id_rate             INTEGER PRIMARY KEY AUTOINCREMENT,
        rate_rub            REAL    NOT NULL,
        source              TEXT    DEFAULT 'manual',
        recorded_at         TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS analytics (
        key                 TEXT    NOT NULL,
        value               TEXT    NOT NULL,
        recorded_at         TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        PRIMARY KEY (key, recorded_at)
    );

    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_products_taobao_id ON products(taobao_item_id);
    CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
    CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
    CREATE INDEX IF NOT EXISTS idx_customers_telegram_id ON customers(telegram_id);
    CREATE INDEX IF NOT EXISTS idx_user_sessions_telegram_id ON user_sessions(telegram_id);
    CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_cart_customer ON cart(id_customer);
    CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(id_customer);
    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
    CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
    CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(id_order);
    CREATE INDEX IF NOT EXISTS idx_exchange_rates_recorded_at ON exchange_rates(recorded_at);
    """

    # Выполняем схему по частям
    cursor.executescript(schema_sql)

    # Инициализация курса юаня
    cursor.execute("INSERT OR IGNORE INTO exchange_rates (rate_rub, source) VALUES (12.5, 'manual');")

    conn.commit()
    conn.close()


# =============================================
# ФУНКЦИИ РАБОТЫ С КЛИЕНТАМИ
# =============================================

def register_or_update_customer(telegram_id, first_name, last_name=None, username=None):
    """Регистрирует или обновляет клиента"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO customers 
            (telegram_id, full_name, username, updated_at) 
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(telegram_id) DO UPDATE SET
                full_name = excluded.full_name,
                username = excluded.username,
                updated_at = excluded.updated_at
        """, (telegram_id, full_name, username))
        conn.commit()
    except Exception as e:
        print(f"Ошибка регистрации клиента: {e}")
    finally:
        conn.close()


def get_customer(telegram_id):
    """Возвращает клиента по telegram_id"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_customer_profile(telegram_id, phone=None, address=None, city=None, email=None):
    """Обновляет профиль клиента"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    fields = []
    values = []

    if phone:
        fields.append("phone = ?")
        values.append(phone)
    if address:
        fields.append("delivery_address = ?")
        values.append(address)
    if city:
        fields.append("city = ?")
        values.append(city)
    if email:
        fields.append("email = ?")  # Добавим email в таблицу (можно расширить)
        values.append(email)

    if not fields:
        return

    values.append(telegram_id)
    set_clause = ", ".join(fields)
    query = f"UPDATE customers SET {set_clause}, updated_at = datetime('now', 'localtime') WHERE telegram_id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()


# =============================================
# ФУНКЦИИ РАБОТЫ С ЗАКАЗАМИ
# =============================================

def save_order(user_info, order_data):
    """Сохраняет заказ и позиции в БД"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        # Получаем клиента
        customer = get_customer(user_info['id'])
        if not customer:
            register_or_update_customer(
                user_info['id'],
                user_info.get('first_name') or user_info.get('name', 'Клиент'),
                user_info.get('last_name'),
                user_info.get('username')
            )
            customer = get_customer(user_info['id'])

        if not customer:
            return None

        # Текущий курс
        cursor.execute("SELECT rate_rub FROM exchange_rates ORDER BY recorded_at DESC LIMIT 1")
        rate_row = cursor.fetchone()
        exchange_rate = rate_row[0] if rate_row else 12.5

        # Вставляем заказ
        cursor.execute("""
            INSERT INTO orders (
                id_customer, total_amount_rub, delivery_address, order_date, exchange_rate_used
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            customer['id_customer'],
            round(order_data['total'], 2),
            user_info.get('address', 'Не указан'),
            order_data['timestamp'],
            exchange_rate
        ))
        order_id = cursor.lastrowid

        # Вставляем позиции
        for item in order_data['items']:
            quantity = item.get('quantity', 1)
            subtotal = item['price'] * quantity
            cursor.execute("""
                INSERT INTO order_items (
                    id_order, id_product, product_name, product_price_rub, size, color, quantity, subtotal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                item.get('id_product'),
                item['name'],
                item['price'],
                item.get('size'),
                item.get('color'),
                quantity,
                subtotal
            ))

        conn.commit()
        return order_id

    except Exception as e:
        print(f"Ошибка сохранения заказа: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_recent_orders(limit=10):
    """Возвращает последние заказы с именами клиентов"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id_order, o.total_amount_rub, o.order_date, o.status,
               c.full_name, c.phone, c.delivery_address
        FROM orders o
        JOIN customers c ON o.id_customer = c.id_customer
        ORDER BY o.order_date DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
