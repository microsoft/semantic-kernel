#!/bin/bash

# Deploy CopilotChat's WebApp to Azure

set -e

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "Usage: $0 -d DEPLOYMENT_NAME -s SUBSCRIPTION --ai AI_SERVICE_TYPE -aikey AI_SERVICE_KEY [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  -s, --subscription SUBSCRIPTION        Subscription to which to make the deployment (mandatory)"
    echo "  -rg, --resource-group RESOURCE_GROUP    Resource group name from a 'deploy-azure.sh' deployment (mandatory)"
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
eval WEB_APP_URL=$(echo $DEPLOYMENT_JSON | jq -r '.properties.outputs.webappUrl.value')
echo "WEB_APP_URL: $WEB_APP_URL"
eval WEB_APP_NAME=$(echo $DEPLOYMENT_JSON | jq -r '.properties.outputs.webappName.value')
echo "WEB_APP_NAME: $WEB_APP_NAME"
eval WEB_API_URL=$(echo $DEPLOYMENT_JSON | jq -r '.properties.outputs.webapiUrl.value')
echo "WEB_API_URL: $WEB_API_URL"
eval WEB_API_NAME=$(echo $DEPLOYMENT_JSON | jq -r '.properties.outputs.webapiName.value')
echo "WEB_API_NAME: $WEB_API_NAME"
echo "Getting webapi key..."
eval WEB_API_KEY=$(az webapp config appsettings list --name $WEB_API_NAME --resource-group $RESOURCE_GROUP | jq '.[] | select(.name=="Authorization:ApiKey").value')

ENV_FILE_PATH="$SCRIPT_ROOT/../webapp/.env"
echo "Writing environment variables to '$ENV_FILE_PATH'..."
echo "REACT_APP_BACKEND_URI=https://$WEB_API_URL/" > $ENV_FILE_PATH
echo "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/common" >> $ENV_FILE_PATH
echo "REACT_APP_AAD_CLIENT_ID=$APPLICATION_ID" >> $ENV_FILE_PATH
echo "REACT_APP_SK_API_KEY=$WEB_API_KEY" >> $ENV_FILE_PATH

echo "Writing swa-cli.config.json..."
SWA_CONFIG_FILE_PATH="$SCRIPT_ROOT/../webapp/swa-cli.config.json"
sed "s/{{appDevserverUrl}}/https:\/\/${WEB_APP_URL}/g" $SCRIPT_ROOT/../webapp/template.swa-cli.config.json > $SWA_CONFIG_FILE_PATH
cat $SWA_CONFIG_FILE_PATH

pushd "$SCRIPT_ROOT/../webapp"

echo "Installing yarn dependencies..."
yarn install
if [ $? -ne 0 ]; then
    echo "Failed to install yarn dependencies"
    exit 1
fi

echo "Building webapp..."
swa build
if [ $? -ne 0 ]; then
    echo "Failed to build webapp"
    exit 1
fi

echo "Deploying webapp..."
swa deploy --subscription-id $SUBSCRIPTION --app-name $WEB_APP_NAME --env production
if [ $? -ne 0 ]; then
    echo "Failed to deploy webapp"
    exit 1
fi

ORIGIN="https://$WEB_APP_URL"
echo "Ensuring CORS origin '$ORIGIN' to webapi '$WEB_API_NAME'..."
CORS_RESULT=$(az webapp cors show --name $WEB_API_NAME --resource-group $RESOURCE_GROUP --subscription $SUBSCRIPTION | jq '.allowedOrigins | index("$ORIGIN")')
if [[ "$CORS_RESULT" == "null" ]]; then 
    echo "Adding CORS origin '$ORIGIN' to webapi '$WEB_API_NAME'..."
    az webapp cors add --name $WEB_API_NAME --resource-group $RESOURCE_GROUP --subscription $SUBSCRIPTION --allowed-origins $ORIGIN
fi

echo "Ensuring '$ORIGIN' is included in AAD app registration's redirect URIs..."
eval OBJECT_ID=$(az ad app show --id $APPLICATION_ID | jq -r '.id')

REDIRECT_URIS=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" --headers 'Content-Type=application/json' | jq -r '.spa.redirectUris')
if [[ ! "$REDIRECT_URIS" =~ "$ORIGIN" ]]; then
    BODY="{spa:{redirectUris:['"
    eval BODY+=$(echo $REDIRECT_URIS | jq $'join("\',\'")')
    BODY+="','$ORIGIN']}}"

    az rest \
    --method PATCH \
    --uri "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" \
    --headers 'Content-Type=application/json' \
    --body $BODY
fi
if [ $? -ne 0 ]; then
    echo "Failed to update app registration"
    exit 1
fi

popd

echo "To verify your deployment, go to 'https://$WEB_APP_URL' in your browser."