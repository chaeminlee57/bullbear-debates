CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE tickers (
  symbol TEXT PRIMARY KEY
);

CREATE TABLE posts (
  id BIGSERIAL,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  title TEXT,
  body TEXT,
  url TEXT,
  subreddit TEXT,
  score INT,
  comments INT,
  tickers TEXT[] NOT NULL DEFAULT '{}',
  stance SMALLINT,
  probs JSONB,
  model_ver TEXT,
  txt_hash TEXT,
  embedding VECTOR(384),
  PRIMARY KEY (id, created_at)
);

SELECT create_hypertable('posts','created_at', if_not_exists=>TRUE);

CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source_extid ON posts(source, external_id, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_tickers_gin ON posts USING GIN (tickers);
CREATE INDEX IF NOT EXISTS idx_posts_hash ON posts(txt_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_embedding ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 64);

CREATE TABLE IF NOT EXISTS ticker_posts (
  created_at TIMESTAMPTZ NOT NULL,
  post_id BIGINT NOT NULL,
  ticker TEXT NOT NULL,
  stance SMALLINT,
  score INT,
  comments INT
);

SELECT create_hypertable('ticker_posts', 'created_at', if_not_exists=>TRUE);
CREATE INDEX IF NOT EXISTS idx_ticker_posts_ticker_time ON ticker_posts(ticker, created_at DESC);

CREATE MATERIALIZED VIEW cagg_10s_sentiment
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('10 seconds', created_at) AS bucket,
  ticker,
  COUNT(*) AS n_posts,
  SUM( CASE WHEN stance=1 THEN 1 WHEN stance=-1 THEN -1 ELSE 0 END
       * (1 + LN(1 + GREATEST(COALESCE(score,0),0) + COALESCE(comments,0))) )::FLOAT
    / NULLIF(SUM(1 + LN(1 + GREATEST(COALESCE(score,0),0) + COALESCE(comments,0))),0)
    AS vw_sentiment,
  SUM( (stance=1)::INT ) AS pos_ct,
  SUM( (stance=0)::INT ) AS neu_ct,
  SUM( (stance=-1)::INT ) AS neg_ct
FROM ticker_posts
WHERE stance IS NOT NULL
GROUP BY bucket, ticker
WITH NO DATA;

CREATE INDEX IF NOT EXISTS idx_cagg_10s_ticker_bucket ON cagg_10s_sentiment(ticker, bucket DESC);

SELECT add_continuous_aggregate_policy('cagg_10s_sentiment',
  start_offset => INTERVAL '1 day',
  end_offset => INTERVAL '10 seconds',
  schedule_interval => INTERVAL '10 seconds');