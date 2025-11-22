DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'came_from'
    ) THEN
        ALTER TABLE "user" ADD COLUMN came_from VARCHAR DEFAULT 'Guest';
    END IF;
END $$;