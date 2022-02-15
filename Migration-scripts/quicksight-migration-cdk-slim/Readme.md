# BIOps: QuickSight Porting Assets CDK Slim

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

___

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

___

### Deploy to central account


#### 🚀 Deploy QuickSight Migration Stack
```bash
export CDK_DEFAULT_ACCOUNT=[Your Source/Dev AWS Account]
export CDK_DEFAULT_REGION=[Your Source/Dev AWS Region]
cdk bootstrap
cdk deploy quicksight-migration-stack
```

### 🚀 Deploy QuickSight Target Stack
----
#### Deploy Target Stack
An IAM role needs to be created on target accounts that will allow the source account to assume.

##### Setup
1. Update self.central_account_id = "123456789123" with the central account ID.
2. Update the `/infra/config` Systems Manager parameter found in `infra_target_account_stack.py` file with the values of your existing Amazon Redshift or RDS clusters. Set redshiftPassword and rdsPassword to the name of the secret found in Secrets Manager for these resources.

```bash
export CDK_DEFAULT_ACCOUNT=[Your Target/Prod AWS Account]
export CDK_DEFAULT_REGION=[Your Target/Prod AWS Region]
cdk bootstrap
cdk deploy quicksight-target-stack
```
___
