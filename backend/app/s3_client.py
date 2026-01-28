from io import BytesIO
from typing import Optional

from backend.app.config import config

import boto3
from botocore.exceptions import ClientError


class S3MemoryClient:
    """
    Клиент для работы с S3 полностью в памяти (in-memory).
    """

    def __init__(
        self,
        bucket_name: str,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.bucket_name = bucket_name

        self.s3 = boto3.client(
            "s3",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url,
        )

    def upload_bytes(
        self,
        data: bytes,
        s3_key: str,
        content_type: Optional[str] = None,
    ) -> None:
        """
        Загружает байты в S3.

        :param data: содержимое файла в виде bytes
        :param s3_key: ключ объекта в S3
        :param content_type: MIME-type (опционально)
        """
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                **extra_args,
            )
        except ClientError as e:
            raise RuntimeError(f"Ошибка загрузки bytes в S3: {e}") from e

    def upload_stream(
        self,
        stream: BytesIO,
        s3_key: str,
        content_type: Optional[str] = None,
    ) -> None:
        """
        Загружает BytesIO-стрим в S3.
        """
        stream.seek(0)

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.s3.upload_fileobj(
                Fileobj=stream,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args or None,
            )
        except ClientError as e:
            raise RuntimeError(f"Ошибка загрузки stream в S3: {e}") from e

    def download_bytes(self, s3_key: str) -> bytes:
        """
        Скачивает объект из S3 и возвращает bytes.
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return response["Body"].read()
        except ClientError as e:
            raise RuntimeError(f"Ошибка скачивания bytes из S3: {e}") from e

    def download_stream(self, s3_key: str) -> BytesIO:
        """
        Скачивает объект из S3 и возвращает BytesIO.
        """
        buffer = BytesIO()

        try:
            self.s3.download_fileobj(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fileobj=buffer,
            )
            buffer.seek(0)
            return buffer
        except ClientError as e:
            raise RuntimeError(f"Ошибка скачивания stream из S3: {e}") from e

    def object_exists(self, s3_key: str) -> bool:
        """
        Проверяет существование объекта в S3.
        """
        try:
            self.s3.head_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return True
        except ClientError:
            return False

# Example of usage
if __name__ == "__main__":
    client = S3MemoryClient(
        bucket_name=config.bucket_name,
        region_name="us-east-2",
        aws_access_key_id=config.minio_user,
        aws_secret_access_key=config.minio_password,
        endpoint_url=config.minio_endpoint
    )

    buffer = BytesIO(b"binary-data")
    client.upload_stream(buffer, "bin/data.bin")