#!/bin/bash

# Initializes and runs both the backend and frontend for Copilot Chat.

set -e

# Parameters
ClientId="$1"
Tenant="${2:-common}"
AzureOpenAIOrOpenAIKey="${3:-}"

ScriptDir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Start backend (in background)
$ScriptDir/Start-Backend.sh $AzureOpenAIOrOpenAIKey &

# Start frontend
$ScriptDir/Start-Frontend.sh $ClientId $Tenant
