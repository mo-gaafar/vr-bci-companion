import json
from config.config import conf
from models.common import ImageFolder, PaginatedList, PaginationIn
import boto3
from google.cloud import storage
import uuid
import re
import os
import io
from abc import ABC, abstractmethod
from repo.base import BaseRepository


class ImageRepository(BaseRepository[bytes, str], ABC):
    @abstractmethod
    def get_by_id(self, _id: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def add_tag(self, image_id: str, tag: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def remove_tag(self, image_id: str, tag: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_content_type(self, obj: bytes) -> str:
        raise NotImplementedError


class AWSS3ImageRepository(ImageRepository):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")

    def create(self, obj: bytes) -> str:
        """Uploads an image to S3 and returns the image ID."""

        image_id = uuid.uuid4().hex
        image_object = self.s3_client.Object(self.bucket_name, image_id)
        image_object.put(Body=obj)

        # Set the image's content type
        image_object.ContentEncoding = self.get_content_type(obj)

        return image_id

    def get_by_id(self, image_id: str) -> bytes:
        """Downloads an image from S3 and returns the image bytes."""

        image_object = self.s3_client.Object(self.bucket_name, image_id)
        image_bytes = image_object.get()["Body"].read()

        return image_bytes

    def delete(self, image_id: str) -> str:
        """Deletes an image from S3."""

        image_object = self.s3_client.Object(self.bucket_name, image_id)
        image_object.delete()

        return image_id

    def add_tag(self, image_id: str, tag: str):
        """Adds a tag to an image in S3."""

        image_object = self.s3_client.Object(self.bucket_name, image_id)
        image_object.Tagging = {"Tags": [{"Key": tag, "Value": ""}]}
        image_object.put()

        return image_id

    def remove_tag(self, image_id: str, tag: str):
        """Removes a tag from an image in S3."""

        image_object = self.s3_client.Object(self.bucket_name, image_id)
        image_object.Tagging = {
            "Tags": [t for t in image_object.Tagging["Tags"] if t["Key"] != tag]}
        image_object.put()

        return image_id

    # def get_content_type(self, obj: bytes) -> str:
    #     """Returns the content type of an image."""

    #     content_type = "image/jpeg"

    #     # Try to guess the content type based on the file extension
    #     if obj.endswith(b".png"):
    #         content_type = "image/png"
    #     elif obj.endswith(b".gif"):
    #         content_type = "image/gif"

    #     return content_type


class GCPImageRepository(ImageRepository):
    def __init__(self, folder: ImageFolder):
        self.bucket_name = conf["GCP_BUCKET_NAME"]
        self.project_id = conf["GCP_PROJECT_ID"]
        self.storage_client = storage.Client.from_service_account_info(
            json.loads(conf["CGP_STORE_JSON"])
        )
        self.folder = folder

    def get_bucket(self):
        return self.storage_client.bucket(self.bucket_name)

    def create(self, obj: bytes) -> str:
        """Uploads an image to GCP and returns the image ID."""

        image_id = uuid.uuid4().hex
        image_blob = self.get_bucket().blob(f"{self.folder}/{image_id}")
        image_blob.upload_from_string(obj)

        # Set the image's content type
        image_blob.content_type = self.get_content_type(obj)

        return image_id

    def get_by_id(self, image_id: str) -> bytes:
        """Downloads an image from GCP and returns the image bytes."""

        image_blob = self.get_bucket().blob(f"{self.folder}/{image_id}")
        image_bytes = image_blob.download_as_string()

        return image_bytes

    def add_tag(self, image_id: str, tag: str) -> str:
        """Adds a tag to an image in GCP."""

        image_blob = self.get_bucket().blob(f"{self.folder}/{image_id}")
        image_blob.metadata["tags"] = image_blob.metadata.get(
            "tags", []) + [tag]

        image_blob.update_metadata()

        return image_id

    def remove_tag(self, image_id: str, tag: str) -> str:
        """Removes a tag from an image in GCP."""

        image_blob = self.get_bucket().blob(f"{self.folder}/{image_id}")
        image_blob.metadata["tags"] = [
            t for t in image_blob.metadata.get("tags", []) if t != tag
        ]

        image_blob.update_metadata()

        return image_id

    def delete(self, image_id: str) -> str:
        """Deletes an image from GCP."""

        image_blob = self.get_bucket().blob(f"{self.folder}/{image_id}")
        image_blob.delete()

        return image_id

    def update(self, image_id: str, obj: bytes) -> str:
        """Updates an image in GCP."""

        image_blob = self.get_bucket().blob(f"{self.folder}/{image_id}")
        image_blob.upload_from_string(obj)

        # Set the image's content type
        image_blob.content_type = self.get_content_type(obj)

        return image_id

    def get_url(self, image_id: str) -> str:
        """Gets the URL of an image in GCP."""

        image_blob = self.get_bucket().blob(f"{self.folder}/{image_id}")
        return image_blob.public_url

    def get_content_type(self, obj: bytes) -> str:
        """Returns the content type of an image."""

        content_type = "image/jpeg"

        # Try to guess the content type based on the file extension
        if obj.endswith(b".png"):
            content_type = "image/png"
        elif obj.endswith(b".gif"):
            content_type = "image/gif"

        return content_type

    def get_all(self, pagination: PaginationIn) -> PaginatedList[str]:
        return super().get_all(pagination)
