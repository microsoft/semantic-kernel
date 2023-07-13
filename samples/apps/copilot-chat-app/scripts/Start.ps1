<#
.SYNOPSIS
Builds and runs both the backend and frontend for Copilot Chat.
#>

$BackendScript = Join-Path "$PSScriptRoot" 'Start-Backend.ps1'
$FrontendScript = Join-Path "$PSScriptRoot" 'Start-Frontend.ps1'

# Start backend (in new PS process)
Start-Process pwsh -ArgumentList "-noexit", "-command $BackendScript"

# Start frontend (in current PS process)
& $FrontendScript
