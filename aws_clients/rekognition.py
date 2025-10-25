import time
import boto3
from utils import AWS_REGION

rekognition = boto3.client("rekognition", region_name=AWS_REGION)

SAFE_LABELS = {"Violence", "Graphic Violence"}
BLOCK_LABELS = {"Explicit Nudity", "Sexual Activity", "Hate Symbols"}

BLOCK_CATEGORIES = [
    "Explicit Nudity", "Suggestive", "Violence",
    "Visually Disturbing", "Weapons", "Drugs",
    "Alcohol", "Tobacco", "Hate Symbols", "Self-Harm"
]


# def moderate_image(bucket, key, threshold=70):
#     response = rekognition.detect_moderation_labels(
#         Image={"S3Object": {"Bucket": bucket, "Name": key}},
#         MinConfidence=threshold
#     )
#     labels = response["ModerationLabels"]
#     flagged = []
#     for label in labels:
#         parent = label.get("ParentName", "")
#         if parent in BLOCK_CATEGORIES and label["Confidence"] >= threshold:
#             flagged.append(f"{parent}/{label['Name']} ({label['Confidence']:.1f}%)")
#     return flagged



def moderate_image(bucket: str, key: str, threshold=70) -> bool:
    """Detect unsafe image content using Rekognition."""
    response = rekognition.detect_moderation_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}}
    )
    labels = response.get("ModerationLabels", [])
    print("labels:", labels)
    for label in labels:
        if label["Confidence"] > threshold:  # configurable threshold
            return True
    return False


def moderate_video(bucket: str, key: str) -> bool:
    """Start an async video moderation job."""
    job_id = rekognition.start_content_moderation(
        Video={"S3Object": {"Bucket": bucket, "Name": key}}
    )["JobId"]

    # Poll for result
    while True:
        result = rekognition.get_content_moderation(JobId=job_id)
        status = result["JobStatus"]
        if status in ["SUCCEEDED", "FAILED"]:
            break
        time.sleep(5)

    if status == "FAILED":
        raise RuntimeError("Video moderation failed")

    labels = result.get("ModerationLabels", [])
    for label in labels:
        if label["Confidence"] > 80:
            return True
    return False

