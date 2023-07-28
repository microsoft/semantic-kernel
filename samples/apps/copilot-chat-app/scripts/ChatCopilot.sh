#!/bin/bash

# Configures, initializes, and runs both the backend and frontend for Chat Copilot.

set -e

# Set defaults and constants
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

# Configure backend and frontend
./Configure.sh

# Start backend (in background)
./Start-Backend.sh &

# Start frontend
./Start-Frontend.sh