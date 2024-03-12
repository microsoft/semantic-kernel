# Copyright 2018 Google Inc. All Rights Reserved.
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
import contextlib
import importlib
import sys


@contextlib.contextmanager
def no_third_party_dir_on_path():
  old_path = sys.path
  try:
    # This works because we insert the third_party dir on the front of
    # sys.path on start up.
    sys.path = sys.path[1:]
    yield
  finally:
    sys.path = old_path

if sys.version_info < (3,):
  from concurrent.python2.concurrent import *
  from concurrent import futures
else:
  # Delete cached concurrent module
  del sys.modules['concurrent']
  with no_third_party_dir_on_path():
    spec = importlib.util.find_spec('concurrent.futures')
    futures  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(futures)

