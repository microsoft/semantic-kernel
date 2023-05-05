<#
.SYNOPSIS
Initializes and runs both the backend and frontend for Copilot Chat.

.PARAMETER ClientId
The client (application) ID for your AAD app registration.

.PARAMETER TenantId
The tenant (directory) ID for your AAD app registration.
If you are using a personal MSA account, enter 'msa' here.
Defaults to the 'common' endpoint.

.PARAMETER Key
Your OpenAI or Azure OpenAI API key.
#>

#Requires -Version 6

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
    Start-Process pwsh -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1"
}
else
{
    # with key
    Start-Process pwsh -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1 -Key $Key"
}

# Start frontend (in current PS process)
& "$PSScriptRoot/Start-Frontend.ps1" -ClientId $ClientId -TenantId $TenantId
