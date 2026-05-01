-- UP Migration: Add continent column to warehouses and seaports
-- Defaulting to 'UNKNOWN' for any existing records

ALTER TABLE warehouses ADD COLUMN continent VARCHAR(50) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE seaports ADD COLUMN continent VARCHAR(50) DEFAULT 'UNKNOWN' NOT NULL;

-- Remove default for future inserts (handled by SQLAlchemy model validation)
ALTER TABLE warehouses ALTER COLUMN continent DROP DEFAULT;
ALTER TABLE seaports ALTER COLUMN continent DROP DEFAULT;
