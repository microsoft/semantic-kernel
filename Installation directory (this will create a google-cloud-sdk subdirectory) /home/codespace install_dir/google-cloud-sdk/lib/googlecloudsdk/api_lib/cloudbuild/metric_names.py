# -*- coding: utf-8 -*- #
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
"""Cloud Build CSI metric names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# Reserved CSI metric prefix for cloudbuild
_CLOUDBUILD_PREFIX = 'cloudbuild_'

# Time to create a configuration
UPLOAD_SOURCE = _CLOUDBUILD_PREFIX + 'upload_source'
