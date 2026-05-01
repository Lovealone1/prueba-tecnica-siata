-- DOWN Migration: Remove continent column from warehouses and seaports

ALTER TABLE seaports DROP COLUMN IF EXISTS continent;
ALTER TABLE warehouses DROP COLUMN IF EXISTS continent;
