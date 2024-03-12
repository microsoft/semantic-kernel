# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Fingerprinting code for the Python runtime."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

DOCKERFILE_PREAMBLE = 'FROM gcr.io/google-appengine/python\n'
DOCKERFILE_VIRTUALENV_TEMPLATE = textwrap.dedent("""\
    LABEL python_version=python{python_version}
    RUN virtualenv --no-download /env -p python{python_version}

    # Set virtualenv environment variables. This is equivalent to running
    # source /env/bin/activate
    ENV VIRTUAL_ENV /env
    ENV PATH /env/bin:$PATH
    """)
DOCKERFILE_REQUIREMENTS_TXT = textwrap.dedent("""\
    ADD requirements.txt /app/
    RUN pip install -r requirements.txt
    """)
DOCKERFILE_INSTALL_APP = 'ADD . /app/\n'
