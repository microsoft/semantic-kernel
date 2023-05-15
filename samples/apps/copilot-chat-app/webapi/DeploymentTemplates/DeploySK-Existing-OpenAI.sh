#!/bin/bash

# Creates a Semantic Kernel service deployment using an existing OpenAI account.

set -e

if [ $# -lt 3 ]; then
    echo "Usage: $0 DeploymentName ApiKey Subscription [CompletionModel] [EmbeddingModel] [PlannerModel] [ResourceGroup] [Region] [PackageUri] [AppServiceSku] [DebugDeployment]"
    exit 1
fi

DeploymentName="$1"
ApiKey="$2"
Subscription="$3"
CompletionModel="${4:-gpt-3.5-turbo}"
EmbeddingModel="${5:-text-embedding-ada-002}"
PlannerModel="${6:-gpt-3.5-turbo}"
ResourceGroup="${7:-}"
Region="${8:-South Central US}"
PackageUri="${9:-https://skaasdeploy.blob.core.windows.net/api/skaas.zip}"
AppServiceSku="${10:-B1}"
DebugDeployment="${11:-}"

if [ -z "$ResourceGroup" ]; then
    ResourceGroup="rg-$DeploymentName"
fi

templateFile="$(dirname "$0")/sk-existing-openai.bicep"

echo "Log into your Azure account"
az login --use-device-code

az account set -s "$Subscription"

echo "Creating resource group $ResourceGroup if it doesn't exist..."
az group create --location "$Region" --name "$ResourceGroup" --tags Creator="$USER"

echo "Validating template file..."
az deployment group validate --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" plannerModel="$PlannerModel" apiKey="$ApiKey" appServiceSku="$AppServiceSku"

echo "Deploying..."
if [ "$DebugDeployment" = "true" ]; then
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --debug --parameters name="$DeploymentName" packageUri="$PackageUri" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" plannerModel="$PlannerModel" apiKey="$ApiKey" appServiceSku="$AppServiceSku"
else
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" plannerModel="$PlannerModel" apiKey="$ApiKey" appServiceSku="$AppServiceSku"
fi