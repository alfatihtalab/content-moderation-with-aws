import os
import uuid

# Mapping of file extensions to content categories
FILE_TYPE_MAP = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
    "video": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
    "voice": [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"],
    "txt": [".txt", ".md", ".json", ".csv", ".log", ".pdf", ".docx"],
}


def get_file_category(filename: str) -> str:
    """
    Determine the file category based on its extension.

    Args:
        filename (str): The name of the file.

    Returns:
        str: One of ['image', 'video', 'voice', 'txt', 'other'].
    """
    ext = os.path.splitext(filename.lower())[1]
    for category, extensions in FILE_TYPE_MAP.items():
        if ext in extensions:
            return category
    return "other"


def generate_s3_key(filename: str) -> str:
    """
    Generate an S3 key (path) under directory [voice/, video/, image/, txt/]
    based on the file extension.

    Example:
        input: "my_photo.png"
        output: "image/62dbf3a9-b7e0-4b9a-8a92-79e4f25c58ef.png"

    Args:
        filename (str): The uploaded file name.

    Returns:
        str: A structured S3 key path.
    """
    category = get_file_category(filename)
    ext = os.path.splitext(filename)[1]
    unique_id = str(uuid.uuid4())
    return f"{category}/{unique_id}{ext}"

