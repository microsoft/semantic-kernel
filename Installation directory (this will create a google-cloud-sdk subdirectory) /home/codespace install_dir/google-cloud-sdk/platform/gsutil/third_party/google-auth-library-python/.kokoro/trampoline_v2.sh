#!/usr/bin/env bash
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# trampoline_v2.sh
#
# This script does 3 things.
#
# 1. Prepare the Docker image for the test
# 2. Run the Docker with appropriate flags to run the test
# 3. Upload the newly built Docker image
#
# in a way that is somewhat compatible with trampoline_v1.
#
# To run this script, first download few files from gcs to /dev/shm.
# (/dev/shm is passed into the container as KOKORO_GFILE_DIR).
#
# gsutil cp gs://cloud-devrel-kokoro-resources/python-docs-samples/secrets_viewer_service_account.json /dev/shm
# gsutil cp gs://cloud-devrel-kokoro-resources/python-docs-samples/automl_secrets.txt /dev/shm
#
# Then run the script.
# .kokoro/trampoline_v2.sh
#
# These environment variables are required:
# TRAMPOLINE_IMAGE: The docker image to use.
# TRAMPOLINE_DOCKERFILE: The location of the Dockerfile.
#
# You can optionally change these environment variables:
# TRAMPOLINE_IMAGE_UPLOAD:
#     (true|false): Whether to upload the Docker image after the
#                   successful builds.
# TRAMPOLINE_BUILD_FILE: The script to run in the docker container.
# TRAMPOLINE_WORKSPACE: The workspace path in the docker container.
#                       Defaults to /workspace.
# Potentially there are some repo specific envvars in .trampolinerc in
# the project root.


set -euo pipefail

TRAMPOLINE_VERSION="2.0.5"

if command -v tput >/dev/null && [[ -n "${TERM:-}" ]]; then
  readonly IO_COLOR_RED="$(tput setaf 1)"
  readonly IO_COLOR_GREEN="$(tput setaf 2)"
  readonly IO_COLOR_YELLOW="$(tput setaf 3)"
  readonly IO_COLOR_RESET="$(tput sgr0)"
else
  readonly IO_COLOR_RED=""
  readonly IO_COLOR_GREEN=""
  readonly IO_COLOR_YELLOW=""
  readonly IO_COLOR_RESET=""
fi

function function_exists {
    [ $(LC_ALL=C type -t $1)"" == "function" ]
}

# Logs a message using the given color. The first argument must be one
# of the IO_COLOR_* variables defined above, such as
# "${IO_COLOR_YELLOW}". The remaining arguments will be logged in the
# given color. The log message will also have an RFC-3339 timestamp
# prepended (in UTC). You can disable the color output by setting
# TERM=vt100.
function log_impl() {
    local color="$1"
    shift
    local timestamp="$(date -u "+%Y-%m-%dT%H:%M:%SZ")"
    echo "================================================================"
    echo "${color}${timestamp}:" "$@" "${IO_COLOR_RESET}"
    echo "================================================================"
}

# Logs the given message with normal coloring and a timestamp.
function log() {
  log_impl "${IO_COLOR_RESET}" "$@"
}

# Logs the given message in green with a timestamp.
function log_green() {
  log_impl "${IO_COLOR_GREEN}" "$@"
}

# Logs the given message in yellow with a timestamp.
function log_yellow() {
  log_impl "${IO_COLOR_YELLOW}" "$@"
}

# Logs the given message in red with a timestamp.
function log_red() {
  log_impl "${IO_COLOR_RED}" "$@"
}

readonly tmpdir=$(mktemp -d -t ci-XXXXXXXX)
readonly tmphome="${tmpdir}/h"
mkdir -p "${tmphome}"

function cleanup() {
    rm -rf "${tmpdir}"
}
trap cleanup EXIT

RUNNING_IN_CI="${RUNNING_IN_CI:-false}"

# The workspace in the container, defaults to /workspace.
TRAMPOLINE_WORKSPACE="${TRAMPOLINE_WORKSPACE:-/workspace}"

pass_down_envvars=(
    # TRAMPOLINE_V2 variables.
    # Tells scripts whether they are running as part of CI or not.
    "RUNNING_IN_CI"
    # Indicates which CI system we're in.
    "TRAMPOLINE_CI"
    # Indicates the version of the script.
    "TRAMPOLINE_VERSION"
)

log_yellow "Building with Trampoline ${TRAMPOLINE_VERSION}"

# Detect which CI systems we're in. If we're in any of the CI systems
# we support, `RUNNING_IN_CI` will be true and `TRAMPOLINE_CI` will be
# the name of the CI system. Both envvars will be passing down to the
# container for telling which CI system we're in.
if [[ -n "${KOKORO_BUILD_ID:-}" ]]; then
    # descriptive env var for indicating it's on CI.
    RUNNING_IN_CI="true"
    TRAMPOLINE_CI="kokoro"
    if [[ "${TRAMPOLINE_USE_LEGACY_SERVICE_ACCOUNT:-}" == "true" ]]; then
	if [[ ! -f "${KOKORO_GFILE_DIR}/kokoro-trampoline.service-account.json" ]]; then
	    log_red "${KOKORO_GFILE_DIR}/kokoro-trampoline.service-account.json does not exist. Did you forget to mount cloud-devrel-kokoro-resources/trampoline? Aborting."
	    exit 1
	fi
	# This service account will be activated later.
	TRAMPOLINE_SERVICE_ACCOUNT="${KOKORO_GFILE_DIR}/kokoro-trampoline.service-account.json"
    else
	if [[ "${TRAMPOLINE_VERBOSE:-}" == "true" ]]; then
	    gcloud auth list
	fi
	log_yellow "Configuring Container Registry access"
	gcloud auth configure-docker --quiet
    fi
    pass_down_envvars+=(
	# KOKORO dynamic variables.
	"KOKORO_BUILD_NUMBER"
	"KOKORO_BUILD_ID"
	"KOKORO_JOB_NAME"
	"KOKORO_GIT_COMMIT"
	"KOKORO_GITHUB_COMMIT"
	"KOKORO_GITHUB_PULL_REQUEST_NUMBER"
	"KOKORO_GITHUB_PULL_REQUEST_COMMIT"
	# For FlakyBot
	"KOKORO_GITHUB_COMMIT_URL"
	"KOKORO_GITHUB_PULL_REQUEST_URL"
    )
elif [[ "${TRAVIS:-}" == "true" ]]; then
    RUNNING_IN_CI="true"
    TRAMPOLINE_CI="travis"
    pass_down_envvars+=(
	"TRAVIS_BRANCH"
	"TRAVIS_BUILD_ID"
	"TRAVIS_BUILD_NUMBER"
	"TRAVIS_BUILD_WEB_URL"
	"TRAVIS_COMMIT"
	"TRAVIS_COMMIT_MESSAGE"
	"TRAVIS_COMMIT_RANGE"
	"TRAVIS_JOB_NAME"
	"TRAVIS_JOB_NUMBER"
	"TRAVIS_JOB_WEB_URL"
	"TRAVIS_PULL_REQUEST"
	"TRAVIS_PULL_REQUEST_BRANCH"
	"TRAVIS_PULL_REQUEST_SHA"
	"TRAVIS_PULL_REQUEST_SLUG"
	"TRAVIS_REPO_SLUG"
	"TRAVIS_SECURE_ENV_VARS"
	"TRAVIS_TAG"
    )
elif [[ -n "${GITHUB_RUN_ID:-}" ]]; then
    RUNNING_IN_CI="true"
    TRAMPOLINE_CI="github-workflow"
    pass_down_envvars+=(
	"GITHUB_WORKFLOW"
	"GITHUB_RUN_ID"
	"GITHUB_RUN_NUMBER"
	"GITHUB_ACTION"
	"GITHUB_ACTIONS"
	"GITHUB_ACTOR"
	"GITHUB_REPOSITORY"
	"GITHUB_EVENT_NAME"
	"GITHUB_EVENT_PATH"
	"GITHUB_SHA"
	"GITHUB_REF"
	"GITHUB_HEAD_REF"
	"GITHUB_BASE_REF"
    )
elif [[ "${CIRCLECI:-}" == "true" ]]; then
    RUNNING_IN_CI="true"
    TRAMPOLINE_CI="circleci"
    pass_down_envvars+=(
	"CIRCLE_BRANCH"
	"CIRCLE_BUILD_NUM"
	"CIRCLE_BUILD_URL"
	"CIRCLE_COMPARE_URL"
	"CIRCLE_JOB"
	"CIRCLE_NODE_INDEX"
	"CIRCLE_NODE_TOTAL"
	"CIRCLE_PREVIOUS_BUILD_NUM"
	"CIRCLE_PROJECT_REPONAME"
	"CIRCLE_PROJECT_USERNAME"
	"CIRCLE_REPOSITORY_URL"
	"CIRCLE_SHA1"
	"CIRCLE_STAGE"
	"CIRCLE_USERNAME"
	"CIRCLE_WORKFLOW_ID"
	"CIRCLE_WORKFLOW_JOB_ID"
	"CIRCLE_WORKFLOW_UPSTREAM_JOB_IDS"
	"CIRCLE_WORKFLOW_WORKSPACE_ID"
    )
fi

# Configure the service account for pulling the docker image.
function repo_root() {
    local dir="$1"
    while [[ ! -d "${dir}/.git" ]]; do
	dir="$(dirname "$dir")"
    done
    echo "${dir}"
}

# Detect the project root. In CI builds, we assume the script is in
# the git tree and traverse from there, otherwise, traverse from `pwd`
# to find `.git` directory.
if [[ "${RUNNING_IN_CI:-}" == "true" ]]; then
    PROGRAM_PATH="$(realpath "$0")"
    PROGRAM_DIR="$(dirname "${PROGRAM_PATH}")"
    PROJECT_ROOT="$(repo_root "${PROGRAM_DIR}")"
else
    PROJECT_ROOT="$(repo_root $(pwd))"
fi

log_yellow "Changing to the project root: ${PROJECT_ROOT}."
cd "${PROJECT_ROOT}"

# To support relative path for `TRAMPOLINE_SERVICE_ACCOUNT`, we need
# to use this environment variable in `PROJECT_ROOT`.
if [[ -n "${TRAMPOLINE_SERVICE_ACCOUNT:-}" ]]; then

    mkdir -p "${tmpdir}/gcloud"
    gcloud_config_dir="${tmpdir}/gcloud"

    log_yellow "Using isolated gcloud config: ${gcloud_config_dir}."
    export CLOUDSDK_CONFIG="${gcloud_config_dir}"

    log_yellow "Using ${TRAMPOLINE_SERVICE_ACCOUNT} for authentication."
    gcloud auth activate-service-account \
	   --key-file "${TRAMPOLINE_SERVICE_ACCOUNT}"
    log_yellow "Configuring Container Registry access"
    gcloud auth configure-docker --quiet
fi

required_envvars=(
    # The basic trampoline configurations.
    "TRAMPOLINE_IMAGE"
    "TRAMPOLINE_BUILD_FILE"
)

if [[ -f "${PROJECT_ROOT}/.trampolinerc" ]]; then
    source "${PROJECT_ROOT}/.trampolinerc"
fi

log_yellow "Checking environment variables."
for e in "${required_envvars[@]}"
do
    if [[ -z "${!e:-}" ]]; then
	log "Missing ${e} env var. Aborting."
	exit 1
    fi
done

# We want to support legacy style TRAMPOLINE_BUILD_FILE used with V1
# script: e.g. "github/repo-name/.kokoro/run_tests.sh"
TRAMPOLINE_BUILD_FILE="${TRAMPOLINE_BUILD_FILE#github/*/}"
log_yellow "Using TRAMPOLINE_BUILD_FILE: ${TRAMPOLINE_BUILD_FILE}"

# ignore error on docker operations and test execution
set +e

log_yellow "Preparing Docker image."
# We only download the docker image in CI builds.
if [[ "${RUNNING_IN_CI:-}" == "true" ]]; then
    # Download the docker image specified by `TRAMPOLINE_IMAGE`

    # We may want to add --max-concurrent-downloads flag.

    log_yellow "Start pulling the Docker image: ${TRAMPOLINE_IMAGE}."
    if docker pull "${TRAMPOLINE_IMAGE}"; then
	log_green "Finished pulling the Docker image: ${TRAMPOLINE_IMAGE}."
	has_image="true"
    else
	log_red "Failed pulling the Docker image: ${TRAMPOLINE_IMAGE}."
	has_image="false"
    fi
else
    # For local run, check if we have the image.
    if docker images "${TRAMPOLINE_IMAGE}:latest" | grep "${TRAMPOLINE_IMAGE}"; then
	has_image="true"
    else
	has_image="false"
    fi
fi


# The default user for a Docker container has uid 0 (root). To avoid
# creating root-owned files in the build directory we tell docker to
# use the current user ID.
user_uid="$(id -u)"
user_gid="$(id -g)"
user_name="$(id -un)"

# To allow docker in docker, we add the user to the docker group in
# the host os.
docker_gid=$(cut -d: -f3 < <(getent group docker))

update_cache="false"
if [[ "${TRAMPOLINE_DOCKERFILE:-none}" != "none" ]]; then
    # Build the Docker image from the source.
    context_dir=$(dirname "${TRAMPOLINE_DOCKERFILE}")
    docker_build_flags=(
	"-f" "${TRAMPOLINE_DOCKERFILE}"
	"-t" "${TRAMPOLINE_IMAGE}"
	"--build-arg" "UID=${user_uid}"
	"--build-arg" "USERNAME=${user_name}"
    )
    if [[ "${has_image}" == "true" ]]; then
	docker_build_flags+=("--cache-from" "${TRAMPOLINE_IMAGE}")
    fi

    log_yellow "Start building the docker image."
    if [[ "${TRAMPOLINE_VERBOSE:-false}" == "true" ]]; then
	echo "docker build" "${docker_build_flags[@]}" "${context_dir}"
    fi

    # ON CI systems, we want to suppress docker build logs, only
    # output the logs when it fails.
    if [[ "${RUNNING_IN_CI:-}" == "true" ]]; then
	if docker build "${docker_build_flags[@]}" "${context_dir}" \
		  > "${tmpdir}/docker_build.log" 2>&1; then
	    if [[ "${TRAMPOLINE_VERBOSE:-}" == "true" ]]; then
		cat "${tmpdir}/docker_build.log"
	    fi

	    log_green "Finished building the docker image."
	    update_cache="true"
	else
	    log_red "Failed to build the Docker image, aborting."
	    log_yellow "Dumping the build logs:"
	    cat "${tmpdir}/docker_build.log"
	    exit 1
	fi
    else
	if docker build "${docker_build_flags[@]}" "${context_dir}"; then
	    log_green "Finished building the docker image."
	    update_cache="true"
	else
	    log_red "Failed to build the Docker image, aborting."
	    exit 1
	fi
    fi
else
    if [[ "${has_image}" != "true" ]]; then
	log_red "We do not have ${TRAMPOLINE_IMAGE} locally, aborting."
	exit 1
    fi
fi

# We use an array for the flags so they are easier to document.
docker_flags=(
    # Remove the container after it exists.
    "--rm"

    # Use the host network.
    "--network=host"

    # Run in priviledged mode. We are not using docker for sandboxing or
    # isolation, just for packaging our dev tools.
    "--privileged"

    # Run the docker script with the user id. Because the docker image gets to
    # write in ${PWD} you typically want this to be your user id.
    # To allow docker in docker, we need to use docker gid on the host.
    "--user" "${user_uid}:${docker_gid}"

    # Pass down the USER.
    "--env" "USER=${user_name}"

    # Mount the project directory inside the Docker container.
    "--volume" "${PROJECT_ROOT}:${TRAMPOLINE_WORKSPACE}"
    "--workdir" "${TRAMPOLINE_WORKSPACE}"
    "--env" "PROJECT_ROOT=${TRAMPOLINE_WORKSPACE}"

    # Mount the temporary home directory.
    "--volume" "${tmphome}:/h"
    "--env" "HOME=/h"

    # Allow docker in docker.
    "--volume" "/var/run/docker.sock:/var/run/docker.sock"

    # Mount the /tmp so that docker in docker can mount the files
    # there correctly.
    "--volume" "/tmp:/tmp"
    # Pass down the KOKORO_GFILE_DIR and KOKORO_KEYSTORE_DIR
    # TODO(tmatsuo): This part is not portable.
    "--env" "TRAMPOLINE_SECRET_DIR=/secrets"
    "--volume" "${KOKORO_GFILE_DIR:-/dev/shm}:/secrets/gfile"
    "--env" "KOKORO_GFILE_DIR=/secrets/gfile"
    "--volume" "${KOKORO_KEYSTORE_DIR:-/dev/shm}:/secrets/keystore"
    "--env" "KOKORO_KEYSTORE_DIR=/secrets/keystore"
)

# Add an option for nicer output if the build gets a tty.
if [[ -t 0 ]]; then
    docker_flags+=("-it")
fi

# Passing down env vars
for e in "${pass_down_envvars[@]}"
do
    if [[ -n "${!e:-}" ]]; then
	docker_flags+=("--env" "${e}=${!e}")
    fi
done

# If arguments are given, all arguments will become the commands run
# in the container, otherwise run TRAMPOLINE_BUILD_FILE.
if [[ $# -ge 1 ]]; then
    log_yellow "Running the given commands '" "${@:1}" "' in the container."
    readonly commands=("${@:1}")
    if [[ "${TRAMPOLINE_VERBOSE:-}" == "true" ]]; then
	echo docker run "${docker_flags[@]}" "${TRAMPOLINE_IMAGE}" "${commands[@]}"
    fi
    docker run "${docker_flags[@]}" "${TRAMPOLINE_IMAGE}" "${commands[@]}"
else
    log_yellow "Running the tests in a Docker container."
    docker_flags+=("--entrypoint=${TRAMPOLINE_BUILD_FILE}")
    if [[ "${TRAMPOLINE_VERBOSE:-}" == "true" ]]; then
	echo docker run "${docker_flags[@]}" "${TRAMPOLINE_IMAGE}"
    fi
    docker run "${docker_flags[@]}" "${TRAMPOLINE_IMAGE}"
fi


test_retval=$?

if [[ ${test_retval} -eq 0 ]]; then
    log_green "Build finished with ${test_retval}"
else
    log_red "Build finished with ${test_retval}"
fi

# Only upload it when the test passes.
if [[ "${update_cache}" == "true" ]] && \
       [[ $test_retval == 0 ]] && \
       [[ "${TRAMPOLINE_IMAGE_UPLOAD:-false}" == "true" ]]; then
    log_yellow "Uploading the Docker image."
    if docker push "${TRAMPOLINE_IMAGE}"; then
	log_green "Finished uploading the Docker image."
    else
	log_red "Failed uploading the Docker image."
    fi
    # Call trampoline_after_upload_hook if it's defined.
    if function_exists trampoline_after_upload_hook; then
	trampoline_after_upload_hook
    fi

fi

exit "${test_retval}"
