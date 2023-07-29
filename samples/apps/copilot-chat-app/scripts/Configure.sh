#!/bin/bash
# Configure user secrets, appsettings.Development.json, and webapp/.env for Chat Copilot.

set -e

# Get defaults and constants
SCRIPT_DIRECTORY="$(dirname $0)"
. $SCRIPT_DIRECTORY/.env

# Argument parsing
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do 
  case $1 in
    --aiservice) # Required argument
      AI_SERVICE="$2"
      shift
      shift
      ;;
    -a|--apikey) # Required argument
      API_KEY="$2"
      shift
      shift
      ;;
    -c|--clientid) # Required argument
      CLIENT_ID="$2"
      shift
      shift
      ;;
    -e|--endpoint) # Required argument for Azure OpenAI
      ENDPOINT="$2"
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

# Validate arguments
if [ -z "$AI_SERVICE" -o \( "$AI_SERVICE" != "$ENV_OPEN_AI" -a "$AI_SERVICE" != "$ENV_AZURE_OPEN_AI" \) ]; then
  echo "Please specify an AI service (AzureOpenAI or OpenAI) for --aiservice. "; exit 1;
fi
if [ -z "$API_KEY" ]; then
  echo "Please specify an API key with -a or --apikey."; exit 1;
fi
if [ -z "$CLIENT_ID" ]; then
  echo "Please specify a client (application) ID with -c or --clientid."; exit 1;
fi
if [ "$AI_SERVICE" = "$ENV_AZURE_OPEN_AI" ] && [ -z "$ENDPOINT" ]; then
  echo "When using `--aiservice AzureOpenAI`, please specify an endpoint with -e or --endpoint."; exit 1;
fi

# Set remaining values from .env if not passed as argument
if [ "$AI_SERVICE" = "$ENV_OPEN_AI" ]; then
  if [ -z "$COMPLETION_MODEL" ]; then
    COMPLETION_MODEL="$ENV_COMPLETION_MODEL_OPEN_AI"
  fi
  if [ -z "$PLANNER_MODEL" ]; then
    PLANNER_MODEL="$ENV_PLANNER_MODEL_OPEN_AI"
  fi
  # TO DO: Validate model values if set by command line.
else # elif [ "$AI_SERVICE" = "$ENV_AZURE_OPEN_AI" ]; then
    if [ -z "$COMPLETION_MODEL" ]; then
    COMPLETION_MODEL="$ENV_COMPLETION_MODEL_AZURE_OPEN_AI"
  fi
  if [ -z "$PLANNER_MODEL" ]; then
    PLANNER_MODEL="$ENV_PLANNER_MODEL_AZURE_OPEN_AI"
  fi
  # TO DO: Validate model values if set by command line.
fi

if [ -z "$EMBEDDING_MODEL" ]; then
  COMPLETION_MODEL="$ENV_EMBEDDING_MODEL"
  # TO DO: Validate model values if set by command line.
fi
if [ -z "$TENANT_ID" ]; then
  TENANT_ID="$ENV_TENANT_ID"
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