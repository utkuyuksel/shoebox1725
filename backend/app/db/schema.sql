-- =============================================================================
-- Shoebox / sport_stats_app — Postgres Schema (v1 MVP)
-- =============================================================================
-- Design principles:
--   1. api-sports.io ids are used as primary keys for entities (leagues, teams,
--      players, fixtures) so we never have to join on a separate "external_id".
--   2. Sport-specific stat tables (football vs basketball) are split for type
--      safety and query performance — no JSONB blobs for the modeled columns.
--   3. Postgres is the canonical store. Redis is a hot cache only — losing
--      Redis must never lose data.
--   4. All timestamps are TIMESTAMPTZ in UTC. Client converts to local.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Extensions
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- fuzzy search (referees, players)


-- -----------------------------------------------------------------------------
-- 1. SPORT / LEAGUE / SEASON
-- -----------------------------------------------------------------------------

CREATE TABLE sports (
    id            SMALLSERIAL PRIMARY KEY,
    code          TEXT UNIQUE NOT NULL,            -- 'football', 'basketball'
    name          TEXT NOT NULL
);

CREATE TABLE leagues (
    id                   INTEGER PRIMARY KEY,      -- api-sports league id
    sport_id             SMALLINT NOT NULL REFERENCES sports(id),
    name                 TEXT NOT NULL,
    country              TEXT,
    country_code         TEXT,                     -- ISO 3166-1 alpha-2 ('TR', 'GB', ...)
    logo_url             TEXT,
    type                 TEXT,                     -- 'League' / 'Cup'
    sort_order           INTEGER DEFAULT 999,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    is_default_popular   BOOLEAN NOT NULL DEFAULT FALSE,
    -- Premium tier control: leagues outside this set are gated for free users.
    is_free_tier         BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_leagues_sport_active     ON leagues(sport_id, is_active);
CREATE INDEX idx_leagues_country_sort     ON leagues(country, sort_order);

CREATE TABLE seasons (
    id            SERIAL PRIMARY KEY,
    league_id     INTEGER NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
    year          INTEGER NOT NULL,                -- 2025 = 2025-2026 season start year
    is_current    BOOLEAN NOT NULL DEFAULT FALSE,
    start_date    DATE,
    end_date      DATE,
    current_round TEXT,                            -- "Regular Season - 12" / "20"
    UNIQUE (league_id, year)
);

CREATE UNIQUE INDEX uniq_seasons_one_current
    ON seasons(league_id) WHERE is_current = TRUE;


-- -----------------------------------------------------------------------------
-- 2. TEAM / PLAYER / SQUAD
-- -----------------------------------------------------------------------------

CREATE TABLE teams (
    id            INTEGER PRIMARY KEY,             -- api-sports team id
    name          TEXT NOT NULL,
    short_name    TEXT,
    logo_url      TEXT,
    country       TEXT,
    founded       INTEGER,
    venue         TEXT,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_teams_name_trgm ON teams USING gin (name gin_trgm_ops);

CREATE TABLE players (
    id            INTEGER PRIMARY KEY,             -- api-sports player id
    name          TEXT NOT NULL,
    firstname     TEXT,
    lastname      TEXT,
    photo_url     TEXT,
    nationality   TEXT,
    birth_date    DATE,
    height_cm     INTEGER,
    weight_kg     INTEGER,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_players_name_trgm ON players USING gin (name gin_trgm_ops);

-- One row per (team, player, season). League is denormalized for fast joins.
CREATE TABLE team_squads (
    team_id        INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id      INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    league_id      INTEGER NOT NULL REFERENCES leagues(id),
    season_year    INTEGER NOT NULL,
    shirt_number   INTEGER,
    position       TEXT,                           -- 'G' / 'D' / 'M' / 'F' for football, etc.
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (team_id, player_id, season_year, league_id)
);

CREATE INDEX idx_team_squads_team_season ON team_squads(team_id, season_year);


-- -----------------------------------------------------------------------------
-- 3. REFEREE
-- -----------------------------------------------------------------------------

CREATE TABLE referees (
    id            INTEGER PRIMARY KEY,             -- api-sports referee id (when available)
    name          TEXT NOT NULL,
    nationality   TEXT,
    photo_url     TEXT,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_referees_name_trgm ON referees USING gin (name gin_trgm_ops);


-- -----------------------------------------------------------------------------
-- 4. FIXTURE (matches)
-- -----------------------------------------------------------------------------

CREATE TABLE fixtures (
    id            BIGINT PRIMARY KEY,              -- api-sports fixture id
    league_id     INTEGER NOT NULL REFERENCES leagues(id),
    season_year   INTEGER NOT NULL,
    round         TEXT,                            -- "Regular Season - 12"
    home_team_id  INTEGER NOT NULL REFERENCES teams(id),
    away_team_id  INTEGER NOT NULL REFERENCES teams(id),
    kickoff_at    TIMESTAMPTZ NOT NULL,
    status        TEXT NOT NULL,                   -- NS / 1H / HT / 2H / FT / AET / PEN / PST / CANC
    is_finished   BOOLEAN GENERATED ALWAYS AS (status IN ('FT', 'AET', 'PEN')) STORED,
    home_goals    INTEGER,
    away_goals    INTEGER,
    home_goals_ht INTEGER,
    away_goals_ht INTEGER,
    referee_id    INTEGER REFERENCES referees(id),
    venue         TEXT,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fixtures_league_season    ON fixtures(league_id, season_year);
CREATE INDEX idx_fixtures_kickoff          ON fixtures(kickoff_at);
CREATE INDEX idx_fixtures_team_kickoff     ON fixtures(home_team_id, kickoff_at DESC);
CREATE INDEX idx_fixtures_away_team        ON fixtures(away_team_id, kickoff_at DESC);
CREATE INDEX idx_fixtures_referee          ON fixtures(referee_id, kickoff_at DESC);
CREATE INDEX idx_fixtures_status           ON fixtures(status) WHERE status NOT IN ('FT','AET','PEN','CANC','PST');


-- Per-team, per-fixture stats. Used for hit-rate calculations, trend graphs,
-- and referee-team aggregations. Football specific (basketball uses its own).
CREATE TABLE football_fixture_team_stats (
    fixture_id          BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    team_id             INTEGER NOT NULL REFERENCES teams(id),
    is_home             BOOLEAN NOT NULL,
    shots_total         INTEGER,
    shots_on            INTEGER,
    shots_off           INTEGER,
    shots_blocked       INTEGER,
    shots_inside_box    INTEGER,
    shots_outside_box   INTEGER,
    fouls               INTEGER,
    corners             INTEGER,
    offsides            INTEGER,
    possession_pct      NUMERIC(5,2),
    yellow_cards        INTEGER,
    red_cards           INTEGER,
    saves               INTEGER,
    passes_total        INTEGER,
    passes_accurate     INTEGER,
    pass_accuracy_pct   NUMERIC(5,2),
    xg                  NUMERIC(6,3),
    PRIMARY KEY (fixture_id, team_id)
);

CREATE INDEX idx_ffts_team ON football_fixture_team_stats(team_id);

CREATE TABLE basketball_fixture_team_stats (
    fixture_id           BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    team_id              INTEGER NOT NULL REFERENCES teams(id),
    is_home              BOOLEAN NOT NULL,
    points               INTEGER,
    field_goals_made     INTEGER,
    field_goals_att      INTEGER,
    two_points_made      INTEGER,
    two_points_att       INTEGER,
    three_points_made    INTEGER,
    three_points_att     INTEGER,
    free_throws_made     INTEGER,
    free_throws_att      INTEGER,
    rebounds_offensive   INTEGER,
    rebounds_defensive   INTEGER,
    assists              INTEGER,
    steals               INTEGER,
    blocks               INTEGER,
    turnovers            INTEGER,
    fouls                INTEGER,
    PRIMARY KEY (fixture_id, team_id)
);

CREATE INDEX idx_bfts_team ON basketball_fixture_team_stats(team_id);


-- -----------------------------------------------------------------------------
-- 5. SEASON AGGREGATES (cached, recomputed by worker)
-- -----------------------------------------------------------------------------
-- These tables store "per-game season averages" — the heart of the Telegram bot
-- and the app's match preview. They are derived from fixtures + fixture stats
-- and refreshed when relevant matches are updated.

CREATE TABLE football_team_season_stats (
    team_id                INTEGER NOT NULL REFERENCES teams(id),
    league_id              INTEGER NOT NULL REFERENCES leagues(id),
    season_year            INTEGER NOT NULL,
    played                 INTEGER NOT NULL DEFAULT 0,
    -- Scoring
    goals_for_pg           NUMERIC(5,2),
    goals_against_pg       NUMERIC(5,2),
    xg_pg                  NUMERIC(5,2),
    -- Shots
    shots_total_pg         NUMERIC(5,2),
    shots_on_pg            NUMERIC(5,2),
    -- Set pieces / discipline
    corners_pg             NUMERIC(5,2),
    fouls_pg               NUMERIC(5,2),
    offsides_pg            NUMERIC(5,2),
    yellow_cards_pg        NUMERIC(5,2),
    red_cards_pg           NUMERIC(5,2),
    saves_pg               NUMERIC(5,2),
    -- Home / Away splits (critical for bettors)
    home_played            INTEGER DEFAULT 0,
    home_goals_for_pg      NUMERIC(5,2),
    home_goals_against_pg  NUMERIC(5,2),
    home_corners_pg        NUMERIC(5,2),
    home_yellow_cards_pg   NUMERIC(5,2),
    away_played            INTEGER DEFAULT 0,
    away_goals_for_pg      NUMERIC(5,2),
    away_goals_against_pg  NUMERIC(5,2),
    away_corners_pg        NUMERIC(5,2),
    away_yellow_cards_pg   NUMERIC(5,2),
    -- League context
    position               INTEGER,
    points                 INTEGER,
    wins                   INTEGER,
    draws                  INTEGER,
    losses                 INTEGER,
    -- Hit-rates (computed from fixture history — denormalized for speed)
    over_15_hit_pct        NUMERIC(5,2),
    over_25_hit_pct        NUMERIC(5,2),
    over_35_hit_pct        NUMERIC(5,2),
    btts_hit_pct           NUMERIC(5,2),
    corners_over_85_pct    NUMERIC(5,2),
    corners_over_105_pct   NUMERIC(5,2),
    cards_over_35_pct      NUMERIC(5,2),
    cards_over_45_pct      NUMERIC(5,2),
    -- Audit
    last_fixture_id        BIGINT,                 -- last finished fixture included
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (team_id, league_id, season_year)
);

CREATE TABLE basketball_team_season_stats (
    team_id              INTEGER NOT NULL REFERENCES teams(id),
    league_id            INTEGER NOT NULL REFERENCES leagues(id),
    season_year          INTEGER NOT NULL,
    played               INTEGER NOT NULL DEFAULT 0,
    points_pg            NUMERIC(5,2),
    points_allowed_pg    NUMERIC(5,2),
    fg_pct               NUMERIC(5,2),
    two_pct              NUMERIC(5,2),
    three_pct            NUMERIC(5,2),
    ft_pct               NUMERIC(5,2),
    two_made_pg          NUMERIC(5,2),
    two_att_pg           NUMERIC(5,2),
    three_made_pg        NUMERIC(5,2),
    three_att_pg         NUMERIC(5,2),
    ft_made_pg           NUMERIC(5,2),
    ft_att_pg            NUMERIC(5,2),
    rebounds_off_pg      NUMERIC(5,2),
    rebounds_def_pg      NUMERIC(5,2),
    rebounds_total_pg    NUMERIC(5,2),
    assists_pg           NUMERIC(5,2),
    steals_pg            NUMERIC(5,2),
    blocks_pg            NUMERIC(5,2),
    turnovers_pg         NUMERIC(5,2),
    -- Home / Away splits
    home_played          INTEGER DEFAULT 0,
    home_points_pg       NUMERIC(5,2),
    home_points_allowed_pg NUMERIC(5,2),
    away_played          INTEGER DEFAULT 0,
    away_points_pg       NUMERIC(5,2),
    away_points_allowed_pg NUMERIC(5,2),
    -- League context
    position             INTEGER,
    wins                 INTEGER,
    losses               INTEGER,
    -- Hit-rates
    total_over_2105_pct  NUMERIC(5,2),             -- combined points over a line
    spread_cover_pct     NUMERIC(5,2),             -- placeholder, computed if needed
    last_fixture_id      BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (team_id, league_id, season_year)
);


-- Player season aggregates (used for player profile + player props in v1.1).
CREATE TABLE football_player_season_stats (
    player_id              INTEGER NOT NULL REFERENCES players(id),
    team_id                INTEGER NOT NULL REFERENCES teams(id),
    league_id              INTEGER NOT NULL REFERENCES leagues(id),
    season_year            INTEGER NOT NULL,
    appearances            INTEGER DEFAULT 0,
    started                INTEGER DEFAULT 0,
    minutes_pg             NUMERIC(5,2),
    rating                 NUMERIC(4,2),
    goals                  INTEGER,
    assists                INTEGER,
    shots_pg               NUMERIC(5,2),
    shots_on_pg            NUMERIC(5,2),
    passes_pg              NUMERIC(5,2),
    passes_accurate_pg     NUMERIC(5,2),
    pass_accuracy_pct      NUMERIC(5,2),
    interceptions_pg       NUMERIC(5,2),
    tackles_pg             NUMERIC(5,2),
    fouls_pg               NUMERIC(5,2),
    was_fouled_pg          NUMERIC(5,2),
    yellow_cards_pg        NUMERIC(5,2),
    red_cards_pg           NUMERIC(5,2),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, team_id, league_id, season_year)
);

CREATE TABLE basketball_player_season_stats (
    player_id              INTEGER NOT NULL REFERENCES players(id),
    team_id                INTEGER NOT NULL REFERENCES teams(id),
    league_id              INTEGER NOT NULL REFERENCES leagues(id),
    season_year            INTEGER NOT NULL,
    appearances            INTEGER DEFAULT 0,
    minutes_pg             NUMERIC(5,2),
    points_pg              NUMERIC(5,2),
    rebounds_pg            NUMERIC(5,2),
    assists_pg             NUMERIC(5,2),
    steals_pg              NUMERIC(5,2),
    blocks_pg              NUMERIC(5,2),
    turnovers_pg           NUMERIC(5,2),
    fg_made_pg             NUMERIC(5,2),
    fg_att_pg              NUMERIC(5,2),
    fg_pct                 NUMERIC(5,2),
    two_made_pg            NUMERIC(5,2),
    two_att_pg             NUMERIC(5,2),
    two_pct                NUMERIC(5,2),
    three_made_pg          NUMERIC(5,2),
    three_att_pg           NUMERIC(5,2),
    three_pct              NUMERIC(5,2),
    ft_made_pg             NUMERIC(5,2),
    ft_att_pg              NUMERIC(5,2),
    ft_pct                 NUMERIC(5,2),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, team_id, league_id, season_year)
);


-- Referee season aggregates + the "ref vs team" matrix.
CREATE TABLE referee_season_stats (
    referee_id           INTEGER NOT NULL REFERENCES referees(id),
    league_id            INTEGER NOT NULL REFERENCES leagues(id),
    season_year          INTEGER NOT NULL,
    matches              INTEGER DEFAULT 0,
    yellow_cards_pg      NUMERIC(5,2),
    red_cards_pg         NUMERIC(5,2),
    fouls_pg             NUMERIC(5,2),
    penalties_pg         NUMERIC(5,2),
    home_win_pct         NUMERIC(5,2),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (referee_id, league_id, season_year)
);

-- The "hakem-takım eşleşmesi" data feed: how does this ref behave when this
-- team is involved? Aggregated across the team's last N matches with this ref.
CREATE TABLE referee_team_history (
    referee_id           INTEGER NOT NULL REFERENCES referees(id),
    team_id              INTEGER NOT NULL REFERENCES teams(id),
    matches              INTEGER DEFAULT 0,
    yellow_cards_pg      NUMERIC(5,2),
    red_cards_pg         NUMERIC(5,2),
    fouls_pg             NUMERIC(5,2),
    wins                 INTEGER DEFAULT 0,
    draws                INTEGER DEFAULT 0,
    losses               INTEGER DEFAULT 0,
    last_fixture_id      BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (referee_id, team_id)
);


-- -----------------------------------------------------------------------------
-- 6. INSIGHTS (rule-based, generated per fixture)
-- -----------------------------------------------------------------------------
-- Each fixture can have N short insight cards generated from rules. We store
-- them so we can rank, dedupe, and serve fast without recomputing per request.

CREATE TABLE fixture_insights (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fixture_id      BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    rule_code       TEXT NOT NULL,                 -- e.g., 'CORNER_TREND_DOWN'
    severity        SMALLINT NOT NULL DEFAULT 1,   -- 1..5, drives card highlight color
    locale          TEXT NOT NULL DEFAULT 'en',
    headline        TEXT NOT NULL,                 -- "GS son 5 maçta korner %22 düşmüş"
    body            TEXT,                          -- optional 1-2 sentence detail
    metric_key      TEXT,                          -- 'corners' / 'yellow_cards' / ...
    metric_value    NUMERIC(8,2),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fixture_insights_fixture ON fixture_insights(fixture_id, severity DESC);
CREATE UNIQUE INDEX uniq_fixture_insights_dedupe
    ON fixture_insights(fixture_id, rule_code, locale);


-- -----------------------------------------------------------------------------
-- 7. USERS (mirror of Supabase Auth)
-- -----------------------------------------------------------------------------
-- Supabase Auth owns identity. We mirror just enough to attach app data
-- (watchlists, preferences, subscription status synced from RevenueCat).

CREATE TABLE users (
    id                  UUID PRIMARY KEY,          -- mirrors auth.users.id from Supabase
    email               TEXT,
    locale              TEXT NOT NULL DEFAULT 'en',
    country_code        TEXT,                      -- detected at signup, refined by app
    -- Subscription state, sourced from RevenueCat webhooks. Trust the webhook
    -- as source of truth; this is a cache to avoid hitting RC on every request.
    is_premium          BOOLEAN NOT NULL DEFAULT FALSE,
    premium_expires_at  TIMESTAMPTZ,
    rc_entitlement      TEXT,
    -- Audit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at        TIMESTAMPTZ
);

CREATE INDEX idx_users_premium ON users(is_premium) WHERE is_premium = TRUE;


CREATE TABLE user_watchlist_fixtures (
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fixture_id   BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    added_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, fixture_id)
);

CREATE INDEX idx_uwf_user_added ON user_watchlist_fixtures(user_id, added_at DESC);


-- -----------------------------------------------------------------------------
-- 8. WORKER / OPERATIONAL
-- -----------------------------------------------------------------------------
-- Track when we last refreshed each league + per-entity refresh, so QStash
-- jobs can decide what to do without scanning everything.

CREATE TABLE refresh_log (
    id            BIGSERIAL PRIMARY KEY,
    entity_kind   TEXT NOT NULL,                   -- 'league_fixtures' / 'team_stats' / ...
    entity_id     TEXT NOT NULL,                   -- composite key encoded as text
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at   TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'running', -- running / ok / failed
    error         TEXT,
    api_calls     INTEGER DEFAULT 0
);

CREATE INDEX idx_refresh_log_entity ON refresh_log(entity_kind, entity_id, finished_at DESC);
CREATE INDEX idx_refresh_log_status ON refresh_log(status, started_at) WHERE status = 'failed';
