from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, status

from app.api.deps import get_current_user
from app.models.auth import User
from app.schemas.response import APIResponse
from app.services.storage.s3_service import S3StorageService

router = APIRouter()

@router.post("/logo", response_model=APIResponse[Dict[str, Any]])
async def upload_logo_attachment(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    category_query: Optional[str] = Query(None, alias="category"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a company or branch logo attachment to AWS S3 (with local media fallback).
    Accepts category via form-data or URL query parameter ("companies" | "branches").
    """
    cat = category or category_query or "companies"
    if cat not in ["companies", "branches"]:
        cat = "companies"

    result = await S3StorageService.upload_image(file=file, category=cat)
    return APIResponse(
        data=result,
        message=f"Logo uploaded successfully ({result.get('storage', 'cloud').upper()})"
    )
