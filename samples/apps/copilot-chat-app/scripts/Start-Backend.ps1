<#
.SYNOPSIS
Builds and runs the Chat Copilot backend.
#>

# Set defaults and constants
$envScriptFilePath = Join-Path "$PSScriptRoot" '.env.ps1'
. $envScriptFilePath

# Environment variable `ASPNETCORE_ENVIRONMENT` required to override 
# appsettings.json with appsettings.$envASPNetCore.json 
# See `webapi/ConfigurationExtensions.cs`
$Env:ASPNETCORE_ENVIRONMENT=$envASPNetCore

Join-Path "$PSScriptRoot" '../webapi' | Set-Location
dotnet build
dotnet run
