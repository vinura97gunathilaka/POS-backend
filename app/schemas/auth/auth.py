from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    is_superadmin: bool
    company_id: int
    roles: List[str] = []
    permissions: List[str] = []

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    type: Optional[str] = None
    company_id: Optional[int] = None

class LoginPayload(BaseModel):
    username: EmailStr
    password: str

class ForgotPasswordPayload(BaseModel):
    email: EmailStr

class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str
