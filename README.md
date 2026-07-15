# Notes

Quick notes on how I built this and why. No fluff — tables and the reasoning behind them.

## Data model

I kept the schema to five tables. Reactions are separate join tables so a user can only react once (composite PK), and every count the feed needs lives directly on the row.

| Table | What it holds | Key points |
|---|---|---|
| `users` | accounts | `email` unique at DB level, `is_active` for soft delete |
| `posts` | feed posts | `content`, `image_urls[]`, `privacy` (`public`/`private`, enforced by CHECK constraint), counter columns, partial index on public posts for the feed |
| `comments` | comments + replies | self-referencing `parent_comment_id` (NULL = top-level), partial indexes split top-level vs replies |
| `post_reactions` | who reacted to which post | composite PK `(post_id, user_id)` — one reaction per user, no duplicate check needed in code |
| `comment_reactions` | who reacted to which comment | composite PK `(comment_id, user_id)`, same idea |

Everything cascades on delete (`ON DELETE CASCADE`), and users/posts/comments use `is_active` for soft delete instead of removing rows.

## Denormalized counters

I store counts on the row instead of running `COUNT(*)` on every feed read.

| Column | Table | Counts | Updated by |
|---|---|---|---|
| `reaction_count` | `posts` | reactions on the post | DB trigger `trg_post_reaction_count` |
| `comment_count` | `posts` | top-level comments only (replies excluded) | DB trigger on `comments` insert/delete |
| `reaction_count` | `comments` | reactions on the comment | DB trigger `trg_comment_reaction_count` |
| `reply_count` | `comments` | direct replies | DB trigger on `comments` insert/delete |

I did the bumping with DB triggers, so the counter update runs inside the same transaction as the insert/delete — app code can't forget it. A faulty/partial transaction could still drift a count over time. If that ever becomes a real problem, the fix I have in mind is an event system (e.g. SQS): push reaction/comment events to a queue and let a consumer recompute counts. Nothing in the schema blocks it, so it's easy to bolt on later.

## Cookie-based authentication

I didn't want tokens in localStorage, so the browser never sees them. The Next.js server acts as a proxy and keeps the JWTs in encrypted cookies.

| Piece | How I did it |
|---|---|
| Storage | two httpOnly cookies — `_sa` (access) and `_sr` (refresh), AES-256-GCM encrypted with `COOKIE_SECRET`, `SameSite=Lax`, scoped to `/api` |
| Login/register | Next route calls the backend, gets the token pair, seals them into cookies, returns only the user object to the browser |
| API calls | browser calls `/api/backend/*` → Next proxy unseals the access token and forwards to the backend with `Authorization: Bearer` |
| Refresh checker | on every proxied request I check the access token's `exp`; if it's missing or expiring within 60s, the proxy silently rotates the pair using the refresh token and re-sets the cookies — the browser never notices |
| Logout / invalid | cookies cleared, `401` returned |

Cookie lifetime is derived from the JWT's own `exp`, so cookie and token always expire together.

## Rate limiter

Redis-backed, one atomic Lua script per request (middleware in `backend/main.py`). I identify the caller as `user:<id>` when a valid access token is present, otherwise `ip:<client-ip>`.

Three windows checked per request, split into read (GET/HEAD) and write buckets:

| Window | Read limit | Write limit |
|---|---|---|
| 10s burst | 40 | 10 |
| 1 minute | 180 | 30 |
| 1 hour | 3000 | 300 |

| Behavior | Value |
|---|---|
| Over any limit | blocked for a random 30–60 min, responses return `429` |
| Redis down | fails open (requests allowed, warning logged) — I'd rather serve traffic than drop it |
| Config | `RATE_LIMIT_*` env vars, defaults in `backend/common/config.py` |

## Need to know

- Migrations in `backend/migrations/` run automatically at backend startup.
- `users.email` is unique at the DB level; register returns `409` if it exists.
- Soft delete via `is_active` on users/posts/comments — rows are not removed.
- Backend and frontend run in Docker with no volume mounts, `docker compose up -d --build`.


