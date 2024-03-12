#!/bin/bash

set -e

pushd .
cd .pyenv
git fetch --tags
git checkout v1.2.7
popd

echo $PYTHON_VERSIONS | xargs -n1 pyenv install
