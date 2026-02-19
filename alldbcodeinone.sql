-- 1. Main Task Ledger: Handles the "Ground Truths" of the blueprint
CREATE TABLE IF NOT EXISTS smart_tasks (
    id SERIAL PRIMARY KEY,
    wbs_code VARCHAR(50),           -- CSI MasterFormat (e.g., 02.10)
    task_name TEXT NOT NULL,        -- e.g., "Remove existing shed"
    planned_hours INT DEFAULT 0,    -- AI-estimated man-hours
    risk_level VARCHAR(20) DEFAULT 'Low', -- High for 15%+ slopes
    environmental_buffer BOOLEAN DEFAULT FALSE, -- True if near Stream
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for high-speed searching by WBS code
CREATE INDEX IF NOT EXISTS idx_wbs ON smart_tasks(wbs_code);

-- 2. Project Context: Stores site history and geography
CREATE TABLE IF NOT EXISTS project_metadata (
    id SERIAL PRIMARY KEY,
    project_name TEXT,              -- e.g., "Sample House"
    parcel_no TEXT UNIQUE,          -- From Page 1: County Assessor Parcel No.
    ground_type TEXT,               -- e.g., "Steep Slopes / 15% or more"
    water_hazard_detected BOOLEAN,  -- Based on Stream findings
    lot_area_sqft NUMERIC,          -- Material density calculation
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Audit & Learning: Tracks AI reasoning for "Future Consequences"
CREATE TABLE IF NOT EXISTS audit_trail (
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES smart_tasks(id),
    change_reason TEXT,             -- e.g., "Adjusted for 15% incline"
    ai_model_version VARCHAR(50),   -- e.g., "llama3.2"
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);