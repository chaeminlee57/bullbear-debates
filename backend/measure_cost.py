import time
import psycopg2
from settings import PG_DSN
from classify_onnx import classify_batch

CPU_COST_PER_HOUR = 0.05

def measure_baseline(texts):
    start = time.time()
    
    for text in texts:
        classify_batch([text])
    
    elapsed = time.time() - start
    return elapsed

def measure_batched(texts, batch_size=32):
    start = time.time()
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        classify_batch(batch)
    
    elapsed = time.time() - start
    return elapsed

def main():
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT title, body 
        FROM posts 
        WHERE created_at > now() - interval '1 day'
        LIMIT 10000
    """)
    
    rows = cur.fetchall()
    texts = [f"{title or ''} {body or ''}" for title, body in rows]
    
    if len(texts) < 1000:
        print(f"Warning: Only {len(texts)} texts available. Need at least 1000.")
        return
    
    texts = texts[:10000]
    n = len(texts)
    
    print(f"Measuring baseline (unbatched) with {n} texts...")
    baseline_time = measure_baseline(texts[:100])
    baseline_time_full = baseline_time * (n / 100)
    
    print(f"Measuring batched (batch_size=32) with {n} texts...")
    batched_time = measure_batched(texts, batch_size=32)
    
    baseline_per_1k = (baseline_time_full / n) * 1000
    batched_per_1k = (batched_time / n) * 1000
    
    baseline_cost_per_1k = (baseline_per_1k / 3600) * CPU_COST_PER_HOUR
    batched_cost_per_1k = (batched_per_1k / 3600) * CPU_COST_PER_HOUR
    
    reduction_pct = ((baseline_cost_per_1k - batched_cost_per_1k) / baseline_cost_per_1k) * 100
    
    print("\n" + "="*60)
    print("COST MEASUREMENT RESULTS")
    print("="*60)
    print(f"Sample size: {n} texts")
    print(f"\nBaseline (unbatched):")
    print(f"  Time per 1k: {baseline_per_1k:.2f}s")
    print(f"  Cost per 1k: ${baseline_cost_per_1k:.6f}")
    print(f"\nOptimized (batched ONNX):")
    print(f"  Time per 1k: {batched_per_1k:.2f}s")
    print(f"  Cost per 1k: ${batched_cost_per_1k:.6f}")
    print(f"\nCost reduction: {reduction_pct:.1f}%")
    print("="*60)
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
