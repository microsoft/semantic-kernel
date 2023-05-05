#!/bin/bash

# Initializes and runs the Copilot Chat backend.

set -e

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir/../WebApi"

# Parameters
Key="$1"

case "$OSTYPE" in
  darwin*)
    dotnet dev-certs https --trust ;;
  msys*)
    dotnet dev-certs https --trust ;;
  cygwin*)
    dotnet dev-certs https --trust ;;
  linux*)
    dotnet dev-certs https ;;
esac

# If key provided, store it in user secrets
if [ "$Key" != "" ]; then
    dotnet user-secrets set "Completion:Key" "$Key"
    dotnet user-secrets set "Embedding:Key" "$Key"
    dotnet user-secrets set "Planner:AIService:Key" "$Key"
fi

# Build and run the backend API server
dotnet build && dotnet run
