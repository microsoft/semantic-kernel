#!/bin/bash

# Run this from the api-test/integration-tests directory

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR="$SCRIPT_DIR/.."

cd $SCRIPT_DIR

if [ ! -f client.truststore ]; then
   ./generateCert.sh
fi

rm -r "$ROOT_DIR/target/wiremock/mappings" || true
rm -r "$ROOT_DIR/src/test/resources/wiremock/mappings/" || true
mkdir -p "$ROOT_DIR/target/wiremock/mappings"
mkdir -p "$ROOT_DIR/src/test/resources/wiremock/mappings/"

cd $ROOT_DIR
source "$ROOT_DIR/../../.env.record"
export AZURE_CLIENT_KEY
export CLIENT_ENDPOINT
export PLUGIN_DIR="$ROOT_DIR/../../../"

../../mvnw clean package -DskipTests -Pcompile-jdk17

MAVEN_OPTS="-Djavax.net.ssl.trustStore=scripts/client.truststore -Djavax.net.ssl.trustStorePassword=password" \
../../mvnw exec:java@recordmappings -Pcompile-jdk17

for f in $ROOT_DIR/target/wiremock/mappings/*.json; do
  cat $f | jq 'del(.response.headers[])' > /tmp/mapping.json
  cat /tmp/mapping.json | json_pp > $f
  mv $f src/test/resources/wiremock/mappings/
done
