<#
.SYNOPSIS
Deploy CopilotChat's WebAPI to Azure
#>

param(
    [Parameter(Mandatory)]
    [string]
    # Subscription to which to make the deployment
    $Subscription,

    [Parameter(Mandatory)]
    [string]
    # Resource group to which to make the deployment
    $ResourceGroupName,
    
    [Parameter(Mandatory)]
    [string]
    # Name of the previously deployed Azure deployment 
    $DeploymentName,

    [string]
    # CopilotChat WebApi package to deploy
    $PackageFilePath = "$PSScriptRoot/out/webapi.zip"
)

# Ensure $PackageFilePath exists
if (!(Test-Path $PackageFilePath)) {
    Write-Error "Package file '$PackageFilePath' does not exist. Have you run 'package-webapi.ps1' yet?"
    exit 1
}

az account show --output none
if ($LASTEXITCODE -ne 0) {
    Write-Host "Log into your Azure account"
    az login --output none
}

az account set -s $Subscription
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "Getting Azure WebApp resource name..."
$webappName=$(az deployment group show --name $DeploymentName --resource-group $ResourceGroupName --output json | ConvertFrom-Json).properties.outputs.webapiName.value
if ($null -eq $webAppName) {
    Write-Error "Could not get Azure WebApp resource name from deployment output."
    exit 1
}

Write-Host "Azure WebApp name: $webappName"

Write-Host "Configuring Azure WebApp to run from package..."
az webapp config appsettings set --resource-group $ResourceGroupName --name $webappName --settings WEBSITE_RUN_FROM_PACKAGE="1" | out-null
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Deploying '$PackageFilePath' to Azure WebApp '$webappName'..."
az webapp deployment source config-zip --resource-group $ResourceGroupName --name $webappName --src $PackageFilePath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}