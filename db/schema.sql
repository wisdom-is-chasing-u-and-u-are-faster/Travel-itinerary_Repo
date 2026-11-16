-- SQL DDL Schema Definition (SQLite / ANSI SQL)
-- Enterprise Travel Itinerary Generator Platform

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    offline_caching_enabled BOOLEAN DEFAULT 1,
    preferred_currency VARCHAR(10) DEFAULT 'USD',
    notifications_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS itineraries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER DEFAULT 1,
    title VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    start_date VARCHAR(50) NOT NULL,
    end_date VARCHAR(50) NOT NULL,
    pacing VARCHAR(50) DEFAULT 'Moderate',
    interests TEXT DEFAULT 'Sightseeing, Dining',
    budget_level VARCHAR(50) DEFAULT 'Standard',
    status VARCHAR(50) DEFAULT 'active',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS itinerary_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    itinerary_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    date VARCHAR(50) NOT NULL,
    theme VARCHAR(255) DEFAULT 'Exploration',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    itinerary_id INTEGER NOT NULL,
    day_id INTEGER NOT NULL,
    time VARCHAR(50) DEFAULT '09:00 AM',
    title VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    latitude NUMERIC(10, 6) DEFAULT 0.0,
    longitude NUMERIC(10, 6) DEFAULT 0.0,
    cost NUMERIC(12, 2) DEFAULT 0.00,
    category VARCHAR(100) DEFAULT 'Sightseeing',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE,
    FOREIGN KEY (day_id) REFERENCES itinerary_days(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS collaborators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    user_id INTEGER,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'Editor',
    status VARCHAR(50) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES itineraries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    amount NUMERIC(18, 4) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    paid_by VARCHAR(255) NOT NULL,
    category VARCHAR(100) DEFAULT 'Food & Dining',
    date VARCHAR(50) DEFAULT CURRENT_DATE,
    amount_base NUMERIC(18, 4) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES itineraries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expense_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    amount NUMERIC(18, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER DEFAULT 1,
    experience_id VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    payment_token VARCHAR(255) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'confirmed',
    voucher_code VARCHAR(100) NOT NULL,
    qr_code_url VARCHAR(255) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES itineraries(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS affiliates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    rating NUMERIC(3, 1) DEFAULT 4.8,
    image_url VARCHAR(255) DEFAULT '',
    affiliate_url VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_itineraries INTEGER DEFAULT 128,
    uptime_percent NUMERIC(5, 2) DEFAULT 99.95,
    p95_ttfb_seconds NUMERIC(5, 2) DEFAULT 1.25,
    affiliate_ctr_percent NUMERIC(5, 2) DEFAULT 15.40,
    in_app_conversion_percent NUMERIC(5, 2) DEFAULT 6.80,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_itinerary_user ON itineraries(user_id);
CREATE INDEX IF NOT EXISTS idx_days_itinerary ON itinerary_days(itinerary_id);
CREATE INDEX IF NOT EXISTS idx_activities_day ON activities(day_id);
CREATE INDEX IF NOT EXISTS idx_expenses_trip ON expenses(trip_id, created_at);
CREATE INDEX IF NOT EXISTS idx_collaborators_trip ON collaborators(trip_id);
