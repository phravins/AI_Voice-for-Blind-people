import logging
import re

logger = logging.getLogger(__name__)

def clean_text(text):
    """Cleans extracted text by removing extra spaces, newlines, etc."""
    if not text:
        return ""
    # Replace multiple spaces/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()

def get_text_chunk(doc_structure, page_num, chunk_index=0):
    """Retrieves a specific text chunk from the document structure."""
    # Support dict keys that may be strings (due to session JSON serialization)
    key_int = page_num
    key_str = str(page_num)
    page_chunks = doc_structure.get(key_int)
    if page_chunks is None:
        page_chunks = doc_structure.get(key_str)
    if page_chunks is None:
        logger.warning(f"Page number {page_num} not found in document structure.")
        return None
    if chunk_index < 0 or chunk_index >= len(page_chunks):
        logger.warning(f"Chunk index {chunk_index} is out of range for page {page_num}.")
        return None
    return page_chunks[chunk_index]

def combine_doc_text(doc_structure, max_chars=None):
    pages = []
    # Normalize ordering: sort by numeric page index when possible
    def _to_int(k):
        try:
            return int(k)
        except Exception:
            return k
    for i in sorted(doc_structure.keys(), key=_to_int):
        chunks = doc_structure.get(i)
        if chunks is None:
            chunks = doc_structure.get(str(i))
        if chunks:
            pages.append(" ".join([c for c in chunks if c]))
    full = "\n\n".join(pages)
    if max_chars is not None and len(full) > max_chars:
        return full[:max_chars]
    return full
