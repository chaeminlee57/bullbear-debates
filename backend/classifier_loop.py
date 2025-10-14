import psycopg2
import psycopg2.extras
import json
import time
from datetime import datetime
from settings import PG_DSN, BATCH_SIZE
from classify_onnx import classify_batch

def classify_unprocessed_posts():
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT id, title, body, tickers, created_at
        FROM posts
        WHERE stance IS NULL
        AND created_at > now() - interval '24 hours'
        AND NOT COALESCE(is_backfill, false)
        ORDER BY ingested_at DESC
        LIMIT %s
    """, (BATCH_SIZE,))
    
    posts = cur.fetchall()
    
    if not posts:
        cur.close()
        conn.close()
        return 0
    
    texts = [f"{p['title'] or ''} {p['body'] or ''}" for p in posts]
    results = classify_batch(texts)
    
    update_cur = conn.cursor()
    for post, result in zip(posts, results):
        update_cur.execute("""
            UPDATE posts
            SET stance = %s, probs = %s, model_ver = %s, classified_at = now()
            WHERE id = %s
        """, (
            result['stance'],
            json.dumps(result['probs']),
            'finbert-onnx-v1',
            post['id']
        ))
        
        for ticker in post['tickers']:
            update_cur.execute("""
                UPDATE ticker_posts
                SET stance = %s
                WHERE post_id = %s AND ticker = %s
            """, (result['stance'], post['id'], ticker))
    
    conn.commit()
    update_cur.close()
    cur.close()
    conn.close()
    
    return len(posts)

if __name__ == '__main__':
    print("Starting classification loop...")
    
    while True:
        try:
            count = classify_unprocessed_posts()
            if count > 0:
                print(f"Classified {count} posts at {datetime.now()}")
        except Exception as e:
            print(f"Error in classification loop: {e}")
        time.sleep(0.1)