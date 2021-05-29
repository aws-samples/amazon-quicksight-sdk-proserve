## Amazon quicksight sdk proserve Migration-scripts

Quicksight Migration Scripts

Author: Ying Wang        Email: wangzyn@amazon.com

Author: Vamsi Bhadriraju Email: bhadrir@amazon.com

## Solution overview
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

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
