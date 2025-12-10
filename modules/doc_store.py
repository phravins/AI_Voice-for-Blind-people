import os
import json
import uuid
from typing import Dict, Any
from config import DOCS_DIR

def save(doc_structure: Dict[Any, Any], custom_id: str = None) -> str:
    doc_id = custom_id if custom_id else uuid.uuid4().hex
    path = os.path.join(DOCS_DIR, f"{doc_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc_structure, f, ensure_ascii=False)
    return doc_id

def load(doc_id: str) -> Dict[Any, Any]:
    path = os.path.join(DOCS_DIR, f"{doc_id}.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
