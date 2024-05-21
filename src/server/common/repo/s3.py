import os
import tempfile
import shutil  # Import shutil for cross-platform file operations
import boto3
from pathlib import Path
from functools import lru_cache
from fastapi import HTTPException
import hashlib
from server.config import CONFIG


class S3Repo:
    def __init__(self, config=CONFIG):
        self.config = config
        self.s3 = boto3.client(
            service_name="s3",
            endpoint_url=config.AWS_S3_ENDPOINT,
            aws_access_key_id=config.AWS_S3_ACCESS_KEY,
            aws_secret_access_key=config.AWS_S3_SECRET_KEY,
        )
        self.cache_dir = Path(tempfile.gettempdir()) / "s3_cache"
        self.cache_dir.mkdir(exist_ok=True)

    @lru_cache(maxsize=128)
    def get_cached_path(self, key):
        cached_path = self.cache_dir / key
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        return cached_path

    def upload_file(self, file_path: str, key: str):
        try:
            self.s3.upload_file(file_path, self.config.AWS_S3_BUCKET, key)
        except boto3.exceptions.S3UploadFailedError as e:
            raise HTTPException(
                status_code=500, detail=f"R2 upload failed: {e}")

    def download_file(self, key: str, file_path: str):
        cached_path = self.get_cached_path(key)
        if cached_path.exists():
            # Check ETag in R2 to see if the file has changed
            try:
                r2_etag = self.s3.head_object(
                    Bucket=self.config.AWS_S3_BUCKET, Key=key
                )["ETag"][1:-1]
            except boto3.exceptions.ClientError as e:
                raise HTTPException(
                    status_code=404, detail=f"File not found in R2: {e}")

            hash_md5 = hashlib.md5()
            with open(cached_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            local_etag = hash_md5.hexdigest()

            if r2_etag == local_etag:
                shutil.copy2(cached_path, file_path)  # Copy with metadata
                return

        # If not cached or ETags don't match, download from R2
        try:
            self.s3.download_file(
                self.config.AWS_S3_BUCKET, key, str(cached_path)
            )
            shutil.copy2(cached_path, file_path)  # Copy with metadata
        except boto3.exceptions.S3DownloadFailedError as e:
            raise HTTPException(
                status_code=404, detail=f"File not found in R2: {e}")

    def delete_file(self, key: str):
        try:
            self.s3.delete_object(Bucket=self.config.AWS_S3_BUCKET, Key=key)
            cached_path = self.get_cached_path(key)
            if cached_path.exists():
                os.remove(cached_path)
        except boto3.exceptions.S3DeleteFailedError as e:
            raise HTTPException(
                status_code=500, detail=f"R2 delete failed: {e}")
