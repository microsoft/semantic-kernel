#!/bin/bash

# Deploy CopilotChat's WebAPI to Azure.

set -e

usage() {
    echo "Usage: $0 -d DEPLOYMENT_NAME -s SUBSCRIPTION --ai AI_SERVICE_TYPE -aikey AI_SERVICE_KEY [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  -s, --subscription SUBSCRIPTION        Subscription to which to make the deployment (mandatory)"
    echo "  -rg, --resource-group RESOUCE_GROUP    Resource group name from a 'deploy-azure.sh' deployment (mandatory)"
    echo "  -d, --deployment-name DEPLOYMENT_NAME  Name of the deployment from a 'deploy-azure.sh' deployment (mandatory)"
    echo "  -p, --package PACKAGE_FILE_PATH        Path to the WebAPI package file from a 'package-webapi.sh' run (mandatory)"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -d|--deployment-name)
        DEPLOYMENT_NAME="$2"
        shift
        shift
        ;;
        -s|--subscription)
        SUBSCRIPTION="$2"
        shift
        shift
        ;;
        -rg|--resource-group)
        RESOURCE_GROUP="$2"
        shift
        shift
        ;;
        -p|--package)
        PACKAGE_FILE_PATH="$2"
        shift
        shift
        ;;
        *)
        echo "Unknown option $1"
        usage
        exit 1
        ;;
    esac
done

# Check mandatory arguments
if [[ -z "$DEPLOYMENT_NAME" ]] || [[ -z "$SUBSCRIPTION" ]] || [[ -z "$RESOURCE_GROUP" ]] || [[ -z "$PACKAGE_FILE_PATH" ]]; then
    usage
    exit 1
fi

# Ensure $PACKAGE_FILE_PATH exists
if [[ ! -f "$PACKAGE_FILE_PATH" ]]; then
    echo "Package file '$PACKAGE_FILE_PATH' does not exist. Have you run 'package-webapi.sh' yet?"
    exit 1
fi

az account show --output none
if [ $? -ne 0 ]; then
    echo "Log into your Azure account"
    az login --use-device-code
fi

az account set -s "$SUBSCRIPTION"

echo "Getting Azure WebApp resource name..."
WEB_APP_NAME=$(az deployment group show --name $DEPLOYMENT_NAME --resource-group $RESOURCE_GROUP --output json | jq '.properties.outputs.webapiName.value'
# Ensure $WEB_APP_NAME is set
if [[ -z "$WEB_APP_NAME" ]]; then
    echo "Could not get Azure WebApp resource name from deployment output."
    exit 1
fi

echo "Azure WebApp name: $webappName"

echo "Configuring Azure WebApp to run from package..."
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings WEBSITE_RUN_FROM_PACKAGE="1" | out-null
if [ $? -ne 0 ]; then
    echo "Could not configure Azure WebApp to run from package."
    exit 1
fi

echo "Deploying '$PackageFilePath' to Azure WebApp '$webappName'..."
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --src $PACKAGE_FILE_PATH
if [ $? -ne 0 ]; then
    echo "Could not deploy '$PackageFilePath' to Azure WebApp '$webappName'."
    exit 1
fi
