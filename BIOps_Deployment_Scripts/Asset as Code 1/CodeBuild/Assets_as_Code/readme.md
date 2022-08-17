# BIA
BI & Analytics

Seed project is intended to support implementation of unit tests and coverage analysis.

Using pytest test framework, pytest test runner, coverage.py (through pytest), and diff-cover

Goal is to show how to generate a pass/fail status based on a supplied threshold of coverage on new and updated lines in the delta between the

Best practices approach to importing code under test

Using "Tests separate" approach

shell scripts for bash (.sh) and Windows (.ps1)

### Setup/Prerequisites
"install" the development code so it will be accessible to the tests by: 

1. opening a command prompt and creating the venv in the package directory: bb-biat-content_IaC\CodeBuild\Assets_as_Code using the command: python -m venv .venv (cd bb-biat-content_IaC\CodeBuild\Assets_as_Code)
2. activating the desired Python environment: .venv\Scripts\activate.bat
3. pip install -r requirements.txt to install necessary packages to run the pytest unit tests
4. To run all test cases, type 'pytest --cov' in the command prompt under the root folder

### Content Deployment
Under the 'Deployment' directory, you will find all of the scripts associated with the assets (themes, datasets, dashboards) deployment for Quicksight

####Two types of content deployment processes:
1) incremental_deployment.py: This script deploys new assets across accounts and regions on a frequent basis to each enterprise. Script currently supports migration of Quicksight themes, datasets, and dashboards.
2) initialization.py: This initialization script deploys all existing assets across accounts and regions to each newly, credentialed enterprise (client). This script runs after the credentialing process is run to create the client's resource infrastructure. Script currently supports migration of Quicksight themes, datasets, and dashboards.

####Used for both incremental_deployment.py and initialization.py:
1) prepare_zip.py: From the Quicksight RD-Dev account, the script extracts contents from the Quicksight release folder or model namespace and prepares a package full of json files to be used in the intiialization.py and incremental_deployment.py
2) reset_folder.py: This script deletes all assets from the Release folder from the RD-Dev account after the end of a deployment.
3) review_to_qa.py: This script makes copies of the specified assets from review-qa-release.json in "QAAssetIds" and moves them from the Review folder to QA folder and removes the folder membership of the original assets
4) qa_to_release.py: This script moves the specified assets from review-qa-release.json in "ReleaseAssetIds" from the QA folder to Release folder
5) deploy_dashboards.py: This script deploys dashboards according to premade templates specified in deploy_dashboards.json

####Used for only initialization.py:
1) infrastructure_setup.py: After a client is credentialed into 360E, this script creates the Quicksight set up for enterprises (namespace, client datasource, groups, users, group-user memberships, folder structure)
In sequence, this is run before initialization.py. 

#### Mapping JSONs required for content deployment:
1) folder_structure.json: Each enterprise in Quicksight will have this static folder structure created and validated per deployment
2) group_to_folders.json: This is the mapping for the groups to folder permissions.
3) review_qa_release.json: This contains the folder arns of the review, qa and release folders as well as the specific asset ids to move between folders

Both these JSON files will be zipped into the SourceAssets/ dir when the deployment scripts extract the zip file from Nexus.

### Terminology:
- Namespace: A container of users and assets. A namespace will be administered for each enterprise (client)
- Assets: The artifacts that are being deployed, which include data sources, themes, datasets, and dashboards
- Credentialing: The process of setting up all necessary resources for each enterprise