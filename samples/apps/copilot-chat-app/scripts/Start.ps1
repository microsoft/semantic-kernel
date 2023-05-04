<#
.SYNOPSIS
Initialize and run both the backend and frontend for Copilot Chat.
#>

param (
    [Parameter(Mandatory)]
    [string] $ClientId,

    [string] $TenantId = 'common',

    [string] $Key
)

# Start backend (in new PS process)
if ($Key -eq '')
{
    # no key
    Start-Process PowerShell -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1"
}
else
{
    # with key
    Start-Process PowerShell -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1 -Key $Key"
}

# Start frontend (in current PS process)
& "$PSScriptRoot/Start-Frontend.ps1" -ClientId $ClientId -TenantId $TenantId
