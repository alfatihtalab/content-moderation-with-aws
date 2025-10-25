from pydantic import BaseModel, field_validator
import re
from typing import Optional


class CreateBucket(BaseModel):
    name: str
    region: Optional[str] = "us-east-2"

    @field_validator('name')
    def validate_bucket_name(cls, v):
        # Check length
        if len(v) < 3 or len(v) > 63:
            raise ValueError('Bucket name must be between 3 and 63 characters')

        # Check for invalid characters
        if not re.match(r'^[a-z0-9.-]+$', v):
            raise ValueError('Bucket name can only contain lowercase letters, numbers, dots, and hyphens')

        # Check starts and ends with alphanumeric
        if not v[0].isalnum() or not v[-1].isalnum():
            raise ValueError('Bucket name must start and end with a letter or number')

        # Check for consecutive dots
        if '..' in v:
            raise ValueError('Bucket name cannot contain consecutive dots')

        # Check if it looks like an IP address
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', v):
            raise ValueError('Bucket name cannot be formatted as an IP address')

        return v

class TextInput(BaseModel):
    text: str