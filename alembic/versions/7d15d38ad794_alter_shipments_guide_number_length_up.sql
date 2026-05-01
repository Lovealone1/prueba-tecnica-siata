-- Migration: alter_shipments_guide_number_length (UP)
ALTER TABLE shipments ALTER COLUMN guide_number TYPE VARCHAR(50);
