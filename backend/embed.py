import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer

_session = None
_tokenizer = None

def init_embed_model():
    global _session, _tokenizer
    if _session is None:
        from settings import EMBED_ONNX_PATH
        _session = ort.InferenceSession(EMBED_ONNX_PATH)
        _tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

def get_embedding(text):
    init_embed_model()
    
    inputs = _tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors='np'
    )
    
    ort_inputs = {
        'input_ids': inputs['input_ids'].astype(np.int64),
        'attention_mask': inputs['attention_mask'].astype(np.int64)
    }
    
    if 'token_type_ids' in inputs:
        ort_inputs['token_type_ids'] = inputs['token_type_ids'].astype(np.int64)
    
    outputs = _session.run(None, ort_inputs)
    
    embedding = outputs[0].mean(axis=1)[0]
    
    return embedding.tolist()