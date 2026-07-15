CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL DEFAULT '',
    image_url TEXT,
    privacy VARCHAR(10) NOT NULL DEFAULT 'public'
        CHECK (privacy IN ('public', 'private')),
    reaction_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_posts_public_feed ON posts (id DESC) WHERE privacy = 'public';
CREATE INDEX IF NOT EXISTS idx_posts_user ON posts (user_id, id DESC);

CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_comment_id BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    reaction_count INT NOT NULL DEFAULT 0,
    reply_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comments_post ON comments (post_id, id) WHERE parent_comment_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments (parent_comment_id, id) WHERE parent_comment_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS post_reactions (
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_post_reactions_user ON post_reactions (user_id);

CREATE TABLE IF NOT EXISTS comment_reactions (
    comment_id BIGINT NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (comment_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_comment_reactions_user ON comment_reactions (user_id);

CREATE OR REPLACE FUNCTION bump_post_reaction_count() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE posts SET reaction_count = reaction_count + 1 WHERE id = NEW.post_id;
        RETURN NEW;
    END IF;
    UPDATE posts SET reaction_count = reaction_count - 1 WHERE id = OLD.post_id;
    RETURN OLD;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_post_reaction_count ON post_reactions;
CREATE TRIGGER trg_post_reaction_count
    AFTER INSERT OR DELETE ON post_reactions
    FOR EACH ROW EXECUTE FUNCTION bump_post_reaction_count();

CREATE OR REPLACE FUNCTION bump_comment_reaction_count() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE comments SET reaction_count = reaction_count + 1 WHERE id = NEW.comment_id;
        RETURN NEW;
    END IF;
    UPDATE comments SET reaction_count = reaction_count - 1 WHERE id = OLD.comment_id;
    RETURN OLD;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_comment_reaction_count ON comment_reactions;
CREATE TRIGGER trg_comment_reaction_count
    AFTER INSERT OR DELETE ON comment_reactions
    FOR EACH ROW EXECUTE FUNCTION bump_comment_reaction_count();

CREATE OR REPLACE FUNCTION bump_comment_counts() RETURNS trigger AS $$
DECLARE
    r RECORD;
    delta INT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        r := NEW; delta := 1;
    ELSE
        r := OLD; delta := -1;
    END IF;
    UPDATE posts SET comment_count = comment_count + delta WHERE id = r.post_id;
    IF r.parent_comment_id IS NOT NULL THEN
        UPDATE comments SET reply_count = reply_count + delta WHERE id = r.parent_comment_id;
    END IF;
    RETURN r;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_comment_counts ON comments;
CREATE TRIGGER trg_comment_counts
    AFTER INSERT OR DELETE ON comments
    FOR EACH ROW EXECUTE FUNCTION bump_comment_counts();
