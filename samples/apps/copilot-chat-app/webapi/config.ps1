<#
.SYNOPSIS
Configure user secrets and appsettings.Development.json for the Copilot Chat AI service.

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
    [string]$PlannerModel = "gpt-3.5-turbo"

)

if ($OpenAI) 
{
    $appsettingsOverrides = @{ AIService = @{ Type = "OpenAI"; Models = @{ Completion = $CompletionModel; Embedding = $EmbeddingModel; Planner = $PlannerModel } } }
}
elseif ($AzureOpenAI) 
{
    # Azure OpenAI has a different model name for gpt-3.5-turbo (no decimal).
    $CompletionModel = $CompletionModel.Replace("gpt-3.5-turbo", "gpt-35-turbo")
    $PlannerModel = $PlannerModel.Replace("gpt-3.5-turbo", "gpt-35-turbo")
    $appsettingsOverrides = @{ AIService = @{ Type = "AzureOpenAI"; Endpoint = $Endpoint; Models = @{ Completion = $CompletionModel; Embedding = $EmbeddingModel; Planner = $PlannerModel } } }
}
else {
    Write-Error "Please specify either -OpenAI or -AzureOpenAI"
    exit(1)
}

$appsettingsOverridesFilePath = Join-Path "$PSScriptRoot" 'appsettings.Development.json'

Write-Host "Setting 'AIService:Key' user secret for $($appsettingsOverrides.AIService.Type)..."
dotnet user-secrets set AIService:Key $ApiKey

Write-Host "Setting up appsettings.Development.json for $($appsettingsOverrides.AIService.Type)..."
Write-Host "($appsettingsOverridesFilePath)"
ConvertTo-Json $appsettingsOverrides  | Out-File -Encoding utf8 $appsettingsOverridesFilePath
Get-Content $appsettingsOverridesFilePath
Write-Host "Done! Please rebuild (i.e., dotnet build) and run (i.e., dotnet run) the application."
