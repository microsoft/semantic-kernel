#!/bin/bash

# Builds and runs the Copilot Chat backend.

set -e

ScriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ScriptDir/../WebApi"

# Build and run the backend API server
dotnet build && dotnet run
