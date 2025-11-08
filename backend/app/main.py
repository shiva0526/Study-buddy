import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import api_router
from app.db.session import init_db

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="StudyBuddy AI Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/api/health")
async def health():
    return {"status": "ok"}

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
