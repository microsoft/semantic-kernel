# Copyright 2020 Google LLC
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

from typing import Mapping, Optional


def merge_metadata(
    a: Optional[Mapping[str, str]], b: Optional[Mapping[str, str]]
) -> Mapping[str, str]:
    """
    Merge the two sets of metadata if either exists. The second map overwrites the first.
    """
    result = {}
    if a:
        for k, v in a.items():
            result[k] = v
    if b:
        for k, v in b.items():
            result[k] = v
    return result
