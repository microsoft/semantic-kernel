# -*- coding: utf-8 -*- #
# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Resource definitions for Cloud Platform Apis generated from apitools."""

import enum

<%!
def SplitPath(path, max_length):
  """Splits path into chunks of max_length."""
  parts = []
  while path:
    if len(path) < max_length:
      index = max_length
    else:
      # Prefer to split on last '/'.
      index = path.rfind('/', 0, max_length - 1)
      if index < 0:
        index = min(max_length - 1, len(path) - 1)
    parts.append(path[:index+1])
    path = path[index+1:]
  return parts
%>
BASE_URL = '${base_url}'
DOCS_URL = '${docs_url}'


class Collections(enum.Enum):
  """Collections for all supported apis."""

% for collection_info in collections:
  ${collection_info.name.upper().replace('.', '_')} = (
      '${collection_info.name}',
% for i, part in enumerate(SplitPath(collection_info.path, 80 - 3 - 6)):
%   if i:

%   endif
      '${part}'\
%   endfor
,
%   if collection_info.flat_paths:
      {
%     for path_name, flat_path in collection_info.flat_paths.items():
          '${path_name}':
%       for i, part in enumerate(SplitPath(flat_path, 80 - 3 - 14)):
%         if i:

%         endif
              '${part}'\
%       endfor
,
%     endfor
      },
%   else:
      {},
%   endif
      ${collection_info.params},
      ${collection_info.enable_uri_parsing}
  )
% endfor

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
