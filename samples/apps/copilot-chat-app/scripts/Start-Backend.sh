#!/bin/bash

# Builds and runs the Chat Copilot backend.

set -e

# Get defaults and constants
SCRIPT_DIRECTORY="$(dirname $0)"
. $SCRIPT_DIRECTORY/.env

# Environment variable `ASPNETCORE_ENVIRONMENT` required to override appsettings.json with 
# appsettings.$ENV_ASPNETCORE.json. See `webapi/ConfigurationExtensions.cs`
export ASPNETCORE_ENVIRONMENT=$ENV_ASPNETCORE

cd "$SCRIPT_DIRECTORY/../webapi"

# Build and run the backend API server
dotnet build && dotnet run
