<#
.Synopsis
   pre-push hook

.DESCRIPTION
   pre-push hook to enable gated check-in with unit tests and code coverage.

.EXAMPLE
   pre-push.ps1
   
.NOTES
   Author: 
   File Name: pre-push.ps1
#>

Write-Output "Validating unit test coverage..."
cd CodeBuild
exit pytest --cov=Assets_as_Code --cov-fail-under=80