import boto3
from botocore.exceptions import ClientError

from app.config.settings import settings

s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


def upload_file_to_s3(file_bytes: bytes, key: str, content_type: str) -> str:
    """Upload bytes to S3 and return the public URL."""
    s3_client.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def generate_presigned_url(key: str, expiry: int = 3600) -> str:
    """Generate a presigned URL for temporary download access."""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
        ExpiresIn=expiry,
    )
