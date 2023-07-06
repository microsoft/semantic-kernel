#!/bin/bash

# Package CiopilotChat's WebAPI for deployment to Azure

set -e

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIRECTORY="$SCRIPT_ROOT"

usage() {
    echo "Usage: $0 -d DEPLOYMENT_NAME -s SUBSCRIPTION --ai AI_SERVICE_TYPE -aikey AI_SERVICE_KEY [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  -c, --configuration CONFIGURATION      Build configuration (default: Release)"
    echo "  -d, --dotnet DOTNET_FRAMEWORK_VERSION  Target dotnet framework (default: net6.0)"
    echo "  -r, --runtime TARGET_RUNTIME           Runtime identifier (default: linux-x64)"
    echo "  -p, --output OUTPUT_DIRECTORY          Output directory (default: $SCRIPT_ROOT)"
    echo "  -nz, --no-zip                          Do not zip package (default: false)"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--configuration)
        CONFIGURATION="$2"
        shift
        shift
        ;;
        -d|--dotnet)
        DOTNET="$2"
        shift
        shift
        ;;
        -r|--runtime)
        RUNTIME="$2"
        shift
        shift
        ;;
        -o|--output)
        OUTPUT_DIRECTORY="$2"
        shift
        shift
        ;;
        -nz|--no-zip)
        NO_ZIP=true
        shift
        ;;
        *)
        echo "Unknown option $1"
        usage
        exit 1
        ;;
    esac
done

# Set defaults
: "${CONFIGURATION:="Release"}"
: "${DOTNET:="net6.0"}"
: "${RUNTIME:="win-x64"}"
: "${OUTPUT_DIRECTORY:="$SCRIPT_ROOT"}"

PUBLISH_OUTPUT_DIRECTORY="$OUTPUT_DIRECTORY/publish"
PUBLISH_ZIP_DIRECTORY="$OUTPUT_DIRECTORY/out"
PACKAGE_FILE_PATH="$PUBLISH_ZIP_DIRECTORY/webapi.zip"

if [[ ! -d "$PUBLISH_OUTPUT_DIRECTORY" ]]; then
    mkdir -p "$PUBLISH_OUTPUT_DIRECTORY"
fi
if [[ ! -d "$PUBLISH_ZIP_DIRECTORY" ]]; then
    mkdir -p "$PUBLISH_ZIP_DIRECTORY"
fi

echo "Build configuration: $CONFIGURATION"
dotnet publish "$SCRIPT_ROOT/../webapi/CopilotChatWebApi.csproj" --configuration $CONFIGURATION --framework $DOTNET --runtime $RUNTIME --self-contained --output "$PUBLISH_OUTPUT_DIRECTORY"
if [ $? -ne 0 ]; then
    exit 1
fi

# if not NO_ZIP then zip the package
if [[ -z "$NO_ZIP" ]]; then
    pushd "$PUBLISH_OUTPUT_DIRECTORY"
    echo "Compressing to $PACKAGE_FILE_PATH"
    zip -r $PACKAGE_FILE_PATH .
    popd
fi


