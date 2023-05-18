<#
.SYNOPSIS
Builds and runs the Copilot Chat backend.
#>

Join-Path "$PSScriptRoot" '../webapi' | Set-Location
dotnet build
dotnet run
