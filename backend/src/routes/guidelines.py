from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Any, Dict

from google.cloud import storage

from routes.auth import get_current_user
from config import settings

router = APIRouter()


@router.get("/pdf/{filename}")
async def get_guideline_pdf(
    filename: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    try:
        client = storage.Client()
        bucket = client.bucket(settings.BUCKET_NAME)
        blob = bucket.blob(filename)
        if not blob.exists():
            raise HTTPException(status_code=404, detail="PDF not found")
        pdf_bytes = blob.download_as_bytes()
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
