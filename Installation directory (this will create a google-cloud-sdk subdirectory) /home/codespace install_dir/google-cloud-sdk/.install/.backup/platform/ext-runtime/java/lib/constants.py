# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Constants shared by plugin and tests."""

# rutimes based on appengine-java-vm-runtime GitHub repo
DOCKERFILE_JAVA8_PREAMBLE = 'FROM gcr.io/google_appengine/openjdk8\n'
DOCKERFILE_JETTY9_PREAMBLE = 'FROM gcr.io/google_appengine/jetty9\n'

# runtimes based on openjdk-runtime and jetty-runtime GitHub repos
DOCKERFILE_JAVA_PREAMBLE = 'FROM gcr.io/google_appengine/openjdk\n'
DOCKERFILE_JETTY_PREAMBLE = 'FROM gcr.io/google_appengine/jetty\n'

DOCKERFILE_LEGACY_PREAMBLE = 'FROM gcr.io/google_appengine/java-compat\n'
DOCKERFILE_COMPAT_PREAMBLE = 'FROM gcr.io/google_appengine/jetty9-compat\n'
DOCKERFILE_CMD = 'CMD {0}\n'
DOCKERFILE_JAVA8_JAR_CMD = 'CMD ["java", "-jar", "/app/{0}"]\n'
DOCKERFILE_INSTALL_APP = 'ADD {0} /app/\n'
DOCKERFILE_INSTALL_WAR = 'ADD {0} $JETTY_BASE/webapps/root.war\n'

