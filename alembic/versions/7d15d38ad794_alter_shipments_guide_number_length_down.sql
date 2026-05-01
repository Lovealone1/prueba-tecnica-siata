-- Migration: alter_shipments_guide_number_length (DOWN)
-- Note: Reverting might fail if there are values longer than 10 chars.
ALTER TABLE shipments ALTER COLUMN guide_number TYPE VARCHAR(10);
