<#
.SYNOPSIS
Install the requirements for running Copilot Chat. Note that this script only works on Windows.
#>

if ($IsWindows)
{
    # Install chocolatey
    Set-ExecutionPolicy Bypass
    [System.Net.ServicePointManager]::SecurityProtocol = 3072
    Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')

    $env:PATH += ";%ALLUSERSPROFILE%\chocolatey\bin"

    # Install packages
    choco install -y dotnet-6.0-sdk nodejs yarn
}
else
{
    Write-Host "ERROR: This script is only supported on Windows."
}
