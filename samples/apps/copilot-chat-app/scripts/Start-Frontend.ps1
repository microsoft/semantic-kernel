<#
.SYNOPSIS
Initializes and runs the Copilot Chat frontend.

.PARAMETER ClientId
The client (application) ID for your AAD app registration.

.PARAMETER TenantId
The tenant (directory) ID for your AAD app registration.
If you are using a personal MSA account, enter 'msa' here.
Defaults to the 'common' endpoint.
#>

#Requires -Version 6

param (
    [Parameter(Mandatory)]
    [string] $ClientId,

    [string] $TenantId = 'common'
)

cd "$PSScriptRoot/../WebApp"
$EnvFilePath = "$PSScriptRoot/../WebApp/.env"

# Overwrite existing .env file
Set-Content -Path $EnvFilePath -Value "REACT_APP_BACKEND_URI=https://localhost:40443/"

if ($TenantId -eq 'msa') 
{
    $TenantId = '9188040d-6c67-4c5b-b112-36a304b66dad'
}

Add-Content -Path $EnvFilePath -Value "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$TenantId"
Add-Content -Path $EnvFilePath -Value "REACT_APP_AAD_CLIENT_ID=$ClientId"

# Build and run the frontend application
yarn install
yarn start
