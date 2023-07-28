<#
.SYNOPSIS
Initializes and runs both the backend and frontend for Chat Copilot.
#>

$BackendScript = Join-Path "$PSScriptRoot" 'Start-Backend.ps1'
$FrontendScript = Join-Path "$PSScriptRoot" 'Start-Frontend.ps1'

Write-Host $BackendScript

# Start backend (in new PS process)
Start-Process pwsh -ArgumentList '-noexit', '-command' "$BackendScript"

# Start frontend (in current PS process)
& $FrontendScript
