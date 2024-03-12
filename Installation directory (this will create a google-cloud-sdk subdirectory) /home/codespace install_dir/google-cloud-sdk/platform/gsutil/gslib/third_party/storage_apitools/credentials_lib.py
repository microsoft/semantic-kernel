# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Shim for backwards-compatibility for moving GCE credentials.

oauth2client loads credentials classes based on the module name where
they were created; this means that moving GceAssertionCredentials from
here to third_party requires a shim mapping the old name to the new
one. Once loaded, the credential will be re-serialized with the new
path, meaning that we can (at some point) consider removing this file.
"""

# TODO: Remove this module once this change has been around long
# enough that old credentials are likely to be rare.

from apitools.base.py import GceAssertionCredentials
