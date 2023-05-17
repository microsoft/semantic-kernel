<#
.SYNOPSIS
Builds and runs the Copilot Chat backend.
#>

#Requires -Version 6

Join-Path "$PSScriptRoot" '..' 'webapi' | Set-Location

# Install dev certificate
if ($IsWindows -or $IsMacOS)
{
    dotnet dev-certs https --trust
}
elseif ($IsLinux)
{
    dotnet dev-certs https
}

dotnet build
dotnet run
