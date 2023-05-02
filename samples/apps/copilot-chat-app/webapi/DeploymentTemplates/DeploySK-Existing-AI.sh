#!/bin/bash

# Creates a Semantic Kernel service deployment using an existing OpenAI or Azure OpenAI instance.

set -e

# Parameters
DeploymentName="$1"
Subscription="$2"
ApiKey="$3"
Endpoint="${4:-}"
AIService="${5:-AzureOpenAI}"
CompletionModel="${6:-gpt-35-turbo}"
EmbeddingModel="${7:-text-embedding-ada-002}"
ResourceGroup="${8:-}"
Region="${9:-South Central US}"
PackageUri="${10:-https://skaasdeploy.blob.core.windows.net/api/skaas.zip}"
AppServiceSku="${11:-B1}"
DebugDeployment="${12:-false}"

if [ -z "$ResourceGroup" ]; then
    ResourceGroup="${DeploymentName}-rg"
fi

templateFile="$(dirname "$0")/sk-existing-ai.bicep"

az login --use-device-code

az account set -s "$Subscription"

echo "Creating resource group $ResourceGroup if it doesn't exist..."
az group create --location "$Region" --name "$ResourceGroup" --tags Creator="$USER"

echo "Validating template file..."
az deployment group validate --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" aiService="$AIService" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" endpoint="$Endpoint" apiKey="$ApiKey" appServiceSku="$AppServiceSku"

echo "Deploying..."
if [ "$DebugDeployment" = "true" ]; then
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --debug --parameters name="$DeploymentName" packageUri="$PackageUri" aiService="$AIService" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" endpoint="$Endpoint" apiKey="$ApiKey" appServiceSku="$AppServiceSku"
else
    az deployment group create --name "$DeploymentName" --resource-group "$ResourceGroup" --template-file "$templateFile" --parameters name="$DeploymentName" packageUri="$PackageUri" aiService="$AIService" completionModel="$CompletionModel" embeddingModel="$EmbeddingModel" endpoint="$Endpoint" apiKey="$ApiKey" appServiceSku="$AppServiceSku"
fi