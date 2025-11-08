from fastapi import APIRouter
from pydantic import BaseModel
from app.services.llm_client import generate_completion

router = APIRouter()

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

@router.post("/generate")
async def generate_quiz(req: QuizRequest):
    return generate_completion({"topic": req.topic, "num": req.num_questions}, mode="quiz", structured=True)

class SubmitRequest(BaseModel):
    answers: list[int]

@router.post("/submit")
async def submit_quiz(req: SubmitRequest):
    score = sum(1 for a in req.answers if a == 0)
    return {"score": score, "feedback": "Mock grading complete", "xp_earned": score * 10}
