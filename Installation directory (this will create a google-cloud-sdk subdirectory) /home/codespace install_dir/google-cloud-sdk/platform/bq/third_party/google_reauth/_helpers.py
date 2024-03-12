#!/usr/bin/env python
# Copyright 2017 Google Inc. All rights reserved.
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

import getpass
import sys


def get_user_password(text):
    """Get password from user.

    Override this function with a different logic if you are using this library
    outside a CLI.

    Args:
        text: message for the password prompt.

    Returns: password string.
    """
    return getpass.getpass(text)


def is_interactive():
    """Check if we are in an interractive environment.

    If the rapt token needs refreshing, the user needs to answer the
    challenges.
    If the user is not in an interractive environment, the challenges can not
    be answered and we just wait for timeout for no reason.

    Returns: True if is interactive environment, False otherwise.
    """

    return sys.stdin.isatty()
