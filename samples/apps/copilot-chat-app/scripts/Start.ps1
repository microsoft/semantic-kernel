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

Set-Location "$PSScriptRoot"
$BackendScript = Join-Path '.' 'Start-Backend.ps1'
$FrontendScript = Join-Path '.' 'Start-Frontend.ps1'

# Start backend (in new PS process)
if ($AzureOpenAIOrOpenAIKey -eq '')
{
    # no key
    Start-Process pwsh -ArgumentList "-noexit", "-command $BackendScript"
}
else
{
    # with key
    Start-Process pwsh -ArgumentList "-noexit", "-command $BackendScript -AzureOpenAIOrOpenAIKey $AzureOpenAIOrOpenAIKey"
}

# Start frontend (in current PS process)
& $FrontendScript -ClientId $ClientId -Tenant $Tenant
