-- Extensions Postgres needs before Alembic migrations run.
-- Loaded by docker-compose on first boot. On Neon, run this once via the
-- console or as a manual migration step.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
