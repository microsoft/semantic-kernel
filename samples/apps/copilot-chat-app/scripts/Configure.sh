#!/bin/bash
# Configure user secrets, appsettings.Development.json, and .env for Copilot Chat.

set -e

# Defaults
COMPLETION_MODEL="gpt-3.5-turbo"
EMBEDDING_MODEL="text-embedding-ada-002"
PLANNER_MODEL="gpt-3.5-turbo"
TENANT_ID="common"

# Argument parsing
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --openai)
      OPENAI=YES
      shift # past argument
      ;;
    --azureopenai)
      AZURE_OPENAI=YES
      shift
      ;;
    -e|--endpoint)
      ENDPOINT="$2"
      shift # past argument
      shift # past value
      ;;
    -a|--apikey)
      API_KEY="$2"
      shift
      shift
      ;;
    --completion)
      COMPLETION_MODEL="$2"
      shift
      shift
      ;;
    --embedding)
      EMBEDDING_MODEL="$2"
      shift
      shift
      ;;
    --planner)
      PLANNER_MODEL="$2"
      shift
      shift
      ;;
    -c|--clientid)
      CLIENT_ID="$2"
      shift
      shift
      ;;
    -t|--tenantid)
      TENANT_ID="$2"
      shift
      shift
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

SCRIPT_DIRECTORY="$(dirname $0)"

# Validate arguments
if [ -z "$API_KEY" ]; then
  echo "Please specify an API key with -a or --apikey."; exit 1;
fi
if [ -z "$CLIENT_ID" ]; then
  echo "Please specify a client (application) ID with -c or --clientid."; exit 1;
fi
if [ "$AZURE_OPENAI" = "YES" ] && [ -z "$ENDPOINT" ]; then
  echo "When using --azureopenti, please specify an endpoint with -e or --endpoint."; exit 1;
fi

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

if [ "$OPENAI" = "YES" ]; then
  AI_SERVICE_TYPE="OpenAI"
elif [ "$AZURE_OPENAI" = "YES" ]; then
  # Azure OpenAI has a different model name for gpt-3.5-turbo (no decimal).
  AI_SERVICE_TYPE="AzureOpenAI"
  COMPLETION_MODEL="${COMPLETION_MODEL/3.5/"35"}"
  EMBEDDING_MODEL="${EMBEDDING_MODEL/3.5/"35"}"
  PLANNER_MODEL="${PLANNER_MODEL/3.5/"35"}"
else 
    echo "Please specify either --openai or --azureopenai."
    exit 1
fi

APPSETTINGS_JSON="{ \"AIService\": { \"Type\": \"${AI_SERVICE_TYPE}\", \"Endpoint\": \"${ENDPOINT}\", \"Models\": { \"Completion\": \"${COMPLETION_MODEL}\", \"Embedding\": \"${EMBEDDING_MODEL}\", \"Planner\": \"${PLANNER_MODEL}\" } } }"
WEBAPI_PROJECT_PATH="${SCRIPT_DIRECTORY}/../webapi"
APPSETTINGS_OVERRIDES_FILEPATH="${WEBAPI_PROJECT_PATH}/appsettings.Development.json"

echo "Setting 'AIService:Key' user secret for $AI_SERVICE_TYPE..."
dotnet user-secrets set --project $WEBAPI_PROJECT_PATH  AIService:Key $API_KEY
if [ $? -ne 0 ]; then exit 1; fi

echo "Setting up 'appsettings.Development.json' for $AI_SERVICE_TYPE..."
echo $APPSETTINGS_JSON > $APPSETTINGS_OVERRIDES_FILEPATH

echo "($APPSETTINGS_OVERRIDES_FILEPATH)"
echo "========"
cat $APPSETTINGS_OVERRIDES_FILEPATH
echo "========"

echo ""
echo "##########################"
echo "# Frontend configuration #"
echo "##########################"

ENV_FILEPATH="${SCRIPT_DIRECTORY}/../webapp/.env"

echo "Setting up '.env'..."
echo "REACT_APP_BACKEND_URI=https://localhost:40443/" > $ENV_FILEPATH
echo "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$TENANT_ID" >> $ENV_FILEPATH
echo "REACT_APP_AAD_CLIENT_ID=$CLIENT_ID" >> $ENV_FILEPATH
echo "# Web Service API key (not required when running locally)" >> $ENV_FILEPATH
echo  "REACT_APP_SK_API_KEY=" >> $ENV_FILEPATH

echo "($ENV_FILEPATH)"
echo "========"
cat $ENV_FILEPATH
echo "========"

echo "Done!"