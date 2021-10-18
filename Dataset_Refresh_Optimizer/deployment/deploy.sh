#! /bin/bash

set -e
set -u
set -o pipefail
ROOT="." # DO NOT CHANGE!

# INPUT PARAMETERS
#################################################################################################################
S3BUCKET="qs-ds-refresh-optimizer"
PROFILE="default"
REGION="us-east-1"
#################################################################################################################

echo ''
echo '-- Packing Lambda source code ...'
S3PATH="lambda_source/"
cd ../lambda_source
zip lambda.zip index.py

echo '-- Uploading AWS Lambda code to S3 ...'
echo "-- Target S3 PATH: s3://${S3BUCKET}/${S3PATH}"
echo ''
aws s3 --p ${PROFILE} cp *.zip "s3://${S3BUCKET}/${S3PATH}"

echo '-- Launching scheduler deployment ...'
cd ../source
python3 scheduler.py

echo '-- Updaing Lambda function ...'

aws lambda --p ${PROFILE} update-function-code \
  --function-name qs-ds-refresh-optimizer \
  --s3-bucket ${S3BUCKET} \
  --s3-key "${S3PATH}lambda.zip" \
  --region ${REGION}

echo ''
echo '-- All done.'
