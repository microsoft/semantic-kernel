#!/bin/bash

# Initializes and runs the Copilot Chat frontend.

set -e

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir/../WebApp"
EnvFilePath='.env'

# Parameters
ClientId="$1"
Tenant="${2:-common}"

# Overwrite existing .env file
echo "REACT_APP_BACKEND_URI=https://localhost:40443/" > $EnvFilePath

echo "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$Tenant" >> $EnvFilePath
echo "REACT_APP_AAD_CLIENT_ID=$ClientId" >> $EnvFilePath

# Build and run the frontend application
yarn install && yarn start
