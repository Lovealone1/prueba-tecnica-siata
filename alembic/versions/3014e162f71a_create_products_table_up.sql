CREATE TYPE transport_mode_enum AS ENUM ('LAND', 'MARITIME');
CREATE TYPE product_size_enum AS ENUM ('SMALL', 'MEDIUM', 'LARGE', 'EXTRA_LARGE');

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    description TEXT,
    product_type VARCHAR(50) NOT NULL,
    transport_mode transport_mode_enum NOT NULL,
    size product_size_enum NOT NULL DEFAULT 'MEDIUM',
    created_at TIMESTAMP(0) WITH TIME ZONE NOT NULL DEFAULT NOW()
);
