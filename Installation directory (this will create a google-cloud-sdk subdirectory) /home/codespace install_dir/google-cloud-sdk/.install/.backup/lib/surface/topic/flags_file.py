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

"""--flags-file=YAML_FILE supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


# NOTE: If the name of this topic is modified, please make sure to update all
# references to it in error messages and other help messages as there are no
# tests to catch such changes.
class CommandConventions(base.TopicCommand):
  r"""--flags-file=YAML_FILE supplementary help.

  The *--flags-file*=_YAML-FILE_ flag, available to all *gcloud* commands,
  supports complex flag values in any command interpreter.

  Complex flag values that contain command interpreter special characters may
  be difficult to specify on the command line. The combined list of _special_
  characters across commonly used command interpreters (shell, cmd.exe,
  PowerShell) is surprisingly large. Among them are ```", ', `, *, ?, [, ],
  (, ), $, %, #, ^, &, |, {, }, ;, \, <, >,``` _space_, _tab_, _newline_.
  Add to that the separator characters for *list* and *dict* valued flags,
  and it becomes all but impossible to construct portable command lines.

  The *--flags-file*=_YAML-FILE_ flag solves this problem by allowing
  command line flags to be specified in a YAML/JSON file. String, numeric, list
  and dict flag values are specified using YAML/JSON notation and quoting rules.

  Flag specification uses dictionary notation. Use a list of dictionaries for
  flags that must be specified multiple times.

  For example, this YAML file defines values for Boolean, integer, floating
  point, string, dictionary and list valued flags:

  ```
      --boolean:
      --integer: 123
      --float: 456.789
      --string: A string value.
      --dictionary:
        a=b: c,d
        e,f: g=h
        i: none
        j=k=l: m=$n,o=%p
        "y:": ":z"
        meta:
        - key: foo
          value: bar
        - key: abc
          value: xyz
      --list:
        - a,b,c
        - x,y,z
  ```

  If the file is named *my-flags.yaml* then the command line flag
  *--flags-file=my-flags.yaml* will set the specified flags on any system
  using any command interpreter. *--flags-file* may be specified in a YAML
  file, and its value can be a YAML list to reference multiple files.

  This example specifies the *--metadata* flag multiple times:

  ```
      - --metadata: abc
        --integer: 123
      - --metadata: xyz
  ```

  Each *--flags-file* arg is replaced by its contents, so normal flag
  precedence applies. For example, given *flags-1.yaml*:

  ```
      --zone: us-east2-a
  ```

  *flags-2.yaml*:

  ```
      --verbosity: info
      --zone: us-central1-a
  ```

  and command line:

  ```
      gcloud compute instances describe \
          --flags-file=flags-1.yaml my-instance --flags-file=flags-2.yaml
  ```

  the effective command line is:

  ```
      gcloud compute instances describe \
          --zone=us-east2-a my-instance --verbosity=info --zone=us-central1-a
  ```

  using zone *us-central1-a* (not *us-east2-a*, because `flags-2.yaml`, to the
  right of `flags-1.yaml`, has higher precedence).
  """
