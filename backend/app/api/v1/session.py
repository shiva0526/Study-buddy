# backend/app/api/v1/session.py
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List

from app.services.llm_client import generate_completion
from app.services.rag import retrieve_top_k_for_topic
from app.services.youtube import search_videos

logger = logging.getLogger(__name__)
router = APIRouter()


class SessionRequest(BaseModel):
    topic: str


@router.post("/start")
async def start_session(req: SessionRequest) -> Dict[str, Any]:
    """
    Start a study session for a topic.
    - Retrieves top-k supporting chunks (RAG)
    - Calls LLM to generate a lesson (summary, examples, practice question)
    - Fetches YouTube video suggestions asynchronously (non-blocking)
    Returns a dictionary with LLM response and `youtube` list.
    """
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    try:
        # 1) Retrieve supporting documents/snippets (RAG)
        docs: List[str] = await retrieve_top_k_for_topic(topic, k=3)

        # 2) Ask the LLM to produce a session package (structured JSON)
        resp = await generate_completion({"topic": topic, "context": docs}, mode="session", structured=True)

        # 3) Fetch YouTube recommendations without blocking event loop
        # search_videos is a synchronous function (requests); run it in a thread via asyncio.to_thread
        try:
            videos = await asyncio.to_thread(search_videos, topic, 3)
        except Exception as e:
            logger.exception("YouTube search failed: %s", e)
            videos = []

        # 4) Merge youtube results into the response
        if isinstance(resp, dict):
            resp_with_videos = dict(resp)
            resp_with_videos["youtube"] = videos
            return resp_with_videos
        else:
            # If generate_completion returned a non-dict (e.g., raw string), wrap it
            return {"raw": resp, "youtube": videos}

    except Exception as exc:
        logger.exception("start_session failed for topic '%s': %s", topic, exc)
        # Provide a helpful error to the client
        raise HTTPException(status_code=500, detail="Failed to start session. Check server logs for details.")
