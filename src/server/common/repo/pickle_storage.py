import os
import tempfile
import boto3
from pathlib import Path
from functools import lru_cache
from typing import Any
import pickle

from fastapi import HTTPException
from s3 import S3Repo
# Configuration

from config import CONFIG

# File Storage Interface (Optional, but good for abstraction)


class FileStorage:
    def save(self, data: Any, path: str) -> None:
        raise NotImplementedError()

    def load(self, path: str) -> Any:
        raise NotImplementedError()

# Local Pickle Storage


class LocalPickleStorage(FileStorage):
    def save(self, data: Any, path: str, config=CONFIG) -> None:
        with open(path, "wb") as file:
            pickle.dump(data, file)

    def load(self, path: str) -> Any:
        with open(path, "rb") as file:
            return pickle.load(file)


# S3 Pickle Storage with Caching (Uses S3Repo)
class S3PickleStorage(FileStorage):
    def __init__(self, config=CONFIG):
        self.s3_repo = S3Repo(config)

    def save(self, data: Any, path: str) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as temp_file:
            pickle.dump(data, temp_file)
        self.s3_repo.upload_file(temp_file.name, path)
        os.remove(temp_file.name)  # Cleanup

    def load(self, path: str) -> Any:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as temp_file:
            self.s3_repo.download_file(path, temp_file.name)
            with open(temp_file.name, "rb") as f:
                data = pickle.load(f)
        os.remove(temp_file.name)
        return data