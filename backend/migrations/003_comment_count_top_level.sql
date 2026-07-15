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
    IF r.parent_comment_id IS NULL THEN
        UPDATE posts SET comment_count = comment_count + delta WHERE id = r.post_id;
    ELSE
        UPDATE comments SET reply_count = reply_count + delta WHERE id = r.parent_comment_id;
    END IF;
    RETURN r;
END $$ LANGUAGE plpgsql;

UPDATE posts p
SET comment_count = sub.n
FROM (
    SELECT p2.id, count(c.id) AS n
    FROM posts p2
    LEFT JOIN comments c ON c.post_id = p2.id AND c.parent_comment_id IS NULL
    GROUP BY p2.id
) sub
WHERE p.id = sub.id AND p.comment_count <> sub.n;
