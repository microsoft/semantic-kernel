#!/bin/bash

# Initializes and runs both the backend and frontend for Copilot Chat.

set -e

# Start backend (in background)
./Start-Backend.sh &

# Start frontend
./Start-Frontend.sh
