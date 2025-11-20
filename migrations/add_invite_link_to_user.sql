DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'invite_link'
    ) THEN
        ALTER TABLE "user" ADD COLUMN invite_link VARCHAR;
    END IF;
END $$;