import os
import tempfile
import shutil
import boto3
from pathlib import Path
from functools import lru_cache
from fastapi import HTTPException
import hashlib
from server.config import CONFIG
import pytest
from server.common.repo.s3 import S3Repo
from server.common.repo.pickle_storage import LocalPickleStorage, S3PickleStorage


@pytest.fixture(scope="module")  # after all tests are done
def s3_fixture():
    s3 = S3Repo()
    yield s3
    shutil.rmtree(s3.cache_dir, ignore_errors=True)  # Delete cache directory
    s3.delete_file("test_key")  # Delete test file from S3
    s3.delete_file("test.pkl")  # Delete test file from S3


@pytest.fixture(scope="module")
def local_storage():
    storage = LocalPickleStorage()
    yield storage
    shutil.rmtree(storage.cache_dir, ignore_errors=True)


def test_s3(s3_fixture):  # Use the fixture in your test
    s3 = s3_fixture
    key = "test_key"
    file_path = "test_file.txt"

    with open(file_path, "w") as f:
        f.write("test data")

    s3.upload_file(file_path, key)
    s3.download_file(key, file_path)

    with open(file_path, "r") as f:
        assert f.read() == "test data"

    # Clean up local and cached files
    os.remove(file_path)
    cached_file = s3.get_cached_path(key)
    if cached_file.exists():
        os.remove(cached_file)

    # Assertions
    assert not Path(file_path).exists()
    assert not Path(cached_file).exists()
    # check if cache directory is empty
    assert not os.listdir(s3.cache_dir)


def test_local_pickle_storage(local_storage):
    filestore = local_storage
    data = {"key": "value"}
    path = "test.pkl"

    filestore.save(data, path)
    assert Path(filestore.cache_dir / path).exists()  # Check if file is saved
    loaded_data = filestore.load(path)  # Load data from file
    assert loaded_data == data  # Check if data is loaded correctly

    os.remove(filestore.cache_dir / path)
    assert not Path(filestore.cache_dir / path).exists()


def test_s3_pickle_storage():
    s3 = S3PickleStorage()
    data = {"key": "value"}
    path = "test.pkl"

    # test saving
    s3.save(data, path)
    # test loading
    loaded_data = s3.load(path)
    assert loaded_data == data
    # test overwriting to the same path and check if cache is invalidated too
    new_data = {"key": "new_value"}
    s3.save(new_data, path)
    loaded_data = s3.load(path)
    assert loaded_data == new_data
    # test deleting
    pass
