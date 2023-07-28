#!/bin/bash

# Builds and runs the Chat Copilot frontend.

set -e

cd "$SCRIPT_DIRECTORY/../webapp"

# Build and run the frontend application
yarn install && yarn start
