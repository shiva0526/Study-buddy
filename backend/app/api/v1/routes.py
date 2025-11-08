from fastapi import APIRouter
from . import user, plan, session, quizzes, revision

api_router = APIRouter()
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(plan.router, prefix="/plans", tags=["plans"])
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(revision.router, prefix="/revision", tags=["revision"])
