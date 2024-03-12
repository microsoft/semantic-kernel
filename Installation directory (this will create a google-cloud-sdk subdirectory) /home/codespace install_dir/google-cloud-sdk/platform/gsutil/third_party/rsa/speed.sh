#!/bin/bash -e
#
#  Copyright 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Checks if a command is available on the system.
check_command() {
    # Return with error, if not called with just one argument.
    if [ "$#" != 1 ]; then
        echo "ERROR: Incorrect usage of function 'check_program'." 1>&2
        echo "       Correct usage: check_command COMMAND" 1>&2
        return 1
    fi
    # Check command availability.
    command -v "$1" >/dev/null 2>&1
}

python_versions="
    pypy
    python2.7
    python3.4
    python3.5
"

echo "int2bytes speed test"
for version in $python_versions; do
    if check_command "$version"; then
        echo "$version"
        "$version" -mtimeit -s'from rsa.transform import int2bytes; n = 1<<4096' 'int2bytes(n)'
        "$version" -mtimeit -s'from rsa.transform import _int2bytes; n = 1<<4096' '_int2bytes(n)'
    fi
done
