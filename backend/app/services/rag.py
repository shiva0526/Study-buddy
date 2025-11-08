import json, math
from app.db.session import async_session
from app.db.models import Embedding, Chunk
from sqlmodel import select

def cosine_similarity(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb + 1e-9)

async def retrieve_top_k_for_topic(topic: str, k=3):
    """Mock retrieval; in production, use embeddings."""
    async with async_session() as session:
        q = await session.execute(select(Chunk))
        all_chunks = q.scalars().all()
        results = []
        for c in all_chunks:
            results.append({"text": c.text})
        return [r["text"] for r in results[:k]]
