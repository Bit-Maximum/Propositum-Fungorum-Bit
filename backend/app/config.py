import json
import os
import logging


class Config:
    def __init__(self):

        self.minio_endpoint = os.getenv("MINIO_APP_ENDPOINT")
        self.minio_user = os.getenv("MINIO_APP_USER")
        self.minio_password = os.getenv("MINIO_APP_PASSWORD")
        self.bucket_name = os.getenv("MINIO_APP_BUCKET_NAME")

        self.logger = logging.getLogger("app")

    def check_config(self):
        missing = []

        required_vars = {
            "MINIO_APP_ENDPOINT": self.minio_endpoint,
            "MINIO_APP_USER": self.minio_user,
            "MINIO_APP_PASSWORD": self.minio_password,
            "MINIO_APP_BUCKET_NAME": self.bucket_name,
        }

        for name, value in required_vars.items():

            if value is None or (isinstance(value, (list, tuple, set)) and not value):
                missing.append(name)
            elif isinstance(value, str) and not value.strip():
                missing.append(name)

        if missing:
            self.logger.error(
                f"Missing required configuration variables: {', '.join(missing)}"
            )
            raise ValueError(
                f"Missing required configuration variables: {', '.join(missing)}"
            )


        self.logger.info("JSON Verifier config validation passed ✅")


config = Config()
