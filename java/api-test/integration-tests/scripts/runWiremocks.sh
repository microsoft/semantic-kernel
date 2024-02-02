#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR="$SCRIPT_DIR/.."

cd $SCRIPT_DIR

if [ ! -f client.truststore ]; then
   ./generateCert.sh
fi


cd $ROOT_DIR

../../mvnw clean test -Dtest=WiremockExamplesIT -Prun-wiremocks