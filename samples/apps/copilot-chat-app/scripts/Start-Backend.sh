#!/bin/bash

# Builds and runs the Chat Copilot backend.

set -e

# Set defaults and constants
SCRIPT_DIRECTORY="$(dirname $0)"
. $SCRIPT_DIRECTORY/.env

# Environment variable `ASPNETCORE_ENVIRONMENT` required to override 
# appsettings.json with appsettings.$ENV_ASPNETCORE.json 
# See `webapi/ConfigurationExtensions.cs`
export ASPNETCORE_ENVIRONMENT=$ENV_ASPNETCORE

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir/../webapi"

# Build and run the backend API server
dotnet build && dotnet run
