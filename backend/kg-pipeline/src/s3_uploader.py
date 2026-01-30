import os
import boto3

def get_s3_client():
    """Create boto3 S3 client configured for MinIO"""
    endpoint_url = os.getenv('MINIO_APP_ENDPOINT')
    access_key = os.getenv('MINIO_APP_USER')
    secret_key = os.getenv('MINIO_APP_PASSWORD')

    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='us-east-1',  # MinIO ignores region
        config=boto3.session.Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}  # MinIO compatibility
        )
    )
    return s3