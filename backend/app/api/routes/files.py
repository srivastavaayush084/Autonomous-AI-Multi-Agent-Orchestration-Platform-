import os
import uuid
import re
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.services.document_service import document_service

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None)
):
    """
    Secure file upload endpoint.
    Guards against path traversal, validates file size, stores physical file,
    and returns parsed metadata and preview text.
    """
    # 1. Sanitize filename
    clean_name = os.path.basename(file.filename or "upload.bin")
    clean_name = re.sub(r"[^\w\.\-\_]", "_", clean_name)
    file_id = f"file-{uuid.uuid4().hex[:12]}"
    saved_filename = f"{file_id}_{clean_name}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    # 2. Stream contents and enforce size limit
    size_bytes = 0
    try:
        with open(saved_path, "wb") as f:
            while chunk := await file.read(1024 * 64):  # 64 KB chunks
                size_bytes += len(chunk)
                if size_bytes > MAX_FILE_SIZE_BYTES:
                    f.close()
                    if os.path.exists(saved_path):
                        os.remove(saved_path)
                    raise HTTPException(status_code=413, detail="File exceeds maximum allowed size (50 MB)")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # 3. Extract text / metadata preview
    try:
        parsed_info = document_service.process_file(saved_path)
        preview_text = parsed_info.get("text", "")[:1000]
        file_type = parsed_info.get("file_type", "unknown")
    except Exception as e:
        preview_text = f"Uploaded successfully. Preview extraction error: {e}"
        file_type = "unknown"

    return JSONResponse(status_code=201, content={
        "file_id": file_id,
        "filename": clean_name,
        "file_path": saved_path,
        "file_type": file_type,
        "size_bytes": size_bytes,
        "preview": preview_text,
        "project_id": project_id
    })
