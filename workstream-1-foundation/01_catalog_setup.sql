-- Main Character Energy - Unity Catalog Setup
-- Target: field_operations_mce catalog

-- Create the main catalog
CREATE CATALOG IF NOT EXISTS field_operations_mce
COMMENT 'Main Character Energy - Agentic Field Management Platform';

-- Create schemas
CREATE SCHEMA IF NOT EXISTS field_operations_mce.raw
COMMENT 'Raw ingestion layer - sensor data, manuals, checklists';

CREATE SCHEMA IF NOT EXISTS field_operations_mce.silver
COMMENT 'Cleaned and enriched data layer';

CREATE SCHEMA IF NOT EXISTS field_operations_mce.gold
COMMENT 'Business-level aggregated metrics';

CREATE SCHEMA IF NOT EXISTS field_operations_mce.agents
COMMENT 'Agent tools, vector indexes, and AI artifacts';

CREATE SCHEMA IF NOT EXISTS field_operations_mce.lakebase_sync
COMMENT 'Staging tables for Lakebase synchronization';

-- Create volumes for file storage
CREATE VOLUME IF NOT EXISTS field_operations_mce.raw.telemetry_ingest
COMMENT 'Incoming sensor telemetry CSV/JSON files';

CREATE VOLUME IF NOT EXISTS field_operations_mce.raw.technical_manuals
COMMENT 'PDF repair manuals and technical documentation';

CREATE VOLUME IF NOT EXISTS field_operations_mce.raw.safety_checklists
COMMENT 'Safety procedure checklists and compliance documents';

-- Grant permissions (adjust group names as needed)
GRANT USE CATALOG ON CATALOG field_operations_mce TO `account users`;
GRANT USE SCHEMA ON SCHEMA field_operations_mce.raw TO `account users`;
GRANT USE SCHEMA ON SCHEMA field_operations_mce.silver TO `account users`;
GRANT USE SCHEMA ON SCHEMA field_operations_mce.gold TO `account users`;
GRANT USE SCHEMA ON SCHEMA field_operations_mce.agents TO `account users`;
GRANT USE SCHEMA ON SCHEMA field_operations_mce.lakebase_sync TO `account users`;

GRANT READ VOLUME ON VOLUME field_operations_mce.raw.telemetry_ingest TO `account users`;
GRANT WRITE VOLUME ON VOLUME field_operations_mce.raw.telemetry_ingest TO `account users`;
GRANT READ VOLUME ON VOLUME field_operations_mce.raw.technical_manuals TO `account users`;
GRANT WRITE VOLUME ON VOLUME field_operations_mce.raw.technical_manuals TO `account users`;
GRANT READ VOLUME ON VOLUME field_operations_mce.raw.safety_checklists TO `account users`;
GRANT WRITE VOLUME ON VOLUME field_operations_mce.raw.safety_checklists TO `account users`;
