import os
import time
import uuid
import boto3
import logging
import requests
from botocore.exceptions import ClientError

from utils import AWS_REGION

#Speech to Text Service - Amazon Transcribe


transcribe = boto3.client('transcribe', region_name=AWS_REGION)



#

def transcribe_voice_file(
    file_uri: str,
    language_code: str = "en-US",
    output_bucket: str = None,
    wait: bool = True,
) -> str:
    """
    Convert voice (audio file) to text using Amazon Transcribe.

    Args:
        file_uri (str): URI to the audio file.
                        Can be a local path or an S3 URI (s3://bucket/file.mp3)
        language_code (str): Language code, default 'en-US'
        output_bucket (str): Optional S3 bucket for storing transcription result.
        wait (bool): If True, waits for job completion and returns transcription text.

    Returns:
        str: Transcribed text if wait=True, otherwise the Transcribe job name.
    """

    job_name = f"transcribe-job-{uuid.uuid4()}"
    logging.info(f"Starting Transcribe job: {job_name}")

    # Handle local files by uploading to S3 first
    if not file_uri.startswith("s3://"):
        raise ValueError("Transcribe requires an S3 URI. Upload the file first.")

    try:
        start_params = {
            "TranscriptionJobName": job_name,
            "Media": {"MediaFileUri": file_uri},
            "MediaFormat": os.path.splitext(file_uri)[1].lstrip(".").lower(),
            "LanguageCode": language_code,
        }
        if output_bucket:
            start_params["OutputBucketName"] = output_bucket

        transcribe.start_transcription_job(**start_params)

        if not wait:
            return job_name  # asynchronous mode

        # Wait until the job completes
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]

            if job_status in ["COMPLETED", "FAILED"]:
                break
            logging.info("Transcription in progress...")
            time.sleep(5)

        if job_status == "FAILED":
            reason = status["TranscriptionJob"].get("FailureReason", "Unknown error")
            raise RuntimeError(f"Transcription failed: {reason}")

        # Retrieve the transcript text
        transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

        # Download the transcript JSON

        resp = requests.get(transcript_uri)
        transcript_json = resp.json()
        transcript_text = transcript_json["results"]["transcripts"][0]["transcript"]

        logging.info(f"Transcription completed for {file_uri}")
        return transcript_text

    except ClientError as e:
        logging.error(f"AWS Transcribe error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

