DO $$
BEGIN
    ALTER TABLE "payment"
        ALTER COLUMN status
        TYPE paymentstatus
        USING UPPER(status)::paymentstatus;
END $$;
