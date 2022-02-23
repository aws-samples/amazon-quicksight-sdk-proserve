import os
import json
import base64
import boto3
import logging
from common.constants import custom_config
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class aws_boto3:
    def __init__(self, aws_account_number, role_name, region=None):
        self.role_name = role_name
        self.aws_account_number = aws_account_number

        if region is not None:
            self.region = region
        else:
            self.region = os.environ["Region"]

        self.sts_region = self.region
        self.session = self.__create_session()

    def __create_session(self):
        session_creds = RefreshableCredentials.create_from_metadata(
            metadata=self.__sts_role_credentials(),
            refresh_using=self.__sts_role_credentials,
            method="sts-assume-role",
        )
        session = get_session()
        session._credentials = session_creds
        session.set_config_variable("region", self.region)
        return boto3.Session(botocore_session=session)

    def __sts_role_credentials(self):
        endpoint = "https://sts.{0}.amazonaws.com".format(self.sts_region)
        sts = boto3.client("sts", endpoint_url=endpoint, config=custom_config)        
        role = sts.assume_role(
            RoleArn=f"arn:aws:iam::{self.aws_account_number}:role/{self.role_name}",
            RoleSessionName="quicksight",
            DurationSeconds=900,
        ).get("Credentials")
        creds = {
            "access_key": role.get("AccessKeyId"),
            "secret_key": role.get("SecretAccessKey"),
            "token": role.get("SessionToken"),
            "expiry_time": role.get("Expiration").isoformat(),
        }
        return creds

    def get_ssm_parameters(session, ssm_string):        
        ssm_client = session.client("ssm", config=custom_config)               
        config_str = ssm_client.get_parameter(
            Name=ssm_string)["Parameter"]["Value"]      
        return json.loads(config_str)

    def get_secret(session, secret_name):
        """Get the object from Secrets Manager"""

        # Create a Secrets Manager client
        client = session.client(service_name="secretsmanager", config=custom_config)

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name)
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "DecryptionFailureException":
                raise ex
            elif ex.response["Error"]["Code"] == "InternalServiceErrorException":
                raise ex
            elif ex.response["Error"]["Code"] == "InvalidParameterException":
                raise ex
            elif ex.response["Error"]["Code"] == "InvalidRequestException":
                raise ex
            elif ex.response["Error"]["Code"] == "ResourceNotFoundException":
                raise ex
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary,
            # one of these fields will be populated.
            if "SecretString" in get_secret_value_response:
                secret = json.loads(get_secret_value_response["SecretString"])
                return secret["password"]
            else:
                decoded_binary_secret = base64.b64decode(
                    get_secret_value_response["SecretBinary"]
                )
                return decoded_binary_secret
