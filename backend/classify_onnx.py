import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer

_session = None
_tokenizer = None

def init_classifier():
    global _session, _tokenizer
    if _session is None:
        from settings import ONNX_MODEL_PATH
        _session = ort.InferenceSession(ONNX_MODEL_PATH)
        _tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')

def classify_batch(texts):
    init_classifier()
    
    inputs = _tokenizer(
        texts,
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
    logits = outputs[0]
    
    probs = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
    
    results = []
    for i, prob_row in enumerate(probs):
        stance_map = {0: -1, 1: 0, 2: 1}
        predicted_class = int(np.argmax(prob_row))
        stance = stance_map[predicted_class]
        
        results.append({
            'stance': stance,
            'probs': {
                'neg': float(prob_row[0]),
                'neu': float(prob_row[1]),
                'pos': float(prob_row[2])
            }
        })
    
    return results