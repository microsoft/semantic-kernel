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
    echo "  -a, --application-id                   Client application ID (mandatory)"
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
        -a|--application-id)
        APPLICATION_ID="$2"
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
if [[ -z "$DEPLOYMENT_NAME" ]] || [[ -z "$SUBSCRIPTION" ]] || [[ -z "$RESOURCE_GROUP" ]] || [[ -z "$APPLICATION_ID" ]]; then
    usage
    exit 1
fi

az account show --output none
if [ $? -ne 0 ]; then
    echo "Log into your Azure account"
    az login --use-device-code
fi

az account set -s "$SUBSCRIPTION"


echo "Getting deployment outputs..."
DEPLOYMENT_JSON=$(az deployment group show --name $DEPLOYMENT_NAME --resource-group $RESOURCE_GROUP --output json)
# get the webapiUrl from the deployment outputs
WEB_APP_URL=$(echo $DEPLOYMENT_JSON | jq -r '.properties.outputs.webappUrl.value')
WEB_API_URL=$(echo $DEPLOYMENT_JSON | jq -r '.properties.outputs.webapiUrl.value')
WEB_API_NAME=$(echo $DEPLOYMENT_JSON | jq -r '.properties.outputs.webapiName.value')
WEB_API_KEY=$(az webapp config appsettings list --name $WEB_API_NAME --resource-group $RESOURCE_GROUP)

WEB_APP_URL=$(.properties.outputs.webappUrl.value
# $webapiUrl=$deployment.properties.outputs.webapiUrl.value
# $webapiName=$deployment.properties.outputs.webapiName.value
# $webapiApiKey=($(az webapp config appsettings list --name $webapiName --resource-group $ResourceGroupName | ConvertFrom-JSON) | Where-Object -Property name -EQ -Value Authorization:ApiKey).value
# Write-Host "webappUrl: $webappUrl"
# Write-Host "webapiName: $webapiName"
# Write-Host "webapiUrl: $webapiUrl"

# # Set UTF8 as default encoding for Out-File
# $PSDefaultParameterValues['Out-File:Encoding'] = 'ascii'

# $envFilePath="$PSSCriptRoot/../webapp/.env"
# Write-Host "Writing environment variables to '$envFilePath'..."
# "REACT_APP_BACKEND_URI=https://$webapiUrl/" | Out-File -FilePath $envFilePath
# "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/common" | Out-File -FilePath $envFilePath -Append
# "REACT_APP_AAD_CLIENT_ID=$ApplicationClientId" | Out-File -FilePath $envFilePath -Append
# "REACT_APP_SK_API_KEY=$webapiApiKey" | Out-File -FilePath $envFilePath -Append

# $swaConfig = $(Get-Content "$PSSCriptRoot/../webapp/template.swa-cli.config.json" -Raw) 
# $swaConfig = $swaConfig.Replace("{{appDevserverUrl}}", "https://$webappUrl") 
# $swaConfig | Out-File -FilePath "$PSSCriptRoot/../webapp/swa-cli.config.json"
# Write-Host $(Get-Content "$PSSCriptRoot/../webapp/swa-cli.config.json" -Raw)

# Push-Location -Path "$PSSCriptRoot/../webapp"
# Write-Host "Installing yarn dependencies..."
# yarn install
# if ($LASTEXITCODE -ne 0) {
#   exit $LASTEXITCODE
# }

# Write-Host "Building webapp..."
# swa build
# if ($LASTEXITCODE -ne 0) {
#     exit $LASTEXITCODE
# }

# Write-Host "Deploying webapp..."
# swa deploy --subscription-id 5b742c40-bc2b-4a4f-902f-ee9f644d8844 --app-name swa-cc-int-cus-001-iudsttm4r2eg4 --env production
# if ($LASTEXITCODE -ne 0) {
#     exit $LASTEXITCODE
# }

# Pop-Location
