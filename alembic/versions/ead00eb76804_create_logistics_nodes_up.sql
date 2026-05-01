-- UP Migration: Create warehouses and seaports tables
-- Both share the same structure for logistics node identification

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE seaports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add indices for name and city/country lookups
CREATE INDEX idx_warehouses_name ON warehouses(name);
CREATE INDEX idx_warehouses_location ON warehouses(city, country);

CREATE INDEX idx_seaports_name ON seaports(name);
CREATE INDEX idx_seaports_location ON seaports(city, country);
