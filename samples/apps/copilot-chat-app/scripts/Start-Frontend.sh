#!/bin/bash

# Initializes and runs the Chat Copilot frontend.

set -e

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir/../webapp"

# Build and run the frontend application
yarn install && yarn start
