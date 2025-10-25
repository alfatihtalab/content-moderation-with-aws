import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from aws_clients import detect_bad_content, upload_file_to_s3
from schema import TextInput

# Apply the dependency to the whole router
router = APIRouter(
    prefix="/text-moderation",
    tags=["text-moderation"]
)





@router.post("/")
async def moderate_text(input_data: TextInput):
    """
    Moderates text before writing/uploading to S3.
    If the text passes moderation → it is saved, uploaded, and URL returned.
    If it fails → rejected before upload.
    """
    try:
        text = input_data.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Apply moderation FIRST
        is_bad = detect_bad_content(text)
        if is_bad:
            return JSONResponse(
                {
                    "status": "rejected",
                    "reason": "Content failed moderation sorry!",
                    "action": "Not uploaded",
                    "uploaded": False,
                },
                status_code=200,
            )

        # Only if content is safe, write to a temp file
        filename = f"{uuid.uuid4()}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)

        # Generate S3 key
        s3_key = f"txt/{filename}"

        # Upload file
        file_url = upload_file_to_s3(filename, s3_key)

        # Delete temp file locally
        os.remove(filename)

        # Return success
        return JSONResponse(
            {
                "status": "approved",
                "message": "Content passed moderation and uploaded, thank you!",
                "file_url": file_url,
                "uploaded": True,
            },
            status_code=200,
        )

    except Exception as e:
        logging.error(f"Moderation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


