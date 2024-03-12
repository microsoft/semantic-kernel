# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Constants/functions related to operating system options supported by image and OVF imports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

OS_CHOICES_IMAGE_IMPORT_GA = [
    'debian-8',
    'debian-9',
    'debian-10',
    'debian-11',
    'centos-7',
    'centos-stream-8',
    'centos-stream-9',
    'opensuse-15',
    'rhel-6',
    'rhel-6-byol',
    'rhel-7',
    'rhel-7-byol',
    'rhel-8',
    'rhel-8-byol',
    'rhel-9',
    'rhel-9-byol',
    'rocky-8',
    'rocky-9',
    'sles-12',
    'sles-12-byol',
    'sles-sap-12',
    'sles-sap-12-byol',
    'sles-15',
    'sles-15-byol',
    'sles-sap-15',
    'sles-sap-15-byol',
    'ubuntu-1404',
    'ubuntu-1604',
    'ubuntu-1804',
    'ubuntu-2004',
    'ubuntu-2204',
    'windows-2008r2',
    'windows-2008r2-byol',
    'windows-2012',
    'windows-2012-byol',
    'windows-2012r2',
    'windows-2012r2-byol',
    'windows-2016',
    'windows-2016-byol',
    'windows-2019',
    'windows-2019-byol',
    'windows-2022',
    'windows-2022-byol',
    'windows-7-x64-byol',
    'windows-7-x86-byol',
    'windows-8-x64-byol',
    'windows-8-x86-byol',
    'windows-10-x64-byol',
    'windows-10-x86-byol',
    'windows-11-x64-byol',
]

OS_CHOICES_IMAGE_IMPORT_BETA = OS_CHOICES_IMAGE_IMPORT_GA
OS_CHOICES_IMAGE_IMPORT_ALPHA = OS_CHOICES_IMAGE_IMPORT_BETA

OS_CHOICES_INSTANCE_IMPORT_GA = OS_CHOICES_IMAGE_IMPORT_GA
OS_CHOICES_INSTANCE_IMPORT_BETA = OS_CHOICES_IMAGE_IMPORT_BETA
