## Amazon quicksight sdk proserve Migration-scripts

Quicksight Migration Scripts

Author: Ying Wang        Email: wangzyn@amazon.com

Author: Vamsi Bhadriraju Email: bhadrir@amazon.com

## Solution overview
![image](https://user-images.githubusercontent.com/41450724/120677740-66c72400-c465-11eb-8d1b-9d5e9481a70f.png)

We provide the sample Python scripts for migrating across accounts in three
SageMaker notebooks: 

functions – Provides all the functions, including describe objects, create
objects, and so on. The supportive functions are developed to perform the
tasks to automate the whole process. For example, update the data source
connection information, get the dashboard ID from dashboard name, and
write logs. 

batch migration – Provides the sample automation procedure to migrate
all the assets from the source account to the target account.

incremental migration – Provides on-demand incremental migration to
migrate specific assets across accounts

![image](https://user-images.githubusercontent.com/41450724/120677686-58790800-c465-11eb-93e8-da99e01109ad.png)


## Prerequisites
For this solution, you should have the following prerequisites:

Access to the following AWS services:
o QuickSight
o SageMaker
o AWS Identity and Access Management (IAM)

Two different QuickSight accounts, for instance, development and
production

Basic knowledge of Python

Basic AWS SDK knowledge

## Create resources
Create your resources in source account by completing the following steps:

1.	Download the notebooks from the GitHub repository.
2.	Create a notebook instance.
3.	Edit the IAM role of this instance to add an inline policy called qs-admin-source:
```bash
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole",
                "quicksight:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Deny",
            "Action": [
                "quicksight:DeleteA*",
                "quicksight:DeleteC*",
                "quicksight:DeleteD*",
                "quicksight:DeleteG*",
                "quicksight:DeleteI*",
                "quicksight:DeleteN*",
                "quicksight:DeleteTh*",
                "quicksight:DeleteU*",
                "quicksight:DeleteV*",
                "quicksight:Unsubscribe"
            ],
            "Resource": "*"
        }
    ]
}
```

4.	On the notebook instance page, on the Actions menu, choose Open JupyterLab.
5.	Upload the three notebooks into the notebook instance.

## Implementing the solution
To implement the solution, complete the following steps:
Assume Role solution:
1.	Create an IAM role in the target (production) account that can be used by the source (development) account. 
2.	In the IAM console navigation pane on the left, choose Roles and then choose Create role.
3.	Choose the Another AWS account role type.
4.	For Account ID, type the source (development) account ID.
5.	Create an IAM policy called qs-admin-target:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["quicksight:*",
		      "sts:AssumeRole"],
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

6.	Grant the IAM role the qs-admin-target IAM policy.

 

7.	Provide the qs-admin-source and qs-admin-target role name in Assume Role cells of the notebooks:
 

## Static Profile solution:
1.	Create IAM user qs-admin-source with policy qs-admin-source in source account.
2.	Create IAM user qs-admin-target with policy qs-admin-target in target account.
3.	Get aws_access_key_id and secret_access_key of these two IAM users.
4.	In the terminal of the SageMaker notebook, go to the directory /home/ec2-user/.aws. 
5.	Edit the config and credential file to add a profile named source with the aws_access_key_id and secret_access_key of qs-admin-source.
6.	Edit the config and credential file to add a profile named target with the aws_access_key_id and secret_access_key of qs-admin-target.
7.	Provide the source and target profile name in the Static Profile cell of the notebook:
 

The tutorials of these notebooks are provided as comments inside the notebooks. You can run it cell by cell. If you want to schedule the notebooks to run automatically, you can schedule the Jupyter notebooks on SageMaker ephemeral instances. 

Please note: In this solution, we assume that the name of dashboard and dataset are unique in target (Prod) account.  If you have multiple dashboards or datasets with the same name, you will hit an error during the migration. Every dashboard has its own business purpose so that we should not create multiple dashboards with the same name in production environment to confuse the dashboard viewers. 
![image](https://user-images.githubusercontent.com/41450724/120677445-14860300-c465-11eb-803c-3cf6a3e171ca.png)


## License

This library is licensed under the MIT-0 License. See the LICENSE file.
