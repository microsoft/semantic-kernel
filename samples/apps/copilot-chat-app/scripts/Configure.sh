#!/bin/bash
# Configure user secrets, appsettings.Development.json, and webapp/.env for Chat Copilot.

set -e

echo "#########################"
echo "# Backend configuration #"
echo "#########################"

# Install dev certificate
case "$OSTYPE" in
  darwin*)
    dotnet dev-certs https --trust
    if [ $? -ne 0 ]; then `exit` 1; fi ;;
  msys*)
    dotnet dev-certs https --trust
    if [ $? -ne 0 ]; then exit 1; fi ;;
  cygwin*)
    dotnet dev-certs https --trust
    if [ $? -ne 0 ]; then exit 1; fi ;;
  linux*)
    dotnet dev-certs https
    if [ $? -ne 0 ]; then exit 1; fi ;;
esac

WEBAPI_PROJECT_PATH="${SCRIPT_DIRECTORY}/../webapi"

echo "Setting 'AIService:Key' user secret for $AI_SERVICE..."
dotnet user-secrets set --project $WEBAPI_PROJECT_PATH  AIService:Key $API_KEY
if [ $? -ne 0 ]; then exit 1; fi

APPSETTINGS_OVERRIDES="{ \"AIService\": { \"Type\": \"${AI_SERVICE}\", \"Endpoint\": \"${ENDPOINT}\", \"Models\": { \"Completion\": \"${COMPLETION_MODEL}\", \"Embedding\": \"${EMBEDDING_MODEL}\", \"Planner\": \"${PLANNER_MODEL}\" } } }"
APPSETTINGS_OVERRIDES_FILEPATH="${WEBAPI_PROJECT_PATH}/appsettings.${ENV_ASPNETCORE}.json"

echo "Setting up 'appsettings.${ENV_ASPNETCORE}.json' for $AI_SERVICE..."
echo $APPSETTINGS_OVERRIDES > $APPSETTINGS_OVERRIDES_FILEPATH

echo "($APPSETTINGS_OVERRIDES_FILEPATH)"
echo "========"
cat $APPSETTINGS_OVERRIDES_FILEPATH
echo "========"

echo ""
echo "##########################"
echo "# Frontend configuration #"
echo "##########################"

WEBAPP_PROJECT_PATH="${SCRIPT_DIRECTORY}/../webapp"
WEBAPP_ENV_FILEPATH="${WEBAPP_PROJECT_PATH}/.env"

echo "Setting up '.env' for webapp..."
echo "REACT_APP_BACKEND_URI=https://localhost:40443/" > $WEBAPP_ENV_FILEPATH
echo "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$ENV_TENANT_ID" >> $WEBAPP_ENV_FILEPATH
echo "REACT_APP_AAD_CLIENT_ID=$CLIENT_ID" >> $WEBAPP_ENV_FILEPATH

echo "($WEBAPP_ENV_FILEPATH)"
echo "========"
cat $WEBAPP_ENV_FILEPATH
echo "========"

echo "Done!"