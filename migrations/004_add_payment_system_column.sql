DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'payment' AND column_name = 'payment_system'
    ) THEN
        ALTER TABLE "payment" ADD COLUMN payment_system VARCHAR DEFAULT 'PRODAMUS';
    END IF;
    ALTER TABLE "payment" RENAME COLUMN prodamus_payment_id TO external_payment_id;
    ALTER TABLE "payment" ADD COLUMN product VARCHAR DEFAULT NULL;
END $$;