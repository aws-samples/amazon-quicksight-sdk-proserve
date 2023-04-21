import json
import requests
import base64
import os
import boto3
import logging
from botocore.exceptions import ClientError

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

cognitoDomainUrl = os.environ.get("COGNITO_DOMAIN_URL")
cognitoClientId = os.environ.get("COGNITO_CLIENT_ID")
cognitoClientSecretName = os.environ.get("COGNITO_CLIENT_SECRET_NAME")
redirectURL = os.environ.get("REDIRECT_URL")
region = os.environ.get("REGION")
qsembedurl = os.environ.get("QS_EMBED_URL")
presignedurl = os.environ.get("PRESIGNED_URL")

#############################################
# Function to read secret from SecretsManager
#############################################
def get_secrets():
    secret_name = cognitoClientSecretName
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',
                            region_name=region,
                            )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(
                get_secret_value_response['SecretBinary'])
        return secret


def lambda_handler(event, context):
    logger.info(event)
    logger.info(context)
    Header = {}
    code = event['params']['querystring']['code']
    if 'state' in event['params']['querystring']:
        state_flag = True
        state = event['params']['querystring']['state']
        states = state.split('$')
        for param in states:
            param_split = param.split('=', 1)
            Header[param_split[0]] = param_split[1]
    else:
        state_flag = False
        # print(states)
    logger.info(code)
    secret = get_secrets()
    encoded_auth = base64.b64encode(
        (cognitoClientId + ':' + json.loads(secret)['cognito-user-pool-secret']).encode('ascii'))

    cognitoHeader = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic '.encode('ascii') + encoded_auth
    }

    cognitoBody = {
        'grant_type': 'authorization_code',
        'client_id': cognitoClientId,
        'code': code,
        'redirect_uri': redirectURL

    }

    requestToken = requests.post(
        cognitoDomainUrl + '/oauth2/token',
        data=cognitoBody,
        headers=cognitoHeader
    )

    token = requestToken.json()['id_token']

    userName = json.loads(base64.b64decode(
        token.split('.')[1] + "========"))['cognito:username']
    email = json.loads(base64.b64decode(
        token.split('.')[1] + "========"))['email']
    logger.info(userName)
    logger.info(email)
    Header['Authorization'] = token
    Header['redirect'] = 'true'
    print(Header)
    if state_flag and 'id' in Header and 'name' in Header:
        r = requests.post(
            presignedurl,
            data=json.dumps({"Empty": "Empty"}),
            headers=Header)
    else:
        r = requests.post(
            qsembedurl,
            data=json.dumps({"Empty": "Empty"}),
            headers=Header)
    logger.info(r.json())
    return r.json()
