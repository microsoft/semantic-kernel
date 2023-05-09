<#
.SYNOPSIS
Initializes and runs both the backend and frontend for Copilot Chat.

.PARAMETER ClientId
The client (application) ID associated with your AAD app registration.

.PARAMETER Tenant
The tenant associated with your AAD app registration.
Defaults to 'common'.

.PARAMETER AzureOpenAIOrOpenAIKey
Your Azure OpenAI or OpenAI API key.
#>

#Requires -Version 6

param (
    [Parameter(Mandatory)]
    [string] $ClientId,

    [string] $Tenant = 'common',

    [string] $AzureOpenAIOrOpenAIKey
)

# Start backend (in new PS process)
if ($AzureOpenAIOrOpenAIKey -eq '')
{
    # no key
    Start-Process pwsh -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1"
}
else
{
    # with key
    Start-Process pwsh -ArgumentList "-noexit", "-command $PSScriptRoot/Start-Backend.ps1 -AzureOpenAIOrOpenAIKey $AzureOpenAIOrOpenAIKey"
}

# Start frontend (in current PS process)
& "$PSScriptRoot/Start-Frontend.ps1" -ClientId $ClientId -Tenant $Tenant
