import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf", "text/plain", "audio/mpeg", "video/mp4"
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_MIME", "message": f"File type '{file.content_type}' is not allowed"}
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "FILE_TOO_LARGE", "message": "File size exceeds 5MB limit"}
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"/uploads/{filename}"
    return {
        "file_url": file_url,
        "filename": file.filename,
        "mime_type": file.content_type,
        "size_bytes": len(content)
    }
