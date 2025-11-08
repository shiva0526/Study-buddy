# backend/app/services/llm_client.py
import os
import re
import json
import time
import hashlib
import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Thread pool for running sync OpenAI calls without blocking asyncio event loop
_EXECUTOR = ThreadPoolExecutor(max_workers=4)

# Config from env (also loaded via your settings module if you prefer)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMB_DIM = int(os.getenv("EMB_DIM", "256"))

# If you prefer to import settings from app.core.settings:
# from app.core.settings import settings
# OPENAI_API_KEY = settings.OPENAI_API_KEY
# EMB_DIM = settings.EMB_DIM

# ---- Utilities ----
def is_api_available() -> bool:
    return bool(OPENAI_API_KEY)

def _mock_vector(text: str, dim: int = EMB_DIM) -> List[float]:
    """Deterministic pseudo-embedding fallback (sha256-based)."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vec = []
    i = 0
    while len(vec) < dim:
        vec.append((h[i % len(h)] / 255.0))
        i += 1
    return vec

def _safe_json_extract(text: str) -> Optional[Union[dict, list]]:
    """
    Try many strategies to extract JSON from LLM text:
     - ```json ... ```
     - plain JSON in response
    Returns parsed JSON or None.
    """
    if not text:
        return None
    # Try fenced json
    m = re.search(r"```json(.*?)```", text, re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass
    # Try triple backticks block (any)
    m2 = re.search(r"```(?:json)?(.*?)```", text, re.S | re.I)
    if m2:
        try:
            return json.loads(m2.group(1).strip())
        except Exception:
            pass
    # Try to find a JSON object in text
    m3 = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    if m3:
        candidate = m3.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # Last attempt: direct parse
    try:
        return json.loads(text)
    except Exception:
        return None

# ---- OpenAI wrappers (sync functions executed in thread pool) ----
def _openai_create_embedding_sync(text: str, model: str = "text-embedding-3-small"):
    import openai
    openai.api_key = OPENAI_API_KEY
    return openai.Embedding.create(model=model, input=text)

def _openai_chat_complete_sync(messages: List[dict], model: str = "gpt-4o-mini", max_tokens: int = 800):
    import openai
    openai.api_key = OPENAI_API_KEY
    # Uses ChatCompletion endpoint
    return openai.ChatCompletion.create(model=model, messages=messages, max_tokens=max_tokens)

# ---- Public API ----
async def get_embedding(text: str, max_retries: int = 3, backoff_factor: float = 0.5) -> List[float]:
    """
    Returns a float vector (embedding). Uses OpenAI embeddings when available, otherwise deterministic mock.
    Uses retries with exponential backoff on transient errors.
    """
    if not is_api_available():
        logger.info("OpenAI key not found — returning mock embedding")
        return _mock_vector(text)

    attempt = 0
    while attempt < max_retries:
        try:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(_EXECUTOR, _openai_create_embedding_sync, text)
            # new openai structure: resp["data"][0]["embedding"]
            emb = resp["data"][0]["embedding"]
            # Sometimes embedding length differs; cast to list of floats
            return [float(x) for x in emb]
        except Exception as e:
            attempt += 1
            wait = backoff_factor * (2 ** (attempt - 1))
            logger.warning("OpenAI embedding attempt %s failed: %s — retrying in %.1fs", attempt, e, wait)
            await asyncio.sleep(wait)
    logger.error("OpenAI embedding failed after %d attempts — returning mock", max_retries)
    return _mock_vector(text)

async def generate_completion(
    payload: Dict[str, Any],
    mode: str = "chat",
    structured: bool = False,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
) -> Any:
    """
    mode: "plan", "session", "quiz", "revision", "chat"
    payload: context dict (topic, snippets, num, plan_id etc.)
    structured: try to parse JSON from the model response and return a dict/list
    """

    # Build system + user prompt based on mode
    system_prompt = (
        "You are StudyBuddy, an expert tutor and study planner. Provide concise, factual, and structured outputs"
    )

    # Prompt templates (kept concise; expand for better results)
    if mode == "plan":
        user_prompt = (
            "Create a study plan from the following inputs. "
            "Return JSON: { plan_id, summary, sessions: [{id,date,topic,objective,duration_min}] }.\n\n"
            f"Inputs: {json.dumps(payload)}"
        )
    elif mode == "session":
        user_prompt = (
            "Given the topic and supporting snippets, produce a short lesson summary, 2-3 examples, "
            "one practice question (with choices if MCQ) and a short explanation. Return as JSON.\n\n"
            f"Inputs: {json.dumps(payload)}"
        )
    elif mode == "quiz":
        user_prompt = (
            "Generate high-quality practice questions for the topic. Return JSON: {topic, questions: [{id,type,stem,choices,answer_index,model_answer,explanation}]}\n\n"
            f"Inputs: {json.dumps(payload)}"
        )
    elif mode == "revision":
        user_prompt = (
            "Create a short revision pack: concise notes and flashcards. Return JSON: {short_notes:[{topic,points}], flashcards:[{front,back}]}\n\n"
            f"Inputs: {json.dumps(payload)}"
        )
    else:
        user_prompt = f"User says: {json.dumps(payload)}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # If API not available, return deterministic mock based on mode
    if not is_api_available():
        logger.info("OpenAI not available — returning deterministic mock for mode: %s", mode)
        return _generate_mock(payload, mode)

    # Try chat completions with retries
    attempt = 0
    last_exc = None
    while attempt < max_retries:
        try:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(_EXECUTOR, _openai_chat_complete_sync, messages)
            # Extract text
            content = ""
            # support both "choices" with "message" or "text"
            choice = resp.get("choices", [{}])[0]
            if "message" in choice:
                content = choice["message"].get("content", "")
            else:
                content = choice.get("text", "")
            if structured:
                parsed = _safe_json_extract(content)
                if parsed is not None:
                    return parsed
                # If structured expected but not found, still return raw with a marker
                return {"raw": content}
            return {"raw": content}
        except Exception as e:
            last_exc = e
            attempt += 1
            wait = backoff_factor * (2 ** (attempt - 1))
            logger.warning("OpenAI chat attempt %d failed: %s — retrying in %.1fs", attempt, e, wait)
            await asyncio.sleep(wait)

    # After retries, fallback to mock but keep the error info
    logger.error("OpenAI generate_completion failed after %d attempts: %s", max_retries, last_exc)
    mock = _generate_mock(payload, mode)
    return {"mock": mock, "error": str(last_exc)}

# ---- Deterministic mock generator (keeps behaviour predictable) ----
def _generate_mock(payload: Dict[str, Any], mode: str):
    topic = payload.get("topic") or payload.get("plan_id") or "General"
    if mode == "quiz":
        num = int(payload.get("num", 3))
        questions = []
        for i in range(num):
            questions.append({
                "id": f"q{i+1}",
                "type": "mcq",
                "stem": f"Sample question {i+1} on {topic}",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 0,
                "model_answer": "A",
                "explanation": f"Mock explanation for question {i+1}."
            })
        return {"topic": topic, "questions": questions}
    if mode == "session":
        return {
            "summary": f"Demo summary for {topic}.",
            "examples": [f"Example 1 for {topic}", f"Example 2 for {topic}"],
            "practice_question": {"id": "q1", "type": "mcq", "stem": f"What is {topic}?", "choices": ["A","B"], "answer_index": 0}
        }
    if mode == "revision":
        return {"short_notes":[{"topic":topic,"points":["p1","p2"]}], "flashcards":[{"front":topic,"back":"keypoint"}]}
    if mode == "plan":
        return {"plan_id":"mock-plan","summary":f"7-day plan for {topic}","sessions":[]}
    return {"reply": f"Mock reply for {mode}"}
