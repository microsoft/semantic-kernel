<#
.SYNOPSIS
Initializes and runs the Copilot Chat frontend.

.PARAMETER ClientId
The client (application) ID associated with your AAD app registration.

.PARAMETER Tenant
The tenant associated with your AAD app registration.
Defaults to 'common'.
#>

#Requires -Version 6

param (
    [Parameter(Mandatory)]
    [string] $ClientId,

    [string] $Tenant = 'common'
)

Join-Path "$PSScriptRoot" '..' 'WebApp' | Set-Location
$EnvFilePath = '.env'

# Overwrite existing .env file
Set-Content -Path $EnvFilePath -Value "REACT_APP_BACKEND_URI=https://localhost:40443/"

Add-Content -Path $EnvFilePath -Value "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$Tenant"
Add-Content -Path $EnvFilePath -Value "REACT_APP_AAD_CLIENT_ID=$ClientId"

# Build and run the frontend application
yarn install
yarn start
