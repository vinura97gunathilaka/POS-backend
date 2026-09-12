from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: Optional[str] = None
    employee_id: Optional[str] = None
    is_superadmin: bool
    must_change_password: bool = False
    company_id: Optional[int] = None
    roles: List[str] = []
    permissions: List[str] = []

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    type: Optional[str] = None
    company_id: Optional[int] = None

class LoginPayload(BaseModel):
    username: str
    password: str

class ForgotPasswordPayload(BaseModel):
    email: EmailStr

class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str

class ChangeInitialPasswordPayload(BaseModel):
    current_password: str
    new_password: str
