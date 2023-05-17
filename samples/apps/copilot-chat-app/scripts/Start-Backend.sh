#!/bin/bash

# Builds and runs the Copilot Chat backend.

set -e

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir/../WebApi"

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

# Build and run the backend API server
dotnet build && dotnet run
