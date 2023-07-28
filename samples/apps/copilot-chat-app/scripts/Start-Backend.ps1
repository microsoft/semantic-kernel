<#
.SYNOPSIS
Builds and runs the Chat Copilot backend.
#>

# Environment variable `ASPNETCORE_ENVIRONMENT` required to override appsettings.json with 
# appsettings.$ENV_ASPNETCORE.json. See `webapi/ConfigurationExtensions.cs`
$Env:ASPNETCORE_ENVIRONMENT=$envASPNetCore

Join-Path "$PSScriptRoot" '../webapi' | Set-Location
dotnet build
dotnet run
