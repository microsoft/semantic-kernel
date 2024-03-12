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
"""Old fingerprinting module for the Java runtime.

This file is almost dead.  It currently just contains constants that we use in
runtimes_test, which should also mostly go away.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

JAVA_APP_YAML = textwrap.dedent("""\
    env: flex
    runtime: {runtime}
    """)
DOCKERIGNORE = textwrap.dedent("""\
    .dockerignore
    Dockerfile
    .git
    .hg
    .svn
    app.yaml
    """)
DOCKERFILE_JAVA8_PREAMBLE = 'FROM gcr.io/google_appengine/openjdk8\n'
DOCKERFILE_JETTY9_PREAMBLE = 'FROM gcr.io/google_appengine/jetty9\n'
DOCKERFILE_JAVA_PREAMBLE = 'FROM gcr.io/google_appengine/openjdk\n'
DOCKERFILE_JETTY_PREAMBLE = 'FROM gcr.io/google_appengine/jetty\n'
DOCKERFILE_LEGACY_PREAMBLE = 'FROM gcr.io/google_appengine/java-compat\n'
DOCKERFILE_COMPAT_PREAMBLE = 'FROM gcr.io/google_appengine/jetty9-compat\n'
DOCKERFILE_JAVA8_JAR_CMD = 'CMD ["java", "-jar", "/app/{0}"]\n'
DOCKERFILE_INSTALL_APP = 'ADD {0} /app/\n'
DOCKERFILE_INSTALL_WAR = 'ADD {0} $JETTY_BASE/webapps/root.war\n'
