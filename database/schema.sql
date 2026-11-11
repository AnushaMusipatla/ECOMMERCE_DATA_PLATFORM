PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_key INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    registration_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id TEXT PRIMARY KEY,
    customer_key INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price NUMERIC NOT NULL CHECK(unit_price > 0),
    total_amount NUMERIC NOT NULL CHECK(total_amount > 0),
    event_timestamp TEXT NOT NULL,
    source_file TEXT,
    run_id TEXT NOT NULL,
    FOREIGN KEY(customer_key) REFERENCES dim_customers(customer_key)
);
CREATE INDEX IF NOT EXISTS idx_fact_orders_customer ON fact_orders(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_timestamp ON fact_orders(event_timestamp);
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY, start_time TEXT NOT NULL, end_time TEXT, duration_seconds REAL,
    orders_input_count INTEGER NOT NULL DEFAULT 0, customers_input_count INTEGER NOT NULL DEFAULT 0,
    valid_count INTEGER NOT NULL DEFAULT 0, rejected_count INTEGER NOT NULL DEFAULT 0,
    loaded_count INTEGER NOT NULL DEFAULT 0, pipeline_status TEXT NOT NULL, error_message TEXT
);
CREATE TABLE IF NOT EXISTS rejected_records (
    reject_id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, source_file TEXT NOT NULL,
    rejected_at TEXT NOT NULL, rejection_reason TEXT NOT NULL, source_record TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id)
);
