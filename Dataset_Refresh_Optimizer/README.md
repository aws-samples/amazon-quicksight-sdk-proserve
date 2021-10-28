## QuickSight Dataset Refresh Optimization

The aim of this solution is to provide our QuickSight customers with near-real-time dashboards that are using SPICE.
This helps obtaining configuration-based control over the update frequency of the QuickSight dashboards and enabling
the customer to adapt and modify the solution as changes applied to the business, and also reducing the effort by
eliminating manual work to update the datasets.

### Built With

* Python 3.8.6
* AWS Lambda
* AWS EventBridge
* AWS CLI
* AWS CloudFormation
* AWS CloudWatch

## Getting started

List of Components:

* Launcher Script: used to take the input of the desired refresh rate for each target dataset and deploy the whole
  solution as a package.
* AWS CloudFormation: used to automate the deployment
* AWS Lambda: serverless component to trigger SPICE refresh job
* AWS EventBridge: set of rules to trigger AWS Lambda periodically
* AWS CloudWatch: used to monitor and debug other components
* AWS SNS: used to send alert in case of a failure

### Prerequisites

- Python 3.8.6 must be installed.
- Create S3 bucket, upload the AWS Lambda zip file using deploy.sh script in lambda_source/ folder and update
  cft/stack.yaml with proper values for S3Bucket and S3Key properties. Default value is:

```yaml 
Code:
    S3Bucket: qs-ds-refresh-optimizer
    S3Key: lambda_source/lambda.zip
```

It is recommended to use the default value and keep it unchanged. AWS Lambda code is located in:
lambda_source/lambda.zip.

- The AWS credentials must be set:

  https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html
- The IAM role to execute the deployment should have following access rights:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "quicksight:*",
        "cloudformation:CreateStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStackEvents",
        "cloudformation:UpdateStack",
        "iam:PassRole"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": "quicksight:Unsubscribe",
      "Resource": "*"
    }
  ]
}
```

### Configuration

Prior to launch, you need to define your datasets and other parameters in `configuration/config.json` file:

```json
{
  "deployment": "../deployment/",
  "stackname": "qs-ds-refresh-optimizer",
  "search": "",
  "account": "",
  "aws_profile": "default",
  "aws_region": "us-east-1",
  "datasets": {
    "proserve-qs-sdk-test": 30
  },
  "ignore": [
    "EG Sales by Brand",
    "Business Review",
    "Marketing Sample",
    "People Overview",
    "Web and Social Media Analytics"
  ]
}
```

In above example, we would like to update the refresh interval for dataset "proserve-qs-sdk-test" with half an hour.

#### Deployment Configuration

You also need to specify parameters in deployment script located in `deployment/deploy.sh`:

```shell
# INPUT PARAMETERS
###################################################################
S3BUCKET="qs-ds-refresh-optimizer"  # S3 Bucket name
PROFILE="default"                   # AWS Credentials Profile Name
REGION="us-east-1"                  # AWS Region
###################################################################
```

### Installation

1. Clone the repo
   ```sh
   git clone URL
   ```
2. Specify configuration parameters in app/config.json

3. Install Python package manager
   ```sh
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   ```
4. Install project requirements
   ```sh
   pip3 install -r requirements.txt
   ```
5. Set Parameters and Launch Deployment
   ```sh
   cd deployment
   # Set parameters in bash script
   ./deploy.sh
   ```

After successful deployment, you will receive a notification email with subject "AWS Notification - Subscription
Confirmation", and you need to subscribe to the SNS topic.

## Search Pattern

In order to execute the project only for certain datasets, change the value of "search" parameter in the
configuration file located in: configuration/config.json. This will automatically search only for datasets with
defined string prefix.

Keeping this variable empty will search for **all** available datasets in QuickSight SPICE.

## Usage

Examples of a successful launch:

```sh
-- Packing Lambda source code ...
updating: ../lambda_source/index.py (deflated 69%)
-- Uploading AWS Lambda code to S3 ...
-- Target S3 PATH: s3://qs-ds-refresh-optimizer/lambda_source/

upload: ../lambda_source/lambda.zip to s3://qs-ds-refresh-optimizer/lambda_source/lambda.zip
-- Launching scheduler deployment ...


-------------------------------------------------------------------------------------------
-- Target dataset: proserve-qs-sdk-test
-------------------------------------------------------------------------------------------
-- New schedule interval for dataset: proserve-qs-sdk-test is going to be: 30
-------------------------------------------------------------------------------------------
-- Temporary stack solution is created.
Updating qs-ds-refresh-optimizer
No changes
-- Done.
-- Updaing Lambda function ...
{
    "FunctionName": "qs-ds-refresh-optimizer",
    "FunctionArn": "arn:aws:lambda:us-east-1:467995266245:function:qs-ds-refresh-optimizer",
    "Runtime": "python3.8",
    "Role": "arn:aws:iam::467995266245:role/qs-ds-refresh-optimizer-LambdaFunctionRole-HMRPD7XVRNQ7",
    "Handler": "index.handler",
    "CodeSize": 1782,
    "Description": "qs-ds-refresh-optimizer | Lambda function to trigger SPICE dataset refresh.",
    "Description": "qs-ds-refresh-optimizer | Lambda function to trigger SPICE dataset refresh.",
    "Timeout": 75,
    "MemorySize": 512,
    "LastModified": "2021-08-27T16:27:29.927+0000",
    "CodeSha256": "b5Cl4IBXXLZVIRFSxTfdJ6Qo2e3Ol53lm0qdGn8p/r4=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "594f0c6c-4fe1-4145-af5b-cfe483539527",
    "State": "Active",
    "LastUpdateStatus": "Successful",
    "PackageType": "Zip"

-- All done.

```

** DO NOT modify AWS resources directly in console. Always use CloudFormation templates to apply changes.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
