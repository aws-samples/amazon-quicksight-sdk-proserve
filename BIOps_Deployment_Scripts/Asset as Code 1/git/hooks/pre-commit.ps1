<#
.Synopsis
   Pre-commit hook

.DESCRIPTION
   Pre-commit hook to warn user about gated check-in

.EXAMPLE
   pre-commit.ps1
   
.NOTES
   Author: 
   File Name: pre-commit.ps1
#>

Write-Host "Have you added unit tests?  git push is gated for unit tests." -ForegroundColor Yellow
exit 0