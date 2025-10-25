import boto3
from aws_clients import upload_file
from utils import AWS_REGION, S3_BUCKET

comprehend = boto3.client("comprehend", region_name=AWS_REGION)



def upload_file_to_s3(local_path: str, s3_key: str) -> str:
    """Upload local file to S3 and return its URI"""
    upload_file(local_path, S3_BUCKET, s3_key)
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"



def detect_bad_content(text: str, allow_pii: bool = False) -> bool:
    """
    Use Amazon Comprehend to detect PII, toxic, or negative content.
    Return True if content is bad (should be blocked).

    :param text: The text to analyze.
    :param allow_pii: If True, PII will not cause rejection.
                      If False, PII will trigger content rejection.
    """

    # Detect PII (Personally Identifiable Information)
    pii_resp = comprehend.detect_pii_entities(Text=text, LanguageCode="en")
    has_pii = bool(pii_resp.get("Entities"))

    # Detect Sentiment
    sentiment_resp = comprehend.detect_sentiment(Text=text, LanguageCode="en")
    sentiment = sentiment_resp.get("Sentiment", "NEUTRAL")

    # Optionally detect toxicity (if available in the region)
    try:
        toxic_resp = comprehend.detect_toxic_content(TextSegments=[{"Text": text}])
        toxic_labels = toxic_resp["ResultList"][0].get("Labels", [])
        toxic_confidence = any(l["Score"] > 0.7 for l in toxic_labels)
    except Exception:
        toxic_confidence = False  # fallback for regions without this API

    # --- Moderation Logic ---
    if allow_pii:
        # Ignore PII, only check for toxicity or negative sentiment
        is_bad = sentiment == "NEGATIVE" or toxic_confidence
    else:
        # Block if PII, negative sentiment, or toxic content
        is_bad = has_pii or sentiment == "NEGATIVE" or toxic_confidence

    return is_bad



# def detect_bad_content(text: str) -> bool:
#     """
#     Use Comprehend to detect PII or toxic / negative content.
#     Return True if content is bad.
#     """
#
#     # Detect PII
#     #PII stands for Personally Identifiable Information.
#     pii_resp = comprehend.detect_pii_entities(Text=text, LanguageCode="en")
#     has_pii = bool(pii_resp.get("Entities"))
#
#     # Detect Sentiment
#     sentiment_resp = comprehend.detect_sentiment(Text=text, LanguageCode="en")
#     sentiment = sentiment_resp.get("Sentiment", "NEUTRAL")
#
#     # Optionally detect toxicity (if available in region)
#     try:
#         toxic_resp = comprehend.detect_toxic_content(
#             TextSegments=[{"Text": text}]
#         )
#         toxic_labels = toxic_resp["ResultList"][0].get("Labels", [])
#         toxic_confidence = any(l["Score"] > 0.7 for l in toxic_labels)
#     except Exception:
#         toxic_confidence = False  # fallback for regions without this API
#
#     # Define your moderation logic
#     is_bad = has_pii or sentiment == "NEGATIVE" or toxic_confidence
#     return is_bad


