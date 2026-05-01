CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TYPE globalrole AS ENUM ('ADMIN', 'USER');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), 
    email CITEXT NOT NULL UNIQUE, 
    first_name VARCHAR(255) NOT NULL, 
    last_name VARCHAR(255) NOT NULL, 
    phone_number VARCHAR(255), 
    is_active BOOLEAN NOT NULL DEFAULT true, 
    global_role globalrole NOT NULL DEFAULT 'ADMIN',
    last_login_at TIMESTAMP(0) WITH TIME ZONE, 
    created_at TIMESTAMP(0) WITH TIME ZONE NOT NULL DEFAULT NOW(), 
    updated_at TIMESTAMP(0) WITH TIME ZONE NOT NULL DEFAULT NOW(), 
    CONSTRAINT check_users_email_lowercase CHECK (email = LOWER(TRIM(email)))
);

CREATE INDEX idx_users_email ON users(LOWER(TRIM(email)));
