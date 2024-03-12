# -*- coding: utf-8 -*- #
#
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Package marker file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import importlib.util
import sys

from googlecloudsdk.core.util import lazy_regex


# Lazy loader doesn't work in some environments, such as par files
try:
  module_name = 'googlecloudsdk.api_lib.app.yaml_parsing'
  try:
    sys.modules[module_name]
  except KeyError:
    spec = importlib.util.find_spec(module_name)
    module = importlib.util.module_from_spec(spec)
    loader = importlib.util.LazyLoader(spec.loader)
    loader.exec_module(module)
except ImportError:
  pass

lazy_regex.initialize_lazy_compile()
