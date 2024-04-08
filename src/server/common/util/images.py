
from repo.image import GCPImageRepository as ImageRepo
from PIL import Image
import io
from fastapi import UploadFile

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024


def check_image(image: UploadFile) -> int:
    """Checks if an image is valid. Checks file type and size. returns image size(bytes)."""
    # check file type
    if not image.content_type.startswith("image/"):
        raise Exception("Invalid file type")
    # check file size
    if image.size > MAX_IMAGE_SIZE_BYTES:
        raise Exception("File size too large")
    print("Image size:", image.size)

    return image.size


def compress_image(image: UploadFile) -> bytes:
    """Compresses an image."""
    # convert image to bytes
    image_bytes = image.file.read()
    # compress image by converting to JPEG bytestream
    image = Image.open(io.BytesIO(image_bytes))
    image = image.convert("RGB") # Convert image to RGB mode
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="JPEG")
    image_bytes = image_bytes.getvalue()

    return image_bytes


def compress_to_thumbnail(image: UploadFile) -> bytes:
    """Compresses an image to thumbnail size."""
    # convert image to bytes
    image_bytes = image.file.read()
    # compress image by converting to JPEG bytestream
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail((1000, 1000))
    image = image.convert("RGB") # Convert image to RGB mode
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="JPEG")
    image_bytes = image_bytes.getvalue()

    return image_bytes


def upload_image(image: UploadFile, folder) -> str:
    """Uploads an image to the cloud and returns the image public URL. Checks if image is valid."""
    # check if image is valid
    check_image(image)
    # compress image
    image_bytes = compress_to_thumbnail(image)
    # upload image
    image_id = ImageRepo(folder).create(image_bytes)
    # get image URL
    image_url = ImageRepo(folder).get_url(image_id)

    return image_url
