# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.appengine.ext import vendor

# Add any libraries installed in the "lib" folder.
vendor.add("lib")


# Patch os.path.expanduser. This should be fixed in GAE
# versions released after Nov 2016.
import os.path


def patched_expanduser(path):
    return path


os.path.expanduser = patched_expanduser