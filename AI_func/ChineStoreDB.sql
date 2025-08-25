CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK (price > 0),        -- Цена для клиента
    category TEXT,                                -- 'электрика', 'сантехника', 'бытовые'
    supplier_url TEXT,                            -- Ссылка на товар у поставщика (например, 1688)
    supplier_price REAL,                          -- Цена у поставщика (в юанях или $)
    supplier_name TEXT DEFAULT 'Unknown',         -- Название поставщика
    image_url TEXT,                               -- Картинка товара
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);