-- External OBD cache: stores AI-summarized web search results per code+vehicle
CREATE TABLE IF NOT EXISTS external_obd_cache (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code TEXT NOT NULL,
    make TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    year TEXT NOT NULL DEFAULT '',
    engine TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    causes JSONB NOT NULL DEFAULT '[]'::jsonb,
    checks JSONB NOT NULL DEFAULT '[]'::jsonb,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (code, make, model, year)
);

CREATE INDEX IF NOT EXISTS idx_external_obd_cache_code ON external_obd_cache (code);
