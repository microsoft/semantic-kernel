<#
.SYNOPSIS
Installs the requirements for running Chat Copilot.
#>

if ($IsLinux) 
{
    Write-Host "ERROR: This script is not supported for your operating system."
    exit 1;
}

Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = 3072

# Install chocolatey if not already installed
$ChocoInstalled = $false
if (Get-Command choco.exe -ErrorAction SilentlyContinue) {
    $ChocoInstalled = $true
}
if (!$ChocoInstalled)
{
    Write-Host "Installing Chocolatey..."
    Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')
    $env:PATH += ";%ALLUSERSPROFILE%\chocolatey\bin"
    refreshenv
}

# Ensure required packages are installed
$Packages = 'dotnet-7.0-sdk', 'nodejs', 'yarn'
foreach ($PackageName in $Packages)
{
    choco install $PackageName -y
}
