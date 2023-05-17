<#
.SYNOPSIS
Builds and runs both the backend and frontend for Copilot Chat.
#>

#Requires -Version 6

Set-Location "$PSScriptRoot"
$BackendScript = Join-Path '.' 'Start-Backend.ps1'
$FrontendScript = Join-Path '.' 'Start-Frontend.ps1'

# Start backend (in new PS process)
Start-Process pwsh -ArgumentList "-noexit", "-command $BackendScript"

# Start frontend (in current PS process)
& $FrontendScript -ClientId $ClientId -Tenant $Tenant
