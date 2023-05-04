<#
.SYNOPSIS
Initialize and run the Copilot Chat backend.
#>

param (
    [string] $Key
)

if ($IsWindows -or $IsMacOS)
{
    dotnet dev-certs https --trust
}
else
{
    dotnet dev-certs https
}

cd $PSScriptRoot/../WebApi

# If key provided, store it in user secrets
if (-not $Key -eq '') {
    dotnet user-secrets set "Completion:Key" "$Key"
    dotnet user-secrets set "Embedding:Key" "$Key"
    dotnet user-secrets set "Planner:AIService:Key" "$Key"
}

# Build and run the backend API server
dotnet build
dotnet run
