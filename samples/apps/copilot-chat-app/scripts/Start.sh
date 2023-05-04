#!/bin/bash

# Initialize and run both the backend and frontend for Copilot Chat.

set -e

# Parameters
ClientId="$1"
TenantId="${2:-common}"
Key="${3:-}"

ScriptDir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Start backend (in background)
$ScriptDir/Start-Backend.sh $Key &

# Start frontend
$ScriptDir/Start-Frontend.sh $ClientId $TenantId
