#!/bin/bash

# Initializes and runs both the backend and frontend for Copilot Chat.

set -e

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir"

# Start backend (in background)
./Start-Backend.sh &

# Start frontend
./Start-Frontend.sh
