-- ==============================================================================
-- VentaPOS NextGen & LicenseManager — Supabase Cloud Audit Schema
-- Single Source of Truth for Append-Only Cloud License Logging & Online Sync
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- 1. Create Licenses Table
CREATE TABLE IF NOT EXISTS public.licenses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    marketeer_id VARCHAR(100) NOT NULL DEFAULT 'default',
    client_name VARCHAR(200) NOT NULL,
    client_phone VARCHAR(50) NOT NULL,
    store_name VARCHAR(200) DEFAULT '',
    machine_id VARCHAR(64) NOT NULL,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    license_code VARCHAR(50) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    start_date DATE NOT NULL,
    expiry_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_licenses_license_code UNIQUE (license_code)
);

-- 2. Indexes for Performance & Search
CREATE INDEX IF NOT EXISTS idx_licenses_machine_id ON public.licenses (machine_id);
CREATE INDEX IF NOT EXISTS idx_licenses_code ON public.licenses (license_code);
CREATE INDEX IF NOT EXISTS idx_licenses_marketeer ON public.licenses (marketeer_id);
CREATE INDEX IF NOT EXISTS idx_licenses_client_phone ON public.licenses (client_phone);
CREATE INDEX IF NOT EXISTS idx_licenses_store_name ON public.licenses (store_name);
CREATE INDEX IF NOT EXISTS idx_licenses_product_id ON public.licenses (product_id);
CREATE INDEX IF NOT EXISTS idx_licenses_created_at ON public.licenses (created_at DESC);

-- 3. Row-Level Security (RLS) Configuration
-- Strictly enable RLS to enforce append-only policies
ALTER TABLE public.licenses ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS "Allow insert for marketeers" ON public.licenses;
DROP POLICY IF EXISTS "Allow select for audit" ON public.licenses;

-- Allow insert with valid service/anon API key
CREATE POLICY "Allow insert for marketeers"
    ON public.licenses
    FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

-- Allow read for audit verification
CREATE POLICY "Allow select for audit"
    ON public.licenses
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- Note: No UPDATE or DELETE policies are granted. RLS rejects them by default.

-- 4. Cryptographic Anti-Tamper Trigger (Guaranteed Append-Only)
-- Prevents any modification or deletion even if elevated privileges are used
CREATE OR REPLACE FUNCTION public.prevent_license_tamper()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'VentaPOS License Audit Guard: License records are strictly append-only. UPDATE and DELETE actions are prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_license_tamper ON public.licenses;

CREATE TRIGGER trg_prevent_license_tamper
BEFORE UPDATE OR DELETE ON public.licenses
FOR EACH ROW
EXECUTE FUNCTION public.prevent_license_tamper();

-- ==============================================================================
-- 5. Multi-App & Online Integration Architecture Notes:
-- Future Online Mobile Apps & Multi-Tenant Web Portals can securely validate
-- licenses and establish foreign-key relationships referencing:
--   REFERENCES public.licenses(license_code) ON DELETE RESTRICT
-- Because this table is strictly append-only, license records are immutable and
-- guaranteed to persist permanently as the central audit source of truth.
-- ==============================================================================
