<#
.SYNOPSIS
Initializes and runs the Copilot Chat backend.

.PARAMETER AzureOpenAIOrOpenAIKey
Your Azure OpenAI or OpenAI API key.
#>

#Requires -Version 6

param (
    [string] $AzureOpenAIOrOpenAIKey
)

Join-Path "$PSScriptRoot" '..' 'WebApi' | Set-Location

# Install dev certificate
if ($IsWindows -or $IsMacOS)
{
    dotnet dev-certs https --trust
}
elseif ($IsLinux)
{
    dotnet dev-certs https
}

# If key provided, store it in user secrets
if (-not $AzureOpenAIOrOpenAIKey -eq '') {
    dotnet user-secrets set "Completion:Key" "$AzureOpenAIOrOpenAIKey"
    dotnet user-secrets set "Embedding:Key" "$AzureOpenAIOrOpenAIKey"
    dotnet user-secrets set "Planner:AIService:Key" "$AzureOpenAIOrOpenAIKey"
}

# Build and run the backend API server
dotnet build
dotnet run
