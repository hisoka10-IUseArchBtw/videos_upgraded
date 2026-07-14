from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from backend.core.database import get_db
from backend.models.User.user_model import User
from backend.auth.jwt import create_access_token, get_current_user

router = APIRouter(tags=["Authentication"])
password_hash = PasswordHash((Argon2Hasher(),))

@router.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not password_hash.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get('/users/me')
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": str(current_user.user_id),
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": getattr(current_user, "is_admin", False)
    }
