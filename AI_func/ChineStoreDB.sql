-- =============================================
-- БАЗА ДАННЫХ: Telegram-бот для заказа товаров с Taobao
-- Система: клиент ищет → бот парсит Taobao → показывает товары → клиент заказывает → админ выкупает
-- =============================================

PRAGMA foreign_keys = ON;


-- =============================================
-- Таблица: suppliers (Поставщики)
-- Описание: Основной поставщик — Taobao. Можно добавить других (1688, AliExpress).
-- =============================================
CREATE TABLE suppliers (
    id_supplier         INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID поставщика
    name                TEXT    NOT NULL,                   -- Название (например, "Taobao")
    platform            TEXT    NOT NULL,                   -- Платформа: 'Taobao', '1688'
    contact_info        TEXT,                               -- Контакты (логин, WeChat, менеджер)
    min_order_value     REAL,                               -- Мин. сумма заказа (в юанях)
    shipping_method     TEXT,                               -- Способ доставки: 'Авиа', 'Курьер'
    avg_delivery_days   INTEGER,                            -- Среднее время доставки (в днях)
    active              INTEGER NOT NULL DEFAULT 1 
                        CHECK (active IN (0, 1)),           -- 1 = активен, 0 = отключён
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                                                             -- Дата добавления
);


-- =============================================
-- Таблица: products (Товары с Taobao)
-- Описание: Кэшированные товары после парсинга. Хранятся фото, цена в рублях, атрибуты.
-- =============================================
CREATE TABLE products (
    id_product          INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID товара в системе
    name                TEXT    NOT NULL,                   -- Название на русском (обработано ИИ)
    description         TEXT,                               -- Описание (переведено и сокращено)
    price_rub           REAL    NOT NULL 
                        CHECK (price_rub > 0),              -- Цена для клиента в рублях
    original_price_yuan REAL    NOT NULL,                   -- Оригинальная цена в юанях
    category            TEXT    DEFAULT 'обувь',            -- Категория: 'обувь', 'одежда', 'аксессуары'
    taobao_url          TEXT    NOT NULL,                   -- Прямая ссылка на товар на Taobao
    taobao_item_id      TEXT    NOT NULL UNIQUE,            -- Уникальный ID товара на Taobao
    image_urls          TEXT,                               -- JSON-массив URL изображений
    attributes          TEXT,                               -- JSON: размеры, цвета, варианты
    last_updated        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                                                             -- Время последнего обновления
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                                                             -- Дата добавления в БД
);


-- =============================================
-- Таблица: customers (Клиенты Telegram)
-- Описание: Зарегистрированные пользователи бота.
-- =============================================
CREATE TABLE customers (
    id_customer         INTEGER PRIMARY KEY AUTOINCREMENT,  -- Внутренний ID клиента
    telegram_id         INTEGER NOT NULL UNIQUE,            -- Telegram user_id (основной ключ)
    full_name           TEXT,                               -- Имя и фамилия из профиля
    username            TEXT,                               -- @username (если есть)
    phone               TEXT,                               -- Номер телефона (по желанию)
    delivery_address    TEXT,                               -- Полный адрес доставки
    city                TEXT,                               -- Город
    country             TEXT    NOT NULL DEFAULT 'Russia',  -- Страна (по умолчанию — Россия)
    language            TEXT    NOT NULL DEFAULT 'ru',      -- Язык интерфейса: 'ru', 'en'
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                                                             -- Дата регистрации
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                                                             -- Последнее обновление профиля
);


-- =============================================
-- Таблица: user_sessions (Сессии поиска)
-- Описание: Временные результаты поиска. Хранятся запрос и товары.
-- =============================================
CREATE TABLE user_sessions (
    id_session          INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID сессии
    telegram_id         INTEGER NOT NULL,                   -- Кто ищет (ссылка на клиента)
    query               TEXT    NOT NULL,                   -- Поисковый запрос: "кроссовки Nike"
    results_json        TEXT,                               -- JSON: список товаров с Taobao
    status              TEXT    NOT NULL DEFAULT 'active' 
                        CHECK (status IN ('active', 'completed', 'expired')),
                                                             -- Статус сессии
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                                                             -- Дата создания
    expires_at          TEXT    NOT NULL DEFAULT (datetime('now', '+1 hour')),
                                                             -- Автоудаление через 1 час
    FOREIGN KEY (telegram_id) REFERENCES customers(telegram_id) ON DELETE CASCADE
);


-- =============================================
-- Таблица: cart (Корзина товаров)
-- Описание: Временное хранение выбранных товаров с размерами и цветами.
-- =============================================
CREATE TABLE cart (
    id_cart             INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID позиции
    id_customer         INTEGER NOT NULL,                   -- Кто добавил (ссылка на клиента)
    id_product          INTEGER NOT NULL,                   -- Ссылка на товар
    size                TEXT,                               -- Размер (например, 42)
    color               TEXT,                               -- Цвет (например, "чёрный")
    quantity            INTEGER NOT NULL DEFAULT 1 
                        CHECK (quantity >= 1 AND quantity <= 10),
                                                             -- Количество
    added_at            TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                                                             -- Дата добавления
    FOREIGN KEY (id_customer) REFERENCES customers(id_customer) ON DELETE CASCADE,
    FOREIGN KEY (id_product) REFERENCES products(id_product) ON DELETE SET NULL,
    UNIQUE (id_customer, id_product, size, color)           -- Один товар с атрибутами — один раз
);


-- =============================================
-- Таблица: orders (Заказы клиентов)
-- Описание: Оформленные заказы. Только для зарегистрированных пользователей.
-- =============================================
CREATE TABLE orders (
    id_order            INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID заказа
    id_customer         INTEGER NOT NULL,                   -- Кто заказал
    total_amount_rub    REAL    NOT NULL,                   -- Общая сумма заказа в рублях
    currency            TEXT    NOT NULL DEFAULT 'RUB',     -- Валюта (по умолчанию — рубли)
    order_date          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                                                             -- Дата оформления
    status              TEXT    NOT NULL DEFAULT 'pending' 
                        CHECK (status IN ('pending', 'confirmed', 'paid', 'processing_supplier', 'shipped', 'delivered', 'cancelled')),
                                                             -- Статус заказа
    payment_status      TEXT    NOT NULL DEFAULT 'unpaid' 
                        CHECK (payment_status IN ('unpaid', 'paid', 'refunded')),
                                                             -- Статус оплаты
    payment_method      TEXT,                               -- Способ оплаты: 'SberPay', 'QIWI'
    delivery_address    TEXT    NOT NULL,                   -- Адрес доставки (на момент заказа)
    tracking_number     TEXT,                               -- Трек-номер после отправки
    admin_note          TEXT,                               -- Комментарий админа (например, "Срочно!")
    exchange_rate_used  REAL,                               -- Курс юаня, использованный при расчёте
    FOREIGN KEY (id_customer) REFERENCES customers(id_customer) ON DELETE CASCADE
);


-- =============================================
-- Таблица: order_items (Позиции в заказе)
-- Описание: Детализация заказа. Сохраняет снимок товара на момент покупки.
-- =============================================
CREATE TABLE order_items (
    id_item             INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID позиции
    id_order            INTEGER NOT NULL,                   -- Ссылка на заказ
    id_product          INTEGER,                            -- ID товара (может быть удалён)
    product_name        TEXT    NOT NULL,                   -- Название на момент заказа
    product_price_rub   REAL    NOT NULL,                   -- Цена на момент заказа
    size                TEXT,                               -- Размер
    color               TEXT,                               -- Цвет
    quantity            INTEGER NOT NULL,                   -- Количество
    subtotal            REAL    NOT NULL,                   -- Итог: quantity * price
    FOREIGN KEY (id_order) REFERENCES orders(id_order) ON DELETE CASCADE,
    FOREIGN KEY (id_product) REFERENCES products(id_product) ON DELETE SET NULL
);


-- =============================================
-- Таблица: exchange_rates (История курсов)
-- Описание: Хранит изменения курса юаня к рублю с точностью до времени.
-- =============================================
CREATE TABLE exchange_rates (
    id_rate             INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID записи курса
    rate_rub            REAL    NOT NULL,                   -- 1 CNY = X RUB
    source              TEXT    DEFAULT 'manual',           -- Источник: 'manual', 'cbr', 'taobao_api'
    recorded_at         TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                                                             -- Дата и время фиксации курса
);


-- =============================================
-- Таблица: analytics (Системные метрики)
-- Описание: Хранит служебные данные: общая статистика, настройки, флаги.
-- =============================================
CREATE TABLE analytics (
    key                 TEXT    NOT NULL,                   -- Ключ: 'total_customers', 'markup_percent'
    value               TEXT    NOT NULL,                   -- Значение: '125', '25.0'
    recorded_at         TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                                                             -- Время записи
    PRIMARY KEY (key, recorded_at)                          -- Поддержка истории по ключу
);


-- =============================================
-- ИНДЕКСЫ (для ускорения запросов)
-- =============================================

-- Товары
CREATE INDEX idx_products_taobao_id ON products(taobao_item_id);
CREATE INDEX idx_products_category   ON products(category);
CREATE INDEX idx_products_name       ON products(name);

-- Клиенты
CREATE INDEX idx_customers_telegram_id ON customers(telegram_id);

-- Сессии
CREATE INDEX idx_user_sessions_telegram_id ON user_sessions(telegram_id);
CREATE INDEX idx_user_sessions_expires_at  ON user_sessions(expires_at);

-- Корзина
CREATE INDEX idx_cart_customer ON cart(id_customer);

-- Заказы
CREATE INDEX idx_orders_customer       ON orders(id_customer);
CREATE INDEX idx_orders_status         ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_date           ON orders(order_date);

-- Позиции заказов
CREATE INDEX idx_order_items_order ON order_items(id_order);

-- Курсы валют
CREATE INDEX idx_exchange_rates_recorded_at ON exchange_rates(recorded_at);
