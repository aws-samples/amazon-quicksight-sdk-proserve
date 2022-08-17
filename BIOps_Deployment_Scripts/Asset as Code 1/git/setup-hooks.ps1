<#
.Synopsis
   Create git hook files
.DESCRIPTION
   Create git hooks for pre-commit and pre-push
.EXAMPLE
   setup-hooks.ps1
.NOTES
   Author: Minh Duong
   File Name: setup-hooks.ps1
#>

# Locate sh.exe path
$git_path = cmd /c where.exe "git.exe"
if (!$git_path) 
{
   Write-Host "Cannot locate git.exe" -ForegroundColor Red
   exit 1
}

$git_path = Split-Path -Path (Split-Path -Path $git_path)
$files = Get-ChildItem -Path $git_path -Include "sh.exe" -Recurse
if (!$files) 
{
   Write-Host ("Cannot locate sh.exe from path " + $git_path) -ForegroundColor Red
   exit 1
}

$sh_path = $files[0].FullName
$sh_path = $sh_path.Replace("\", "/")
$sh_path = "#!" + $sh_path.Replace(" ", "\ ")

# Create pre-commit hook
$pre_commit = $sh_path + "`n`n" + "exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File `".\git\hooks\pre-commit.ps1`""
Out-File -FilePath .\..\.git\hooks\pre-commit -InputObject $pre_commit -NoNewline -Encoding ASCII

# Create pre-push hook
$pre_commit = $sh_path + "`n`n" + "exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File `".\git\hooks\pre-push.ps1`""
Out-File -FilePath .\..\.git\hooks\pre-push -InputObject $pre_commit -NoNewline  -Encoding ASCII

Write-Host "Hooks setup complete!" -ForegroundColor Green