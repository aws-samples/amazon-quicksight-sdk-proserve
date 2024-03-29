# BIOps: QuickSight Assets Porting Across Accounts CDK Slim

Please refer to the AWS blogpost BIOps: QuickSight Objects Migration and Version Control for a complete walk-through.

## Prerequisites

For this walk-through, you should have the following prerequisites:

- Access to the following AWS services:
  - Lambda
  - QuickSight
- Two different QuickSight accounts, such as development and production
- Basic knowledge of Python
- AWS SDK for Python (Boto3)
- CDK installed, see AWS CDK Intro Workshop: Python Workshop.
- venv / pip
- Git

### Clone the repository

```bash
git clone https://github.com/aws-samples/amazon-quicksight-sdk-proserve/tree/master/Migration-scripts/cdk-slim/
```

### Setup your virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
### Set enviroment varibles

#### Central/Source Account
```bash
export CDK_CENTRAL_ACCOUNT=[Your Source AWS Account]
export CDK_CENTRAL_REGION=[Your Source AWS Region]
```

#### Target/Destination Account
```bash
export CDK_TARGET_ACCOUNT=[Your Target AWS Account]
export CDK_TARGET_REGION=[Your Target AWS Region]
```

## Deploy QuickSight Source Stack

### Deploy Stack

```bash
cdk bootstrap
cdk deploy quicksight-migration-stack
```

---

## Deploy QuickSight Target Stack

An IAM role needs to be created on target accounts that will allow the source account to assume.

### Pre-Deploy Setup

#### Code Changes (Optional - Can be done after deployment)
- Update the `/infra/config` Systems Manager parameter found in `infra_target_account_stack.py` file with the values of your existing Amazon Redshift or RDS clusters. 
- Set redshiftPassword and rdsPassword to the name of the secret found in Secrets Manager for these resources.

#### Deploy Stack

```bash
cdk bootstrap
cdk deploy quicksight-target-stack
```

---

## Invoke Lambda Function from CLI

Once the cloudformation stacks have been deployed using the CDK the Lambda function can be invoked from the CLI.

**Logging:**
The complete log history is available in CloudWatch.

```bash
aws lambda invoke \
--cli-binary-format raw-in-base64-out \
--function-name quicksight_migration_lambda \
--payload file://events/sample.json \
quicksight_migration.log \
--log-type Tail \
--query 'LogResult' \
--output text |  base64 -d -> quicksight_migration.log
```

### Sample Log - CLI

![sampelog](images/cli_log.png)

### Sample Log - CloudWatch

![sampelog](images/cloudwatch_log.png)