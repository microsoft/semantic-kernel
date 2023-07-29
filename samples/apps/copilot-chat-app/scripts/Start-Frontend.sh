#!/bin/bash

# Builds and runs the Chat Copilot frontend.

set -e

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIRECTORY/../webapp"

# Build and run the frontend application
yarn install && yarn start
