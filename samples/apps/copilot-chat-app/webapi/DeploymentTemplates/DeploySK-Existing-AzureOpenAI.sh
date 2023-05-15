#!/bin/bash

# Creates a Semantic Kernel service deployment using an existing Azure OpenAI account.

set -e

if [ $# -lt 4 ]; then
    echo "Usage: $0 DeploymentName Endpoint ApiKey Subscription [ResourceGroup] [Region] [PackageUri] [AppServiceSku] [DebugDeployment]"
    exit 1
fi

DeploymentName="$1"
Endpoint="$2"
ApiKey="$3"
Subscription="$4"
ResourceGroup="${5:-rg-$DeploymentName}"
Region="${6:-South Central US}"
PackageUri="${7:-https://skaasdeploy.blob.core.windows.net/api/skaas.zip}"
AppServiceSku="${8:-B1}"
DebugDeployment="${9:-false}"

templateFile="$(dirname "$0")/sk-existing-azureopenai.bicep"

echo "Log into your Azure account"
az login --use-device-code

az account set -s "$Subscription"

echo "Creating resource group $ResourceGroup if it doesn't exist..."
az group create --location "$Region" --name "$ResourceGroup" --tags Creator="$USER"

echo "Validating template file..."
az deployment group validate --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" plannerModel="$PlannerModel" endpoint="$Endpoint" apiKey="$ApiKey" appServiceSku="$AppServiceSku"

echo "Deploying..."
if [ "$DebugDeployment" = "true" ]; then
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --debug --parameters name="$DeploymentName" packageUri="$PackageUri" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" plannerModel="$PlannerModel" endpoint="$Endpoint" apiKey="$ApiKey" appServiceSku="$AppServiceSku"
else
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" plannerModel="$PlannerModel" endpoint="$Endpoint" apiKey="$ApiKey" appServiceSku="$AppServiceSku"
fi