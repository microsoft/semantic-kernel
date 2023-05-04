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

if ($Key -eq '')
{
    Start-Process PowerShell -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1"
}
else
{
    Start-Process PowerShell -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1 -Key $Key"
}

Start-Process PowerShell -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Frontend.ps1 -ClientId $ClientId -TenantId $TenantId"
