import os
import logging
import requests
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
# handler = logger.handlers[0]
# formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(aws_request_id)s\t%(message)s\n', '%Y-%m-%dT%H:%M:%S')
# handler.setFormatter(formatter)

DEFAULT_REGION = "eu-west-1"

# Environment variables
AWS_REGION = os.environ.get("AWS_REGION", DEFAULT_REGION)
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")


def create_presigned_url(object_name, expiration=3600):
    """Generate a presigned URL

    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
        endpoint_url=f'https://s3.{AWS_REGION}.amazonaws.com',
        config=Config(signature_version="s3v4")
    )
    try:
        response = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            HttpMethod="GET",
            Params={"Bucket": S3_BUCKET_NAME, "Key": object_name},
            ExpiresIn=expiration  # default expiry is 1 hour (3600 seconds)
        )
    except ClientError as e:
        logger.error(e)
        return None

    # The response contains the presigned URL
    return response


def lambda_handler(event, context):
    logger.info(f"payload={event}")
    call_id = event['params']['header']["id"]
    filename = event['params']['header']["name"]
    redirect = True if "redirect" in event['params']['header'] \
                       and event['params']['header']["redirect"] == "true" else False
    try:
        url = create_presigned_url(f"call-attachments/{call_id}/{filename}")
    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": bool("true")
            },
            "body": e
        }
    if url is not None and redirect:
        return {
            "statusCode": 302,
            "headers": {
                "Location": url,
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": bool("true")
            }
        }
    else:
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": bool("true")
            },
            "body": url
        }
