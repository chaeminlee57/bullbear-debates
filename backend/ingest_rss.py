import feedparser
import psycopg2
import hashlib
import time
from datetime import datetime
from pathlib import Path
from settings import PG_DSN
from ticker_extract import extract_tickers
from embed import get_embedding

def get_text_hash(text):
    normalized = ''.join(text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()

def ingest_rss_feeds():
    feeds_file = Path(__file__).parent.parent / 'data' / 'seeds' / 'feeds.txt'
    
    with open(feeds_file) as f:
        feed_urls = [line.strip() for line in f if line.strip()]
    
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    for feed_url in feed_urls:
        try:
            print(f"Fetching {feed_url}...")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:50]:
                try:
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    text = f"{title} {summary}"
                    
                    txt_hash = get_text_hash(text)
                    tickers = extract_tickers(text)
                    
                    if not tickers:
                        continue
                    
                    embedding = get_embedding(text[:512])
                    
                    external_id = entry.get('id', entry.get('link', ''))
                    url = entry.get('link', '')
                    
                    pub_date = entry.get('published_parsed') or entry.get('updated_parsed')
                    if pub_date:
                        created_time = datetime(*pub_date[:6])
                    else:
                        created_time = datetime.now()
                    
                    cur.execute("""
                        INSERT INTO posts 
                        (source, external_id, created_at, title, body, url, tickers, txt_hash, embedding, score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source, external_id, created_at) DO NOTHING
                        RETURNING id
                    """, (
                        'rss', external_id, created_time, title, summary, url, 
                        tickers, txt_hash, embedding, 1
                    ))
                    
                    result = cur.fetchone()
                    if result:
                        post_id = result[0]
                        for ticker in tickers:
                            cur.execute("""
                                INSERT INTO ticker_posts (created_at, post_id, ticker, score, comments)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                            """, (created_time, post_id, ticker, 1, 0))
                    
                except Exception as e:
                    print(f"Error processing RSS entry: {e}")
                    continue
        
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            continue
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    print("Starting RSS ingestion...")
    
    while True:
        try:
            ingest_rss_feeds()
            print(f"RSS poll complete at {datetime.now()}")
        except Exception as e:
            print(f"Error in RSS polling: {e}")
        time.sleep(60)