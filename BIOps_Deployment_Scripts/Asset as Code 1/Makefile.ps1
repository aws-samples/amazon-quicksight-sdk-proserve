$CFN_Templates = "cloudformation\*.template"
$CFPipelineTemplate  = "codepipeline\pipeline.yml"
$PIPELINE_CFN_Name = "pr-biat-content-pipeline-PRPipeline"
$Pipeline_name = "biat-content"
$AWSRegion = "us-east-1"

# Requirements:
# 1. Read the requirements for the awshelper module that is used in this script - https://we.mmm.com/wiki/display/HIS/Installing+AWS+CLI+tools
# 2. You must have the AWSPowershell module installed. Instructions are here: https://docs.aws.amazon.com/powershell/latest/userguide/pstools-getting-set-up.html
# 3. You must be running powershell as administrator if you have not yet installed the MMMHIS.AWSHelper module
# 4. You must have at least Powershell v5 installed.
# 5. If you are assuming a role, select the non-privileged role when prompted. At the second prompt, select "yes" to assume a role and then enter the role ARN. 
 

$ErrorActionPreference = "Stop"
$Error.Clear()


# Import the MMMHIS.AWSHelper module.
# First register the Nexus repository "3m-windowsautomation"
$RepositoryName = "3m-windowsautomation"
IF (!(Get-PSRepository | Where-Object {$_.name -eq $RepositoryName}))
    {
    $NugetRepository = "https://nexus.ci.soa-pr.aws.3mhis.net/repository/3m-windowsautomation/"
    Register-PSRepository -Name $RepositoryName -SourceLocation $NugetRepository -PublishLocation $NugetRepository -PackageManagementProvider nuget -InstallationPolicy Trusted
    }

# Install the module if it doesn't exist. If you have already installed it, make sure you are running version 1.0.0.5 or later.
IF (!(Get-Module -ListAvailable | Where-Object {$_.Name -eq "MMMHIS.AWSHelper"}))
    {
    Install-Module -Name "MMMHIS.AWSHelper" -Repository $RepositoryName -Force -Scope CurrentUser
    }


# Import the module
Try
    {
    Import-module MMMHIS.AWSHelper
    }
CATCH
    {
    Throw "An error occurred attempting to import the MMMHIS.AWSHelper Module. The error was '$error'."
    }

# Import the AWS Module
Import-Module AWSPowershell

# Authenticate with AWS using the mmmhis.helper function. Please see the documentation on the wiki for more information.
IF ($AWSRegion.StartsWith("us-gov")) {$AWSEnvironment = "GOV"} ELSE {$AWSEnvironment = "CSP"}
Set-AWSCredentials -Credential (Get-AWSCredentials3M -LoginType "3MSSO" -AWSEnvironment $AWSEnvironment -AWSRegion $AWSRegion)

Write-output "Getting the old pipeline stack params"
$StackParams = (Get-CFNStack -StackName $PIPELINE_CFN_Name -Region $AWSRegion).Parameters

Write-output "Removing the parameter value and setting UsePreviousValue to True"
FOREACH ($Stackp in $StackParams)
    {
    $Stackp.ParameterValue = $Null
    $Stackp.UsePreviousValue = $True
    }


Write-output "Updating the pipeline."
$TemplateYML = Get-content -path $CFPipelineTemplate | Out-String
$CFNOutput = Update-CFNStack -StackName $PIPELINE_CFN_Name -TemplateBody $TemplateYML -Parameter $StackParams -region $AWSRegion

# Wait for it to complete
While ((Get-CFNStack -StackName $PIPELINE_CFN_Name -region $AWSRegion | Select -ExpandProperty StackStatus | Select -ExpandProperty value) -in ("UPDATE_IN_PROGRESS","UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"))
    {
    Write-output "Waiting for the stack to complete."
    Start-Sleep -Seconds 5
    }

$StackCompleteStatus = Get-CFNStack -StackName $PIPELINE_CFN_Name -Region $AWSRegion | Select -ExpandProperty StackStatus | Select -ExpandProperty value
IF ($StackCompleteStatus -ne "Update_Complete") 
	{
	Throw "Error. The stack '$Pipeline_CFN_Name' failed with the status '$StackCompleteStatus'."
	}

# Validate the templates
IF (Test-Path $CFN_Templates) 
    {
    $CFNTemplateFiles  = Get-Childitem $CFN_Templates
    FOREACH ($CFNtemplate in $CFNTemplateFiles)
        {
    	Write-output "Testing the template: $($CFNTemplate.Fullname)"
        $CFNTxt = Get-Content -Path $CFNtemplate.Fullname
    	TRY
		    {
		    Test-CFNTemplate -TemplateBody ($CFNTxt | Out-String) -Region $AWSRegion
		    }
	    CATCH
    		{
		    Write-Warning -Message "Warning. Unable to validate the template $($CFNTemplate.Fullname) due to error '$error'."
		    $Error.Clear()
		    }
        }
    }