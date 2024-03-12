#!/usr/bin/env python
#
# Copyright 2018 Google Inc.
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

"""This file replaces the version that imports everything to the top level.

Different from the normal dependency generation process, this file just replaces
a single file (apitools/base/py/__init__.py) from Google internal apitools
during the depenency generation process. This allows us to make a breaking
change to apitools without complicating the process of updating apitools, as
changes are frequently pulled in from upstream.
"""
