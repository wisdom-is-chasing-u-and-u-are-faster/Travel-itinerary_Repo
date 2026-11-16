-- Seed Data for Travel Itinerary Generator Platform (SQLite / ANSI SQL)

-- Users
INSERT OR IGNORE INTO users (id, name, email, offline_caching_enabled, preferred_currency, notifications_enabled)
VALUES 
    (1, 'Alex Morgan', 'alex.morgan@example.com', 1, 'USD', 1),
    (2, 'Sophia Chen', 'sophia.chen@example.com', 1, 'EUR', 1),
    (3, 'Marcus Rossi', 'marcus.rossi@example.com', 1, 'USD', 0);

-- Itineraries
INSERT OR IGNORE INTO itineraries (id, user_id, title, destination, start_date, end_date, pacing, interests, budget_level, status, version)
VALUES 
    (1, 1, 'Classic Italian Renaissance - Florence & Tuscany', 'Florence, Italy', '2026-10-10', '2026-10-15', 'Moderate', 'Art, Architecture, Gastronomy', 'Standard', 'active', 1),
    (2, 1, 'Tokyo Urban Lights & Ancient Shrines', 'Tokyo, Japan', '2026-11-01', '2026-11-06', 'Fast-paced', 'Culture, Tech, Street Food', 'Standard', 'active', 1);

-- Itinerary Days
INSERT OR IGNORE INTO itinerary_days (id, itinerary_id, day_number, date, theme)
VALUES 
    (1, 1, 1, '2026-10-10', 'Historic Heart of Florence'),
    (2, 1, 2, '2026-10-11', 'Galleries & Panoramic Vistas'),
    (3, 1, 3, '2026-10-12', 'Chianti Wine Country Day Trip'),
    (4, 2, 1, '2026-11-01', 'Shinjuku & Shibuya Neon Trails'),
    (5, 2, 2, '2026-11-02', 'Asakusa & Traditional Tokyo');

-- Activities (with spatial geocoordinates for clustering verification REQ-F-005)
INSERT OR IGNORE INTO activities (id, itinerary_id, day_id, time, title, location, latitude, longitude, cost, category, notes)
VALUES 
    (1, 1, 1, '09:00 AM', 'Cattedrale di Santa Maria del Fiore (Duomo)', 'Piazza del Duomo, Florence', 43.773145, 11.255960, 30.00, 'Sightseeing', 'Skip-the-line reservation voucher secured.'),
    (2, 1, 1, '11:30 AM', 'Battistero di San Giovanni', 'Piazza San Giovanni, Florence', 43.773200, 11.254980, 15.00, 'Culture', 'Admire the Gates of Paradise bronze reliefs.'),
    (3, 1, 1, '01:00 PM', 'Tuscan Trattoria Lunch', 'Mercato Centrale, Florence', 43.776600, 11.253000, 25.00, 'Dining', 'Authentic ribollita and local Chianti.'),
    (4, 1, 1, '03:30 PM', 'Piazza della Signoria & Loggia dei Lanzi', 'Piazza della Signoria, Florence', 43.769560, 11.255814, 0.00, 'Sightseeing', 'Open-air sculpture museum walking tour.'),
    (5, 1, 2, '10:00 AM', 'Uffizi Gallery Masterpieces Tour', 'Piazzale degli Uffizi, Florence', 43.767786, 11.255311, 45.00, 'Art', 'Guided viewing of Botticelli Birth of Venus.'),
    (6, 1, 2, '02:00 PM', 'Ponte Vecchio Artisan Stroll', 'Ponte Vecchio, Florence', 43.767985, 11.253198, 0.00, 'Shopping', 'Historic medieval stone closed-spandrel bridge.'),
    (7, 2, 4, '09:30 AM', 'Meiji Jingu Shrine Morning Walk', 'Shibuya, Tokyo', 35.676398, 139.699326, 0.00, 'Culture', 'Peaceful forested shrine dedicated to Emperor Meiji.'),
    (8, 2, 4, '01:00 PM', 'Harajuku Takeshita Street Lunch', 'Harajuku, Tokyo', 35.671500, 139.703200, 18.00, 'Dining', 'Trendy cafes and Japanese savory crepes.');

-- Collaborators (REQ-F-011, AC-3)
INSERT OR IGNORE INTO collaborators (id, trip_id, user_id, name, email, role, status)
VALUES 
    (1, 1, 1, 'Alex Morgan', 'alex.morgan@example.com', 'Owner', 'Active'),
    (2, 1, 2, 'Sophia Chen', 'sophia.chen@example.com', 'Editor', 'Active'),
    (3, 1, 3, 'Marcus Rossi', 'marcus.rossi@example.com', 'Viewer', 'Active');

-- Expenses (Multi-currency ledger with decimal precision)
INSERT OR IGNORE INTO expenses (id, trip_id, title, amount, currency, paid_by, category, date, amount_base, status)
VALUES 
    (1, 1, 'Florence Duomo Dome Access Tickets', 90.0000, 'EUR', 'Alex Morgan', 'Sightseeing', '2026-10-10', 97.2000, 'active'),
    (2, 1, 'Trattoria da Burde Welcome Dinner', 15000.0000, 'JPY', 'Sophia Chen', 'Food & Dining', '2026-10-10', 100.0000, 'active'),
    (3, 1, 'Private Chianti Wine Shuttle', 180.0000, 'USD', 'Marcus Rossi', 'Transport', '2026-10-11', 180.0000, 'active');

-- Expense Splits
INSERT OR IGNORE INTO expense_splits (id, expense_id, user_name, amount)
VALUES 
    (1, 1, 'Alex Morgan', 32.4000),
    (2, 1, 'Sophia Chen', 32.4000),
    (3, 1, 'Marcus Rossi', 32.4000),
    (4, 2, 'Alex Morgan', 33.3333),
    (5, 2, 'Sophia Chen', 33.3333),
    (6, 2, 'Marcus Rossi', 33.3334);

-- Bookings (REQ-F-016, AC-4)
INSERT OR IGNORE INTO bookings (id, trip_id, experience_id, title, payment_token, amount, currency, status, voucher_code, qr_code_url)
VALUES 
    (1, 1, 'exp-florence-duomo', 'Small-Group Florence Duomo Tour', 'tok_visa_4242', 65.00, 'EUR', 'confirmed', 'VOUCH-DUOMO-9821', '/static/qr/duomo.png');

-- Affiliate Deals
INSERT OR IGNORE INTO affiliates (id, title, destination, provider, price, rating, image_url, affiliate_url, status)
VALUES 
    (1, 'Small-Group Florence Duomo Tour', 'Florence', 'GetYourGuide', 65.00, 4.9, 'https://images.unsplash.com/photo-1543429776-2782fc8e1acd', 'https://www.getyourguide.com/florence-l32/duomo-tour?partner_id=TRAVELGEN', 'active'),
    (2, 'Hotel Pitti Palace Boutique Stay', 'Florence', 'Booking.com', 220.00, 4.8, 'https://images.unsplash.com/photo-1566073771259-6a8506099945', 'https://www.booking.com/hotel/it/pitti-palace.html?aid=TRAVELGEN', 'active'),
    (3, 'Tuscan Cooking Class & Farmhouse Dinner', 'Florence', 'Viator', 95.00, 5.0, 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5', 'https://www.viator.com/tours/florence/cooking-class?aid=TRAVELGEN', 'active');

-- Admin Metrics
INSERT OR IGNORE INTO admin_metrics (id, total_itineraries, uptime_percent, p95_ttfb_seconds, affiliate_ctr_percent, in_app_conversion_percent)
VALUES 
    (1, 1420, 99.98, 1.15, 16.20, 7.10);
