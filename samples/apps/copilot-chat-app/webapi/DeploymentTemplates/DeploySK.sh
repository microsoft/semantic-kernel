#!/bin/bash

# Creates a Semantic Kernel service deployment.

set -e

# Parameters
DeploymentName="$1"
Subscription="$2"
ResourceGroup="${3:-}"
Region="${4:-South Central US}"
PackageUri="${5:-https://skaasdeploy.blob.core.windows.net/api/skaas.zip}"
AppServiceSku="${6:-B1}"
DebugDeployment="$7"

templateFile="$(dirname "$0")/sk.bicep"

if [ -z "$ResourceGroup" ]; then
    ResourceGroup="$rg-{DeploymentName}"
fi

az login --use-device-code

az account set -s "$Subscription"

echo "Creating resource group $ResourceGroup if it doesn't exist..."
az group create --location "$Region" --name "$ResourceGroup" --tags Creator="$USER"

echo "Validating template file..."
az deployment group validate --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" appServiceSku="$AppServiceSku"

echo "Deploying..."
if [ -n "$DebugDeployment" ]; then
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --debug --parameters name="$DeploymentName" packageUri="$PackageUri" appServiceSku="$AppServiceSku"
else
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" appServiceSku="$AppServiceSku"
fi