# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Resource keys supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base


class Keys(base.TopicCommand):
  """Resource keys supplementary help."""

  detailed_help = {

      'DESCRIPTION': textwrap.dedent("""\
          A *resource* is a JSON-serializable object organized as a tree.
          Each node is a scalar, indexed array, or dictionary. Structs and
          classes are represented by dictionaries indexed by member name.

          Each node is reachable by a unique path of names from the root. A
          node *key* is the path names separated by '.'. [_number_] represents
          an array index. For example:

            foo
            foo.bar
            abc.def[3].ghi

          The resource keys and data values for any _gcloud_ _list_
          command can be printed by running _gcloud_ ... _list_
          *--format=flattened*. See the command specific documentation for
          details on specific resource keys.
          """),

      'EXAMPLES': textwrap.dedent("""\
          This command lists the keys and values for the *regions* resource:

            $ gcloud compute regions list --format=flattened

          and here is sample output for the command:

            ---
            creationTimestamp: 2013-05-23T07:02:09.522-07:00
            description:       us-central1
            id:                22115839677829654
            kind:              compute#region
            name:              us-central1
            quotas[0].limit:   24.0
            quotas[0].metric:  CPUS
            quotas[0].usage:   15.0
            quotas[1].limit:   5120.0
            quotas[1].metric:  DISKS_TOTAL_GB
            quotas[1].usage:   1416.0
            quotas[2].limit:   7.0
            quotas[2].metric:  STATIC_ADDRESSES
            quotas[2].usage:   1.0
            quotas[3].limit:   23.0
            quotas[3].metric:  IN_USE_ADDRESSES
            quotas[3].usage:   16.0
            quotas[4].limit:   1024.0
            quotas[4].metric:  SSD_TOTAL_GB
            quotas[4].usage:   0.0
            quotas[5].limit:   1500.0
            quotas[5].metric:  LOCAL_SSD_TOTAL_GB
            quotas[5].usage:   750.0
            selfLink:          https://www.googleapis.com/.../us-central1
            status:            UP
            zones[0]:          us-central1-a
            zones[1]:          us-central1-b
            zones[2]:          us-central1-f

          The *list* command produces a resource list. The keys are to the
          left of ':' and the values are to the right.
          """),
      }
