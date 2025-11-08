import json
from fastapi import APIRouter, Form, UploadFile, File
from typing import List, Optional
from app.db.session import async_session
from app.db.models import Plan, Resource, Chunk, Embedding, Question
from app.utils.file_utils import save_upload_file
from app.services.extractor import extract_text
from app.services.chunker import chunk_text
from app.services.llm_client import get_embedding, generate_completion

router = APIRouter()

@router.post("/create")
async def create_plan(
    username: str = Form(...),
    subject: str = Form(...),
    exam_date: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
):
    async with async_session() as session:
        plan = Plan(user_id=username, subject=subject, exam_date=exam_date, status="indexing")
        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        # Process uploaded files
        if files:
            for upload in files:
                filepath = save_upload_file(upload, plan.id)
                resource = Resource(plan_id=plan.id, filename=upload.filename, filepath=filepath)
                session.add(resource)
                await session.commit()

                # Extract and chunk
                text = extract_text(filepath)
                chunks = chunk_text(text)
                for i, ch in enumerate(chunks):
                    chunk = Chunk(resource_id=resource.id, chunk_index=i, text=ch["text"])
                    session.add(chunk)
                    await session.commit()
                    await session.refresh(chunk)

                    # Embeddings
                    vec = get_embedding(ch["text"])
                    emb = Embedding(chunk_id=chunk.id, vector=json.dumps(vec))
                    session.add(emb)
                    await session.commit()

        # Generate mock questions
        questions = generate_completion({"topic": subject}, mode="quiz", structured=True)
        for q in questions["questions"]:
            question = Question(plan_id=plan.id, topic=subject, stem=q["stem"],
                                choices=json.dumps(q["choices"]), answer_index=q["answer_index"],
                                explanation=q["explanation"])
            session.add(question)
        plan.status = "ready"
        await session.commit()
        return {"plan_id": plan.id, "status": "ready", "summary": f"Plan created for {subject}"}
