DO $$
BEGIN
    ALTER TABLE "payment"
        ALTER COLUMN payment_system
        TYPE paymentsystem
        USING UPPER(status)::paymentsystem;
END $$;
