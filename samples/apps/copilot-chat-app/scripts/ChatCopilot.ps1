<#
.SYNOPSIS
Configures, initializes, and runs both the backend and frontend for Chat Copilot.

.PARAMETER AIService
The service type used: OpenAI or Azure OpenAI.

.PARAMETER APIKey
The API key for the AI service.

.PARAMETER ClientId
The client (application) ID associated with your AAD app registration.

.PARAMETER Endpoint
Set when using Azure OpenAI.

.PARAMETER CompletionModel
The chat completion model to use (e.g., gpt-3.5-turbo or gpt-4).

.PARAMETER EmbeddingModel
The embedding model to use (e.g., text-embedding-ada-002).

.PARAMETER PlannerModel
The chat completion model to use for planning (e.g., gpt-3.5-turbo or gpt-4).

.PARAMETER TenantId
The tenant (directory) associated with your AAD app registration.
Defaults to 'common'. 
See https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-client-application-configuration#authority.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$AIService,
    
    [Parameter(Mandatory=$true)]
    [string]$APIKey,

    [Parameter(Mandatory = $true)]
    [string] $ClientId,

    [Parameter(Mandatory=$false)]
    [string]$Endpoint,
    
    [Parameter(Mandatory=$false)]
    [string]$CompletionModel,

    [Parameter(Mandatory=$false)]
    [string]$EmbeddingModel, 

    [Parameter(Mandatory=$false)]
    [string]$PlannerModel,

    [Parameter(Mandatory = $false)]
    [string] $TenantId
)

$envScriptFilePath = Join-Path "$PSScriptRoot" 'Variables.ps1'
. $envScriptFilePath

# Set remaining values from Variables.ps1
if ($AIService -eq $envOpenAI) 
{
    if (!$CompletionModel)
    {
         $CompletionModel = $envCompletionModelOpenAI
    }
    if (!$PlannerModel)
    {
         $PlannerModel = $envPlannerModelOpenAI
    }

    # TO DO: Validate model values if set by command line.
}
elseif ($AIService -eq $envAzureOpenAI) 
{
    if (!$CompletionModel)
    {
         $CompletionModel = $envCompletionModelAzureOpenAI
    }
    if (!$PlannerModel)
    {
         $PlannerModel = $envPlannerModelAzureOpenAI
    }
   
    # TO DO: Validate model values if set by command line.

    if (!$Endpoint)
    {
        Write-Error "Please specify an endpoint for -Endpoint when using AzureOpenAI."
        exit(1)
    }
}
else {
    Write-Error "Please specify an AI service (AzureOpenAI or OpenAI) for -AIService."
    exit(1)
}

if (!$EmbeddingModel)
{
     $EmbeddingModel = $envEmbeddingModel
     # TO DO: Validate model values if set by command line.
}
if (!$TenantId)
{
     $TenantId = $envTenantId
     # TO DO: Validate tenantID value if set by command line.
}

# Configure backend and frontend
.\Configure.ps1

# Start backend (in new PS process)
Start-Process pwsh -ArgumentList '-noexit', '-file', ".\Start-Backend.ps1"

# Start frontend (in current PS process)
& .\Start-Frontend.ps1
