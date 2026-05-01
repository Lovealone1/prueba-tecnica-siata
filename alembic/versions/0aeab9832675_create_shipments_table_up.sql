CREATE TYPE shipping_status_enum AS ENUM ('PENDING', 'SENT', 'DELIVERED');
CREATE TYPE shipping_type_enum AS ENUM ('LAND', 'MARITIME');

CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    seaport_id UUID REFERENCES seaports(id) ON DELETE SET NULL,
    product_quantity INTEGER NOT NULL,
    shipping_type shipping_type_enum NOT NULL,
    base_price NUMERIC(12, 2) NOT NULL,
    discount_percentage FLOAT DEFAULT 0.0,
    total_price NUMERIC(12, 2) NOT NULL,
    dispatch_location VARCHAR(100) NOT NULL DEFAULT 'USA',
    dispatch_continent VARCHAR(100) NOT NULL DEFAULT 'North America',
    guide_number VARCHAR(10) NOT NULL UNIQUE,
    vehicle_plate VARCHAR(6),
    fleet_number VARCHAR(8),
    registry_date TIMESTAMP(0) WITH TIME ZONE DEFAULT NOW(),
    shipping_date TIMESTAMP(0) WITH TIME ZONE NOT NULL,
    shipping_status shipping_status_enum NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP(0) WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP(0) WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_shipments_guide_number ON shipments(guide_number);
