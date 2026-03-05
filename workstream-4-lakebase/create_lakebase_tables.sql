
    -- Create main_energy user
    CREATE USER IF NOT EXISTS main_energy WITH PASSWORD 'MCE_SecurePass_2026!';

    -- Grant permissions
    GRANT USAGE ON SCHEMA mce_operations TO main_energy;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mce_operations TO main_energy;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA mce_operations TO main_energy;

    -- Create permanent user for service connections
    CREATE USER IF NOT EXISTS mce_service WITH PASSWORD 'MCE_Service_Perm_2026!';
    GRANT USAGE ON SCHEMA mce_operations TO mce_service;
    GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mce_operations TO mce_service;
    


    -- Table 1: Live Asset Status
    CREATE TABLE IF NOT EXISTS mce_lakebase_catalog.mce_operations.mce_assets_live_status (
        asset_id VARCHAR(50) PRIMARY KEY,
        site VARCHAR(200),
        asset_type VARCHAR(50),
        asset_name VARCHAR(200),
        vibration_hz DECIMAL(10,2),
        temp_celsius DECIMAL(10,2),
        rpm DECIMAL(10,2),
        voltage_output DECIMAL(15,2),
        status VARCHAR(20) CHECK (status IN ('CRITICAL', 'WARNING', 'HEALTHY')),
        predicted_failure_type VARCHAR(50),
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active_work_order_id UUID,
        hours_since_last_maintenance DECIMAL(10,2)
    );

    CREATE INDEX IF NOT EXISTS idx_asset_status ON mce_lakebase_catalog.mce_operations.mce_assets_live_status(status);
    CREATE INDEX IF NOT EXISTS idx_asset_site ON mce_lakebase_catalog.mce_operations.mce_assets_live_status(site);
    CREATE INDEX IF NOT EXISTS idx_last_updated ON mce_lakebase_catalog.mce_operations.mce_assets_live_status(last_updated);

    -- Table 2: Work Orders
    CREATE TABLE IF NOT EXISTS mce_lakebase_catalog.mce_operations.mce_work_orders (
        work_order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        asset_id VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        priority VARCHAR(10) CHECK (priority IN ('P1', 'P2', 'P3')),
        status VARCHAR(20) CHECK (status IN ('DISPATCHED', 'IN_PROGRESS', 'COMPLETE', 'CANCELLED')),
        assigned_technician VARCHAR(200),
        predicted_failure_date DATE,
        predicted_failure_type VARCHAR(50),
        required_parts JSONB,
        procedure_steps JSONB,
        safety_checklist JSONB,
        ai_repair_summary TEXT,
        estimated_duration_hours DECIMAL(5,2),
        actual_duration_hours DECIMAL(5,2),
        first_time_fix_verified BOOLEAN DEFAULT FALSE,
        completed_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES mce_lakebase_catalog.mce_operations.mce_assets_live_status(asset_id)
    );

    CREATE INDEX IF NOT EXISTS idx_wo_status ON mce_lakebase_catalog.mce_operations.mce_work_orders(status);
    CREATE INDEX IF NOT EXISTS idx_wo_priority ON mce_lakebase_catalog.mce_operations.mce_work_orders(priority);
    CREATE INDEX IF NOT EXISTS idx_wo_asset ON mce_lakebase_catalog.mce_operations.mce_work_orders(asset_id);
    CREATE INDEX IF NOT EXISTS idx_wo_technician ON mce_lakebase_catalog.mce_operations.mce_work_orders(assigned_technician);

    -- Table 3: Technicians
    CREATE TABLE IF NOT EXISTS mce_lakebase_catalog.mce_operations.mce_technicians (
        technician_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        site VARCHAR(200),
        certifications JSONB,
        current_location TEXT,
        available BOOLEAN DEFAULT TRUE,
        active_work_orders INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_tech_available ON mce_lakebase_catalog.mce_operations.mce_technicians(available);
    CREATE INDEX IF NOT EXISTS idx_tech_site ON mce_lakebase_catalog.mce_operations.mce_technicians(site);

    -- Create updated_at trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Apply trigger to work_orders
    DROP TRIGGER IF EXISTS update_work_orders_updated_at ON mce_lakebase_catalog.mce_operations.mce_work_orders;
    CREATE TRIGGER update_work_orders_updated_at
        BEFORE UPDATE ON mce_lakebase_catalog.mce_operations.mce_work_orders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Apply trigger to technicians
    DROP TRIGGER IF EXISTS update_technicians_updated_at ON mce_lakebase_catalog.mce_operations.mce_technicians;
    CREATE TRIGGER update_technicians_updated_at
        BEFORE UPDATE ON mce_lakebase_catalog.mce_operations.mce_technicians
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    