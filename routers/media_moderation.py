import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile

from aws_clients import detect_bad_content, upload_file, moderate_video, moderate_image
from aws_clients.s3 import delete_file
from aws_clients.transcribe import transcribe_voice_file
from utils import get_file_category, generate_s3_key, S3_BUCKET, AWS_REGION

# Apply the dependency to the whole router
router = APIRouter(
    prefix="/media-moderation",
    tags=["media-moderation"]
)




# ---------- ENDPOINT ----------
@router.post("/")
async def upload_media(file: UploadFile = File(...)):
    """
    Upload a media file to S3 and automatically moderate based on file type.
    """
    try:
        # Save file temporarily
        with NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Detect category and generate key
        category = get_file_category(file.filename)
        s3_key = generate_s3_key(file.filename)

        # Upload to S3
        success = upload_file(tmp_path, S3_BUCKET, s3_key)
        os.remove(tmp_path)
        if not success:
            raise HTTPException(status_code=500, detail="Upload to S3 failed")

        file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        logging.info(f"Uploaded {file.filename} as {s3_key}")

        # Voice moderation
        if category == "voice":
            text = transcribe_voice_file(s3_uri)
            if not text.strip():
                return JSONResponse(
                    {
                        "status": "no_content",
                        "category": category,
                        "message": "Voice file is silent or contains no speech.",
                        "file_url": file_url,
                    }
                )

            is_bad = detect_bad_content(text)
            if is_bad:
                delete_file(S3_BUCKET, s3_key)
                return JSONResponse(
                    {
                        "status": "rejected",
                        "category": category,
                        "reason": "Unsafe voice content",
                        "action": "File deleted",
                    }
                )
            return JSONResponse(
                {
                    "status": "approved",
                    "category": category,
                    "message": "Voice content safe",
                    "file_url": file_url,
                    "transcript": text,
                }
            )

        # Image moderation
        elif category == "image":
            is_bad = moderate_image(S3_BUCKET, s3_key, threshold=90)
            if is_bad:
                delete_file(S3_BUCKET, s3_key)
                return JSONResponse(
                    {
                        "status": "rejected",
                        "category": category,
                        "reason": "Unsafe image content",
                        "action": "File deleted",
                    }
                )
            return JSONResponse(
                {
                    "status": "approved",
                    "category": category,
                    "message": "Image content safe",
                    "file_url": file_url,
                }
            )

        # Video moderation
        elif category == "video":
            is_bad = moderate_video(S3_BUCKET, s3_key)
            if is_bad:
                delete_file(S3_BUCKET, s3_key)
                return JSONResponse(
                    {
                        "status": "rejected",
                        "category": category,
                        "reason": "Unsafe video content",
                        "action": "File deleted",
                    }
                )
            return JSONResponse(
                {
                    "status": "approved",
                    "category": category,
                    "message": "Video content safe",
                    "file_url": file_url,
                }
            )

        # Default for other file types (e.g. txt)
        else:
            return JSONResponse(
                {
                    "status": "uploaded",
                    "category": category,
                    "message": "File uploaded (no moderation applied).",
                    "file_url": file_url,
                }
            )

    except Exception as e:
        logging.error(f"Media upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
