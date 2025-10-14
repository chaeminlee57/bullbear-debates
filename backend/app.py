from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
from settings import PG_DSN
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return psycopg2.connect(PG_DSN)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/sentiment/series")
def sentiment_series(ticker: str, from_hours: int = 1):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT bucket, vw_sentiment, n_posts, pos_ct, neu_ct, neg_ct
        FROM cagg_10s_sentiment
        WHERE ticker = %s
        AND bucket > now() - make_interval(hours => %s)
        ORDER BY bucket DESC
    """, (ticker, from_hours))
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(r) for r in results]

@app.get("/sentiment/latest")
def sentiment_latest(ticker: str):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT bucket, vw_sentiment, n_posts, pos_ct, neu_ct, neg_ct
        FROM cagg_10s_sentiment
        WHERE ticker = %s
        ORDER BY bucket DESC
        LIMIT 1
    """, (ticker,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return dict(result) if result else {}

@app.get("/posts/similar")
def posts_similar(id: int, k: int = 10):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("SELECT embedding FROM posts WHERE id = %s", (id,))
    result = cur.fetchone()
    
    if not result:
        cur.close()
        conn.close()
        return []
    
    query_embedding = result['embedding']
    
    cur.execute("""
        SELECT id, title, source, created_at, tickers, stance
        FROM posts
        WHERE id != %s
        ORDER BY embedding <-> %s::vector
        LIMIT %s
    """, (id, query_embedding, k))
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(r) for r in results]

@app.get("/metrics/pipeline")
def metrics_pipeline():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT COUNT(*) as last_5m_count
        FROM posts
        WHERE ingested_at > now() - interval '5 minutes'
    """)
    count_result = cur.fetchone()
    
    cur.execute("""
        SELECT 
            EXTRACT(EPOCH FROM PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY classified_at - ingested_at)) as p95_latency_sec
        FROM posts
        WHERE classified_at IS NOT NULL
        AND classified_at > now() - interval '10 minutes'
        AND ingested_at > now() - interval '10 minutes'
        AND NOT COALESCE(is_backfill, false)
    """)
    latency_result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        "p95_latency_sec": round(latency_result['p95_latency_sec'] or 0, 2),
        "last_5m_count": count_result['last_5m_count'],
        "batched_avg_size": 32
    }

@app.get("/tickers")
def get_tickers(q: str = ""):
    conn = get_db()
    cur = conn.cursor()
    
    if q:
        cur.execute("SELECT symbol FROM tickers WHERE symbol LIKE %s LIMIT 20", (f"{q}%",))
    else:
        cur.execute("SELECT symbol FROM tickers LIMIT 100")
    
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    return results

@app.post("/ingest/replay")
def replay_backfill():
    from ingest_reddit import ingest_reddit_posts
    from ingest_rss import ingest_rss_feeds
    
    ingest_reddit_posts(backfill_hours=24)
    ingest_rss_feeds()
    
    return {"status": "backfill_complete"}