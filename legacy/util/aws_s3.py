import os
from botocore.exceptions import ClientError
import base64
import boto3

import logging
from config.config import conf

BUCKET = str(conf["AWS_S3_BUCKET_NAME"])


def base64_to_s3(base64_image, bucket: str = BUCKET, key: str = "None"):
    """
    Uploads a base64 string to S3 and returns the link to the image
    """
    try:
        if key is "None":
            key = base64_image.split("/")[-1]

        s3_client = boto3.client(
            's3', aws_access_key_id=conf["AWS_ACCESS_KEY_ID"], aws_secret_access_key=conf["AWS_SECRET_ACCESS_KEY"])
        decoded_image = base64.b64decode(base64_image)
        s3_client.put_object(Body=decoded_image, Bucket=bucket, Key=key)
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except ClientError as e:
        logging.error(e)
        return None


def s3_to_base64(link: str, bucket: str = BUCKET, key: str = "None"):
    """
    Downloads an image from S3 and returns the base64 string
    """
    try:
        if key is "None":
            key = link.split("/")[-1]

        s3_client = boto3.client(
            's3', aws_access_key_id=conf["AWS_ACCESS_KEY_ID"], aws_secret_access_key=conf["AWS_SECRET_ACCESS_KEY"])
        image = s3_client.get_object(Bucket=bucket, Key=key)
        return base64.b64encode(image['Body'].read()).decode('utf-8')
    except ClientError as e:
        logging.error(e)
        return None


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
