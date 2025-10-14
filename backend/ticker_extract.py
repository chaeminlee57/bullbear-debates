import re
import psycopg2
from settings import PG_DSN

STOPLIST = {'A', 'I', 'IT', 'CEO', 'CFO', 'CTO', 'COO', 'CIO', 'USA', 'US', 'UK', 'EU', 'AI', 'ML', 'API', 'IPO', 'ETF', 'USD', 'GDP', 'IMF', 'WTO'}

_ticker_map = None

def load_ticker_whitelist():
    global _ticker_map
    if _ticker_map is None:
        _ticker_map = {}
        conn = psycopg2.connect(PG_DSN)
        cur = conn.cursor()
        cur.execute("SELECT symbol FROM tickers")
        for row in cur.fetchall():
            symbol = row[0]
            _ticker_map[symbol.upper()] = symbol
            
            parts = symbol.lower().split()
            for part in parts:
                if len(part) > 2:
                    _ticker_map[part.upper()] = symbol
        
        cur.close()
        conn.close()
    return _ticker_map

def extract_tickers(text):
    if not text:
        return []
    
    ticker_map = load_ticker_whitelist()
    text_upper = text.upper()
    text_lower = text.lower()
    
    found = set()
    
    candidates = re.findall(r'\$?[A-Z]{1,5}\b', text_upper)
    for c in candidates:
        c = c.lstrip('$')
        if c in ticker_map and c not in STOPLIST:
            found.add(ticker_map[c])
    
    keywords = [
        'apple', 'microsoft', 'google', 'alphabet', 'amazon', 'nvidia', 'tesla',
        'meta', 'facebook', 'berkshire', 'visa', 'jpmorgan', 'walmart', 'mastercard',
        'exxon', 'johnson', 'home depot', 'chevron', 'merck', 'abbvie', 'coca-cola',
        'coke', 'pepsi', 'costco', 'broadcom', 'lilly', 'mcdonald', 'cisco',
        'accenture', 'abbott', 'adobe', 'nike', 'salesforce', 'verizon', 'wells fargo',
        'bristol myers', 'ups', 'honeywell', 'lowe', 'raytheon', 'qualcomm', 'intel',
        'amd', 'oracle', 'ibm', 'boeing'
    ]
    
    keyword_to_ticker = {
        'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
        'amazon': 'AMZN', 'nvidia': 'NVDA', 'tesla': 'TSLA', 'meta': 'META',
        'facebook': 'META', 'berkshire': 'BRK.B', 'visa': 'V', 'jpmorgan': 'JPM',
        'walmart': 'WMT', 'mastercard': 'MA', 'exxon': 'XOM', 'johnson': 'JNJ',
        'home depot': 'HD', 'chevron': 'CVX', 'merck': 'MRK', 'abbvie': 'ABBV',
        'coca-cola': 'KO', 'coke': 'KO', 'pepsi': 'PEP', 'costco': 'COST',
        'broadcom': 'AVGO', 'lilly': 'LLY', 'mcdonald': 'MCD', 'cisco': 'CSCO',
        'accenture': 'ACN', 'abbott': 'ABT', 'adobe': 'ADBE', 'nike': 'NKE',
        'salesforce': 'CRM', 'verizon': 'VZ', 'wells fargo': 'WFC',
        'bristol myers': 'BMY', 'ups': 'UPS', 'honeywell': 'HON', 'lowe': 'LOW',
        'raytheon': 'RTX', 'qualcomm': 'QCOM', 'intel': 'INTC', 'amd': 'AMD',
        'oracle': 'ORCL', 'ibm': 'IBM', 'boeing': 'BA'
    }
    
    for keyword in keywords:
        if keyword in text_lower:
            ticker = keyword_to_ticker.get(keyword)
            if ticker:
                found.add(ticker)
    
    return list(found)[:5]