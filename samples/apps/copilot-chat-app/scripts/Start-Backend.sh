#!/bin/bash

# Initializes and runs the Copilot Chat backend.

set -e

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir/../WebApi"

# Parameters
AzureOpenAIOrOpenAIKey="$1"

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
if [ "$AzureOpenAIOrOpenAIKey" != "" ]; then
    dotnet user-secrets set "Completion:Key" "$AzureOpenAIOrOpenAIKey"
    dotnet user-secrets set "Embedding:Key" "$AzureOpenAIOrOpenAIKey"
    dotnet user-secrets set "Planner:AIService:Key" "$AzureOpenAIOrOpenAIKey"
fi

# Build and run the backend API server
dotnet build && dotnet run
