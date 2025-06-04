#!/usr/bin/env bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$SCRIPT_DIR" > /dev/null

# Release config triggers also "dotnet format"
dotnet build --configuration Release --interactive
dotnet test --configuration Release --no-build --no-restore --interactive

popd > /dev/null