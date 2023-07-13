<#
.SYNOPSIS
Configure user secrets, appsettings.Development.json, and .env for Copilot Chat.

.PARAMETER OpenAI
Switch to configure for OpenAI.

.PARAMETER AzureOpenAI
Switch to configure for Azure OpenAI.

.PARAMETER Endpoint
Set when using Azure OpenAI.

.PARAMETER ApiKey
The API key for the AI service.

.PARAMETER CompletionModel
The chat completion model to use (e.g., gpt-3.5-turbo or gpt-4).

.PARAMETER EmbeddingModel
The embedding model to use (e.g., text-embedding-ada-002).

.PARAMETER PlannerModel
The chat completion model to use for planning (e.g., gpt-3.5-turbo or gpt-4).

.PARAMETER ClientID
The client (application) ID associated with your AAD app registration.

.PARAMETER Tenant
The tenant (directory) associated with your AAD app registration.
Defaults to 'common'. 
See https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-client-application-configuration#authority.
#>

param(
    [Parameter(ParameterSetName='OpenAI',Mandatory=$false)]
    [switch]$OpenAI,
    
    [Parameter(ParameterSetName='AzureOpenAI',Mandatory=$false)]
    [switch]$AzureOpenAI,
    
    [Parameter(ParameterSetName='AzureOpenAI',Mandatory=$true)]
    [string]$Endpoint,
    
    [Parameter(Mandatory=$true)]
    [string]$ApiKey,

    [Parameter(Mandatory=$false)]
    [string]$CompletionModel = "gpt-3.5-turbo",

    [Parameter(Mandatory=$false)]
    [string]$EmbeddingModel = "text-embedding-ada-002",

    [Parameter(Mandatory=$false)]
    [string]$PlannerModel = "gpt-3.5-turbo",

    [Parameter(Mandatory = $true)]
    [string] $ClientId,

    [Parameter(Mandatory = $false)]
    [string] $Tenant = 'common'
)

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

if ($OpenAI) 
{
    $aiServiceType = "OpenAI"
    $Endpoint = ""
}
elseif ($AzureOpenAI) 
{
    $aiServiceType = "AzureOpenAI"

    # Azure OpenAI has a different model name for gpt-3.5-turbo (no decimal).
    $CompletionModel = $CompletionModel.Replace("3.5", "35")
    $EmbeddingModel = $EmbeddingModel.Replace("3.5", "35")
    $PlannerModel = $PlannerModel.Replace("3.5", "35")
}
else {
    Write-Error "Please specify either -OpenAI or -AzureOpenAI"
    exit(1)
}

$appsettingsOverrides = @{ AIService = @{ Type = $aiServiceType; Endpoint = $Endpoint; Models = @{ Completion = $CompletionModel; Embedding = $EmbeddingModel; Planner = $PlannerModel } } }

$webapiProjectPath = Join-Path "$PSScriptRoot" '../webapi'
$appsettingsOverridesFilePath = Join-Path $webapiProjectPath 'appsettings.Development.json'

Write-Host "Setting 'AIService:Key' user secret for $aiServiceType..."
dotnet user-secrets set --project $webapiProjectPath  AIService:Key $ApiKey
if ($LASTEXITCODE -ne 0) { exit(1) }

Write-Host "Setting up 'appsettings.Development.json' for $aiServiceType..."
ConvertTo-Json $appsettingsOverrides | Out-File -Encoding utf8 $appsettingsOverridesFilePath

Write-Host "($appsettingsOverridesFilePath)"
Write-Host "========"
Get-Content $appsettingsOverridesFilePath | Write-Host
Write-Host "========"

Write-Host ""
Write-Host "##########################"
Write-Host "# Frontend configuration #"
Write-Host "##########################"

$envFilePath = Join-Path "$PSScriptRoot" '../webapp/.env'

Write-Host "Setting up '.env'..."
Set-Content -Path $envFilePath -Value "REACT_APP_BACKEND_URI=https://localhost:40443/"
Add-Content -Path $envFilePath -Value "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$Tenant"
Add-Content -Path $envFilePath -Value "REACT_APP_AAD_CLIENT_ID=$ClientId"
Add-Content -Path $envFilePath -Value ""
Add-Content -Path $envFilePath -Value "# Web Service API key (not required when running locally)"
Add-Content -Path $envFilePath -Value "REACT_APP_SK_API_KEY="

Write-Host "($envFilePath)"
Write-Host "========"
Get-Content $envFilePath | Write-Host
Write-Host "========"

Write-Host "Done!"
