## Automatic Excel data ingestion into QuickSight with Lambda and S3

1. Download and edit DataClean.py, and then update it with your AWS account ID, bucket name and SNS topic name. Install pandas module in your local Python environment. Noticeably, since Lambda function is based on Amazon Linux operating system, we have to download Pandas and NumPy which are compatible to Amazon Linux when we prepare the package (Link: https://medium.com/@korniichuk/lambda-with-pandas-fd81aa2ff25e). Please Zip the edited package, and upload the zip file to Function code section.

2. Follow the QuickSight SDK documentation to prepare the local SDK environment: https://docs.aws.amazon.com/quicksight/latest/user/quicksight-sdk-python.html. Download sample code “qsAutoIngestion.py”. Edit qsAutoIngestion.py, and update it with your AWS account ID, bucket name, dataset ID and SNS topic name. Zip the whole SDK folder as a package, and upload the zip file to function code.

Author: Ying Wang
Email: wangzyn@amazon.com

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
