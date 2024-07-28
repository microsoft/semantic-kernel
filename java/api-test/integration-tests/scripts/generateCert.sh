#!/bin/bash

KEYTOOL_ARGS="-noprompt -srcstorepass password -deststorepass password -srckeypass password"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

if [ -f client.keystore ]; then
  exit
fi

rm client.keystore client.truststore server.keystore server.truststore || true

openssl genrsa -out diagserverCA.key 2048
openssl req -x509 -new -nodes -key diagserverCA.key -sha256 -days 1024 -out diagserverCA.pem -subj "/C=US/ST=NA/L=NA/O=NA/OU=NA/CN=localhost"
openssl pkcs12 -export -name server-cert -password pass:password -in diagserverCA.pem -inkey diagserverCA.key -out serverkeystore.p12

openssl genrsa -out diagclientCA.key 2048
openssl req -x509 -new -nodes -key diagclientCA.key -sha256 -days 1024 -out diagclientCA.pem -subj "/C=US/ST=NA/L=NA/O=NA/OU=NA/CN=localhost"
openssl pkcs12 -export -name client-cert -password pass:password -in diagclientCA.pem -inkey diagclientCA.key -out clientkeystore.p12


keytool -importkeystore $KEYTOOL_ARGS -destkeystore server.keystore -srckeystore serverkeystore.p12 -srcstoretype pkcs12 -alias server-cert
keytool -import $KEYTOOL_ARGS -alias client-cert -file diagclientCA.pem -keystore server.truststore
keytool -import $KEYTOOL_ARGS -alias server-cert -file diagserverCA.pem -keystore server.truststore


keytool -importkeystore $KEYTOOL_ARGS -destkeystore client.keystore -srckeystore clientkeystore.p12 -srcstoretype pkcs12 -alias client-cert
keytool -import $KEYTOOL_ARGS -alias server-cert -file diagserverCA.pem -keystore client.truststore
keytool -import $KEYTOOL_ARGS -alias client-cert -file diagclientCA.pem -keystore client.truststore

keytool -importkeystore -srckeystore /usr/lib/jvm/default-java/lib/security/cacerts -destkeystore client.truststore -srcstorepass changeit -deststorepass password
keytool -importkeystore -srckeystore /usr/lib/jvm/default-java/lib/security/cacerts -destkeystore server.truststore -srcstorepass changeit -deststorepass password

rm diagclientCA.key  diagserverCA.pem clientkeystore.p12  diagclientCA.pem serverkeystore.p12 diagserverCA.key || true
