<#
.SYNOPSIS
Initializes and runs the Copilot Chat backend.

.PARAMETER Key
Your OpenAI or Azure OpenAI API key.
#>

#Requires -Version 6

param (
    [string] $Key
)

cd "$PSScriptRoot/../WebApi"

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
if (-not $Key -eq '') {
    dotnet user-secrets set "Completion:Key" "$Key"
    dotnet user-secrets set "Embedding:Key" "$Key"
    dotnet user-secrets set "Planner:AIService:Key" "$Key"
}

# Build and run the backend API server
dotnet build
dotnet run
