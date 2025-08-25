PRAGMA foreign_keys = ON;


-- =============================================
-- Таблица: suppliers (Поставщики из Китая)
-- Описание: Хранит данные о поставщиках, с которыми вы работаете.
-- =============================================
CREATE TABLE suppliers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID поставщика
    name                TEXT    NOT NULL,                   -- Название компании или контактного лица
    platform            TEXT,                                -- Платформа: '1688', 'AliExpress', 'Taobao'
    contact_info        TEXT,                                -- Контакты: WeChat, логин, телефон, менеджер
    min_order_value     REAL,                                -- Минимальная сумма заказа (в юанях или $)
    shipping_method     TEXT,                                -- Способ доставки: 'Авиа', 'Морем', 'Экспресс'
    avg_delivery_days   INTEGER,                             -- Среднее время доставки (в днях)
    active              INTEGER NOT NULL DEFAULT 1 
                        CHECK (active IN (0, 1)),            -- Статус: 1 = активен, 0 = неактивен
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))  -- Дата добавления
);


-- =============================================
-- Таблица: products (Товары в каталоге)
-- Описание: Все товары, доступные для продажи клиентам.
-- =============================================
CREATE TABLE products (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID товара
    name                TEXT    NOT NULL,                   -- Название товара (например, "Кран шаровой 1/2")
    description         TEXT,                                -- Подробное описание
    price               REAL    NOT NULL 
                        CHECK (price > 0),                   -- Цена для клиента (в рублях)
    price_CNY               REAL    NOT NULL 
                        CHECK (price > 0),                   -- Цена для клиента (в юанях)
    category            TEXT,                                -- Категория: 'электрика', 'сантехника', 'бытовые'
    supplier_url        TEXT,                                -- Прямая ссылка на товар у поставщика
    supplier_price      REAL,                                -- Цена у поставщика (в юанях)
    supplier_id         INTEGER,                             -- Ссылка на поставщика
    image_url           TEXT,                                -- URL изображения товара
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),  -- Дата добавления
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),  -- Дата обновления
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);


-- =============================================
-- Таблица: customers (Клиенты)
-- Описание: Зарегистрированные пользователи, которые могут оформлять заказы.
-- =============================================
CREATE TABLE customers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID клиента
    full_name           TEXT    NOT NULL,                   -- Полное имя (ФИО)
    email               TEXT    NOT NULL UNIQUE,            -- Email
    phone               TEXT    NOT NULL UNIQUE,            -- Телефон
    delivery_address    TEXT    NOT NULL,                   -- Полный адрес доставки
    city                TEXT,                                -- Город
    country             TEXT    NOT NULL DEFAULT 'Russia',  -- Страна (по умолчанию — Россия)
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))  -- Дата регистрации
);


-- =============================================
-- Таблица: cart (Корзина)
-- Описание: Временное хранение товаров.
--           Поддерживает анонимных пользователей через session_id.
--           При регистрации корзина привязывается к customer_id.
-- =============================================
CREATE TABLE cart (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,      -- Уникальный ID записи в корзине
    customer_id     INTEGER,                                 -- ID клиента (если авторизован)
    session_id      TEXT,                                    -- Уникальный ID сессии (для анонимных)
    product_id      INTEGER NOT NULL,                       -- Ссылка на товар
    quantity        INTEGER NOT NULL DEFAULT 1 
                    CHECK (quantity > 0 AND quantity <= 100),-- Количество (ограничение)
    added_at        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),  -- Дата добавления
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE (customer_id, product_id) WHERE customer_id IS NOT NULL,
    UNIQUE (session_id, product_id) WHERE session_id IS NOT NULL
);


-- =============================================
-- Таблица: orders (Заказы)
-- Описание: Оформленные заказы.
--           Доступны ТОЛЬКО для зарегистрированных клиентов.
--           Анонимные заказы запрещены.
-- =============================================
CREATE TABLE orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID заказа
    customer_id         INTEGER NOT NULL,                   -- ссылка на клиента
    total_amount        REAL    NOT NULL 
                        CHECK (total_amount >= 0),           -- Сумма заказа
    currency            TEXT    NOT NULL DEFAULT 'RUB',     -- Валюта (по умолчанию — рубли)
    order_date          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),  -- Дата оформления
    status              TEXT    NOT NULL DEFAULT 'pending' 
                        CHECK (status IN ('pending', 'confirmed', 'processing_supplier', 'shipped', 'delivered', 'cancelled', 'failed')),
                                                              -- Статус заказа
    payment_status      TEXT    NOT NULL DEFAULT 'unpaid' 
                        CHECK (payment_status IN ('unpaid', 'paid', 'refunded')),
                                                              -- Статус оплаты
    payment_method      TEXT,                                -- Способ оплаты: 'SberPay', 'QIWI', 'наличные'
    tracking_number     TEXT,                                -- Трек-номер доставки
    supplier_order_date TEXT,                                -- Дата заказа у поставщика
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);


-- =============================================
-- Таблица: order_items (Состав заказа)
-- Описание: Какие товары и в каком количестве входят в заказ.
-- =============================================
CREATE TABLE order_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,      -- Уникальный ID позиции
    order_id        INTEGER NOT NULL,                       -- Ссылка на заказ
    product_id      INTEGER NOT NULL,                       -- Ссылка на товар
    quantity        INTEGER NOT NULL 
                    CHECK (quantity > 0),                    -- Количество
    price_at_time   REAL    NOT NULL 
                    CHECK (price_at_time >= 0),              -- Цена на момент заказа
    supplier_price  REAL,                                   -- Цена у поставщика (для анализа прибыли)
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);


-- =============================================
-- Таблица: loyalty_levels (Справочник уровней лояльности)
-- Описание: Хранит все возможные уровни ценности клиентов.
--           Позволяет гибко управлять критериями и автоматизацией.
-- =============================================
CREATE TABLE loyalty_levels (
    level_key                 TEXT PRIMARY KEY,             -- Уникальный ключ уровня
    name                      TEXT NOT NULL,                -- Отображаемое название уровня
    description               TEXT,                         -- Подробное описание уровня
    is_vip                    INTEGER NOT NULL 
                              CHECK (is_vip IN (0, 1)),     -- 1 = это VIP-уровень
    can_upgrade_automatically INTEGER NOT NULL 
                              CHECK (can_upgrade_automatically IN (0, 1))
                                                             -- 1 = можно повышать автоматически
);


-- =============================================
-- Таблица: customer_analytics (Аналитика клиентов)
-- Описание: Хранит статистику покупок и текущий уровень лояльности.
--           Обновляется при каждом новом заказе.
-- =============================================
CREATE TABLE customer_analytics (
    customer_id         INTEGER PRIMARY KEY,                -- Ссылка на клиента
    total_orders        INTEGER NOT NULL DEFAULT 0 
                        CHECK (total_orders >= 0),           -- Общее количество оплаченных заказов
    total_items         INTEGER NOT NULL DEFAULT 0 
                        CHECK (total_items >= 0),            -- Общее количество купленных товаров
    total_spent         REAL    NOT NULL DEFAULT 0.0 
                        CHECK (total_spent >= 0),            -- Общая сумма всех заказов (в рублях)
    avg_order_value     REAL,                                -- Средний чек
    last_order_date     TEXT,                                -- Дата последнего оплаченного заказа
    loyalty_level       TEXT    NOT NULL DEFAULT 'novice' 
                        REFERENCES loyalty_levels(level_key),-- Текущий уровень лояльности
    is_vip              INTEGER NOT NULL DEFAULT 0 
                        CHECK (is_vip IN (0, 1)),            --  1 = клиент — VIP
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                                                             -- Время последнего обновления аналитики
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);


-- =============================================
-- ИНДЕКСЫ (для ускорения запросов)
-- =============================================

-- Аналитика клиентов
CREATE INDEX idx_customer_analytics_loyalty_level ON customer_analytics(loyalty_level);
CREATE INDEX idx_customer_analytics_is_vip         ON customer_analytics(is_vip);
CREATE INDEX idx_customer_analytics_last_order_date ON customer_analytics(last_order_date);

-- Продукты
CREATE INDEX idx_products_category ON products(category);

-- Заказы
CREATE INDEX idx_orders_status ON orders(status);

-- Клиенты
CREATE INDEX idx_customers_phone ON customers(phone);

-- Состав заказов
CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- Поставщики
CREATE INDEX idx_suppliers_platform ON suppliers(platform);

-- Корзина
CREATE INDEX idx_cart_session_id ON cart(session_id);


-- =============================================
-- ТРИГГЕРЫ
-- =============================================

-- Обновляет updated_at при изменении товара
CREATE TRIGGER update_products_updated_at
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    UPDATE products
    SET updated_at = datetime('now', 'localtime')
    WHERE id = OLD.id;
END;
