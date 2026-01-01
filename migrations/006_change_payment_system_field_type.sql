DO $$
BEGIN
    ALTER TABLE "payment"
        ALTER COLUMN payment_system
        TYPE paymentsystem
        USING UPPER(payment_system)::paymentsystem;
END $$;
