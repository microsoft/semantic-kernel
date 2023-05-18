#!/bin/bash

# Initializes and runs both the backend and frontend for Copilot Chat.

set -e

# Parameters
ClientId="$1"
Tenant="common"
AzureOpenAIOrOpenAIKey="${2:-}"

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir"

# Start backend (in background)
./Start-Backend.sh $AzureOpenAIOrOpenAIKey &

# Start frontend
./Start-Frontend.sh $ClientId $Tenant
