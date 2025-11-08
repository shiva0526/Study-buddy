def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        chunks.append({"text": chunk})
        start += chunk_size - overlap
    return chunks
