DO $$
BEGIN
    ALTER TABLE "payment" ALTER COLUMN payment_system DROP DEFAULT;

    ALTER TABLE "payment"
        ALTER COLUMN payment_system
        TYPE paymentsystem
        USING UPPER(payment_system)::paymentsystem;

    ALTER TABLE "payment" ALTER COLUMN payment_system SET DEFAULT 'ROBOKASSA'::paymentsystem;
END $$;
