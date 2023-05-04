#!/bin/bash

# Initialize and run the Copilot Chat frontend.

set -e

# Parameters
ClientId="$1"
TenantId="${2:-common}"

ScriptDir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
EnvFilePath="$ScriptDir/../WebApp/.env"

# Overwrite existing .env file
echo "REACT_APP_BACKEND_URI=https://localhost:40443/" > $EnvFilePath

if [ "$TenantId" == "msa" ]; then
    TenantId='9188040d-6c67-4c5b-b112-36a304b66dad'
fi

echo "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$TenantId" >> $EnvFilePath
echo "REACT_APP_AAD_CLIENT_ID=$ClientId" >> $EnvFilePath

# Build and run the frontend application
cd $ScriptDir/../WebApp
yarn install && yarn start
