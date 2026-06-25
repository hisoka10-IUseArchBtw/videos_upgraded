from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from backend.core.database import get_db
from backend.models.User.user_model import User
from backend.models.User.user_schema import UserCreate, UserResponse

router = APIRouter(tags=["Authentication"])
password_hash = PasswordHash((Argon2Hasher(),))

@router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    result_username = await db.execute(select(User).where(User.username == user.username))
    if result_username.scalars().first():
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = password_hash.hash(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user