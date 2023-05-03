<#
.SYNOPSIS
Initialize and run the Copilot Chat backend.
#>

param (
    [SecureString] $Key
)

if ($IsWindows)
{
    dotnet dev-certs https --trust
}
else
{
    dotnet dev-certs https
}

cd $PSScriptRoot/../WebApi

# If key provided, store it in user secrets
If (-Not $Key -eq '') {
    dotnet user-secrets set "Completion:Key" "$Key"
    dotnet user-secrets set "Embedding:Key" "$Key"
}

# Build and run the backend API server
dotnet build
dotnet run
