<#
.SYNOPSIS
Initialize and run both the backend and frontend for Copilot Chat.
#>

param (
    [SecureString] $Key,

    [Parameter(Mandatory)]
    [string] $ClientId,

    [string] $TenantId = 'common'
)

Start-Process PowerShell -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1 -Key $Key"
Start-Process PowerShell -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Frontend.ps1 -ClientId $ClientId -TenantId $TenantId"
