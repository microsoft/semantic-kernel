#!/usr/bin/env bash

# This script is an example showing how to upload a file to
# Semantic Memory web service from the command line, using curl

set -e

# Request parameters: User Id, Request Id, Memory Vaults
USER_ID="myusername"
REQUEST_ID="bash-test"
VAULTS="abc 200-1ff 9a"

# Web service endpoint
URL="http://127.0.0.1:9001/upload"

# Input validation
if [ -z "$1" ]; then
  echo "Please specify a file to upload"
  exit -1
fi
if [ -d "$1" ]; then
  echo "$1 is a directory."
  exit -1
fi
if [ ! -f "$1" ]; then
  echo "$1 does not exist."
  exit -1
fi

# Handle list of vault IDs
VAULTS_FIELD=""
for v in ${VAULTS[@]}; do
  VAULTS_FIELD="${VAULTS_FIELD} -F vaults=\"${v}\""
done

# Send HTTP request using curl
#set -x
curl -v \
       -F 'requestId="'"${REQUEST_ID}"'"' \
       -F 'user="'"${USER_ID}"'"' \
       -F 'file1=@"'"$1"'"' \
       $VAULTS_FIELD \
       $URL
