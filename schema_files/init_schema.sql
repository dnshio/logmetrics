CREATE TABLE snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL,
    errors INTEGER NOT NULL,
    avg_duration DOUBLE PRECISION NOT NULL,
    median_duration DOUBLE PRECISION NOT NULL,
    p99_duration DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (customer_id, date)
);

-- Index for the composite unique constraint and queries using both customer_id and date
CREATE INDEX idx_daily_stats_customer_date ON snapshots (customer_id, date);

-- Index for queries filtering by customer_id alone
CREATE INDEX idx_daily_stats_customer ON snapshots (customer_id);
