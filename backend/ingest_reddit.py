import praw
import psycopg2
import psycopg2.extras
import hashlib
import time
from datetime import datetime
from settings import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER_AGENT, PG_DSN
from ticker_extract import extract_tickers
from embed import get_embedding

SUBREDDITS = ['stocks', 'investing', 'wallstreetbets', 'options', 'StockMarket', 
              'dividends', 'ValueInvesting', 'SecurityAnalysis', 'CanadianInvestor',
              'UKInvesting', 'ETFs', 'pennystocks', 'RobinHood', 'Daytrading',
              'swingtrading', 'algotrading', 'Fire', 'Bogleheads']

def get_text_hash(text):
    normalized = ''.join(text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()

def ingest_reddit_posts(backfill_hours=None):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    for sub_name in SUBREDDITS:
        subreddit = reddit.subreddit(sub_name)
        
        posts_to_fetch = []
        if backfill_hours:
            posts_to_fetch = list(subreddit.new(limit=200))
        else:
            posts_to_fetch = list(subreddit.new(limit=100)) + list(subreddit.hot(limit=100))
        
        for post in posts_to_fetch:
            try:
                text = f"{post.title} {post.selftext}"
                txt_hash = get_text_hash(text)
                tickers = extract_tickers(text)
                
                if not tickers:
                    continue
                
                embedding = get_embedding(text[:512])
                created_time = datetime.fromtimestamp(post.created_utc)
                
                cur.execute("""
                    INSERT INTO posts 
                    (source, external_id, created_at, title, body, url, subreddit, score, comments, tickers, txt_hash, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source, external_id, created_at) DO NOTHING
                    RETURNING id
                """, (
                    'reddit', post.id, created_time, post.title, post.selftext, 
                    post.url, sub_name, post.score, post.num_comments, tickers, 
                    txt_hash, embedding
                ))
                
                result = cur.fetchone()
                if result:
                    post_id = result[0]
                    for ticker in tickers:
                        cur.execute("""
                            INSERT INTO ticker_posts (created_at, post_id, ticker, score, comments)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (created_time, post_id, ticker, post.score, post.num_comments))
                
            except Exception as e:
                print(f"Error processing post {post.id}: {e}")
                continue
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    print("Running initial Reddit backfill...")
    ingest_reddit_posts(backfill_hours=24)
    print("Backfill complete. Starting live polling...")
    
    while True:
        try:
            ingest_reddit_posts()
            print(f"Reddit poll complete at {datetime.now()}")
        except Exception as e:
            print(f"Error in Reddit polling: {e}")
        time.sleep(30)