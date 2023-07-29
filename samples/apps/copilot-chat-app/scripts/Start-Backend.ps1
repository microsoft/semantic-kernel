<#
.SYNOPSIS
Builds and runs the Chat Copilot backend.
#>

# Get defaults and constants
$varScriptFilePath = Join-Path "$PSScriptRoot" 'Variables.ps1'
. $varScriptFilePath

# Environment variable `ASPNETCORE_ENVIRONMENT` required to override appsettings.json with 
# appsettings.$varASPNetCore.json. See `webapi/ConfigurationExtensions.cs`
$Env:ASPNETCORE_ENVIRONMENT=$varASPNetCore

Join-Path "$PSScriptRoot" '../webapi' | Set-Location
dotnet build
dotnet run
