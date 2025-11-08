from fastapi import APIRouter
from app.services.llm_client import generate_completion

router = APIRouter()

@router.post("/generate")
async def generate_revision():
    data = generate_completion({}, mode="revision", structured=True)
    return {"revision_pack": data}
