<#
.SYNOPSIS
Initialize and run the Copilot Chat frontend.
#>

param (
    [Parameter(Mandatory)]
    [string] $ClientId,

    [string] $TenantId = 'common'
)

$EnvFilePath = "$PSScriptRoot/../WebApp/.env"

# Overwrite existing .env file
Set-Content -Path $EnvFilePath -Value "REACT_APP_BACKEND_URI=https://localhost:40443/"

if ($TenantId -eq 'msa') 
{
    $TenantId = '9188040d-6c67-4c5b-b112-36a304b66dad'
} 
elseIf ($TenantId -eq 'msft') 
{
    $TenantId = '72f988bf-86f1-41af-91ab-2d7cd011db47'
}

Add-Content -Path $EnvFilePath -Value "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$TenantId"
Add-Content -Path $EnvFilePath -Value "REACT_APP_AAD_CLIENT_ID=$ClientId"

# Build and run the frontend application
cd $PSScriptRoot/../WebApp
yarn install
yarn start
