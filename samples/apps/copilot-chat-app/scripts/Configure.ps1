<#
.SYNOPSIS
Configure user secrets, appsettings.Development.json, and .env for Copilot Chat.

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

$envScriptFilePath = Join-Path "$PSScriptRoot" '.env.ps1'
. $envScriptFilePath

# Set remaining values from .env.ps1
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

Write-Host "#########################"
Write-Host "# Backend configuration #"
Write-Host "#########################"

# Install dev certificate
if ($IsLinux)
{
    dotnet dev-certs https
    if ($LASTEXITCODE -ne 0) { exit(1) }
}
else # Windows/MacOS
{
    dotnet dev-certs https --trust
    if ($LASTEXITCODE -ne 0) { exit(1) }
}

$webapiProjectPath = Join-Path "$PSScriptRoot" '../webapi'

Write-Host "Setting 'AIService:Key' user secret for $AIService..."
dotnet user-secrets set --project $webapiProjectPath  AIService:Key $ApiKey
if ($LASTEXITCODE -ne 0) { exit(1) }

$appsettingsOverrides = @{ AIService = @{ Type = $AIService; Endpoint = $Endpoint; Models = @{ Completion = $CompletionModel; Embedding = $EmbeddingModel; Planner = $PlannerModel } } }
$appSettingsJson = -join ("appsettings.", $envASPNetCore, ".json");
$appsettingsOverridesFilePath = Join-Path $webapiProjectPath $appSettingsJson

Write-Host "Setting up '$appSettingsJson' for $AIService..."
ConvertTo-Json $appsettingsOverrides | Out-File -Encoding utf8 $appsettingsOverridesFilePath

Write-Host "($appsettingsOverridesFilePath)"
Write-Host "========"
Get-Content $appsettingsOverridesFilePath | Write-Host
Write-Host "========"

Write-Host ""
Write-Host "##########################"
Write-Host "# Frontend configuration #"
Write-Host "##########################"

$webappProjectPath = Join-Path "$PSScriptRoot" '../webapi'
$webappEnvFilePath = Join-Path "$webappProjectPath" '/.env'

Write-Host "Setting up '.env'..."
Set-Content -Path $webappEnvFilePath -Value "REACT_APP_BACKEND_URI=https://localhost:40443/"
Add-Content -Path $webappEnvFilePath -Value "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$TenantId"
Add-Content -Path $webappEnvFilePath -Value "REACT_APP_AAD_CLIENT_ID=$ClientId"

Write-Host "($webappEnvFilePath)"
Write-Host "========"
Get-Content $webappEnvFilePath | Write-Host
Write-Host "========"

Write-Host "Done!"
