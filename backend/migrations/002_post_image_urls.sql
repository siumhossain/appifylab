ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_urls TEXT[] NOT NULL DEFAULT '{}';

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'posts' AND column_name = 'image_url') THEN
        UPDATE posts SET image_urls = ARRAY[image_url] WHERE image_url IS NOT NULL;
        ALTER TABLE posts DROP COLUMN image_url;
    END IF;
END $$;
