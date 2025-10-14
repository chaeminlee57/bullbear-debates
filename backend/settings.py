import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

env_path = BASE_DIR / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

PG_DSN = os.getenv('PG_DSN', 'postgresql://localhost:5432/bullbear')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_SECRET = os.getenv('REDDIT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'bullbear-min')
ONNX_MODEL_PATH = os.getenv('ONNX_MODEL_PATH', './backend/models/finbert.onnx')
EMBED_ONNX_PATH = os.getenv('EMBED_ONNX_PATH', './backend/models/minilm.onnx')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '32'))