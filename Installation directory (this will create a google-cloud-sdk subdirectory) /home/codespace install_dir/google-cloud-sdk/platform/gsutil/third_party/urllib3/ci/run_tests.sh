#!/bin/bash


if [[ "${NOX_SESSION}" == "app_engine" ]]; then
    export GAE_SDK_PATH=$HOME/.cache/google_appengine
    python2 -m pip install gcp-devrel-py-tools==0.0.16
    gcp-devrel-py-tools download-appengine-sdk "$(dirname ${GAE_SDK_PATH})"
fi

if [[ -z "$NOX_SESSION" ]]; then
    cat /etc/hosts
    NOX_SESSION=test-${PYTHON_VERSION%-dev}
fi
nox -s $NOX_SESSION --error-on-missing-interpreters
