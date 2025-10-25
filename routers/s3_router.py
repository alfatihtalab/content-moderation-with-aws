import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
from aws_clients import upload_file
from aws_clients.s3 import create_bucket, s3
from schema import CreateBucket
from utils import generate_s3_key, S3_BUCKET, AWS_REGION

# Apply the dependency to the whole router
router = APIRouter(
    prefix="/s3-router",
    tags=["S3"]
)


@router.get("/get-all-buckets")
async def get_all_buckets():
    # Print out bucket names
    for bucket in s3.buckets.all():
        print(bucket.name)

@router.post("/")
async def create_s3_bucket(bucket: CreateBucket):
    is_created = create_bucket(bucket.name, bucket.region)

    return {"is_created": is_created}


@router.post("/upload-to-s3")
async def upload_to_s3(file: UploadFile = File(...)):
    """Endpoint to upload a file to S3."""
    try:
        # Save the uploaded file temporarily
        with NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Use the original filename for S3 object
        # object_name = file.filename
        object_name = generate_s3_key(file.filename)

        # Upload to S3
        success = upload_file(tmp_path, S3_BUCKET, object_name)

        # Delete temp file
        os.remove(tmp_path)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload to S3")

        file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
        return JSONResponse({"message": "File uploaded successfully", "url": file_url})

    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

