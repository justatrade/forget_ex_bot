DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'reminder_24h_sent'
    ) THEN
        ALTER TABLE "user" DROP COLUMN reminder_24h_sent;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'reminder_72h_sent'
    ) THEN
        ALTER TABLE "user" DROP COLUMN reminder_72h_sent;
    END IF;
END $$;