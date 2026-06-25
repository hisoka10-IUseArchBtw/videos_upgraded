from pydantic import BaseModel, EmailStr
import uuid

# Request model for creating a user
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# Response model to send back to the user (excluding password)
class UserResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str

    class Config:
        from_attributes = True
