from fastapi import APIRouter
from app.db.session import async_session
from app.db.models import User
from sqlmodel import select

router = APIRouter()

@router.get("/{username}")
async def get_user(username: str):
    async with async_session() as session:
        q = await session.execute(select(User).where(User.username == username))
        user = q.scalar_one_or_none()
        if user:
            return user
        new = User(username=username)
        session.add(new)
        await session.commit()
        await session.refresh(new)
        return new
