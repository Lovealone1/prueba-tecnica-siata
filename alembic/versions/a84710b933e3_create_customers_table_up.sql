CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    identifier VARCHAR(255) NOT NULL UNIQUE,
    email CITEXT NOT NULL UNIQUE,
    phone VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP(0) WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP(0) WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT check_customers_email_lowercase CHECK (email = LOWER(TRIM(email)))
);

CREATE INDEX idx_customers_email ON customers(LOWER(TRIM(email)));
CREATE INDEX idx_customers_identifier ON customers(identifier);
